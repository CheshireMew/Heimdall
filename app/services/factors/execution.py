from __future__ import annotations

from datetime import datetime
from typing import Any

from app.infra.db.database import session_scope
from app.infra.db.schema import BacktestEquityPoint, BacktestRun, BacktestSignal, BacktestTrade
from app.services.backtest.freqtrade_report_builder import FreqtradeReportBuilder
from app.services.backtest.models import (
    BacktestEquityPointRecord,
    BacktestSignalRecord,
    BacktestTradeRecord,
    PortfolioConfigRecord,
    ResearchConfigRecord,
    StrategyVersionRecord,
)
from app.services.backtest.run_contract import BACKTEST_EXECUTION_MODE, FACTOR_BLEND_ENGINE, build_backtest_metadata
from app.services.factors.service import FactorResearchService
from app.services.factors.signal_execution_core import FactorSignalContext, FactorSignalExecutionCore


class FactorExecutionService:
    def __init__(
        self,
        *,
        factor_service: FactorResearchService,
        report_builder: FreqtradeReportBuilder,
        execution_core: FactorSignalExecutionCore,
    ) -> None:
        self.factor_service = factor_service
        self.report_builder = report_builder
        self.execution_core = execution_core

    def run_backtest(
        self,
        *,
        research_run_id: int,
        initial_cash: float,
        fee_rate: float,
        position_size_pct: float,
        stake_mode: str = "fixed",
        entry_threshold: float | None = None,
        exit_threshold: float | None = None,
        stoploss_pct: float = -0.08,
        takeprofit_pct: float = 0.16,
        max_hold_bars: int = 20,
    ) -> int:
        research_run, frame = self.factor_service.build_stored_blend_frame(research_run_id)
        if frame.empty:
            raise ValueError("研究结果没有可回测的组合分数。")

        request_payload = dict(research_run.get("request") or {})
        blend = dict(research_run.get("blend") or {})
        symbol = request_payload["symbol"]
        timeframe = request_payload["timeframe"]
        entry_threshold = float(blend.get("entry_threshold", 0.0) if entry_threshold is None else entry_threshold)
        exit_threshold = float(blend.get("exit_threshold", 0.0) if exit_threshold is None else exit_threshold)

        label_column = f"label::{request_payload['horizon_bars']}".replace("::", "__")
        rows = [
            {
                "timestamp": row.timestamp,
                "close": float(row.close),
                "composite_score": float(row.composite_score or 0.0),
                "future_return": float(getattr(row, label_column, 0.0) or 0.0),
            }
            for row in frame.itertuples(index=False)
        ]
        context = FactorSignalContext(
            symbol=symbol,
            research_run_id=research_run_id,
            initial_cash=float(initial_cash),
            fee_rate=float(fee_rate),
            position_size_pct=float(position_size_pct),
            stake_mode=stake_mode,
            entry_threshold=entry_threshold,
            exit_threshold=exit_threshold,
            stoploss_pct=stoploss_pct,
            takeprofit_pct=takeprofit_pct,
            max_hold_bars=max_hold_bars,
        )
        batch = self.execution_core.run_batch(
            rows=rows,
            state=self.execution_core.create_state(initial_cash),
            context=context,
            force_close=True,
        )
        signals = batch.signals
        trades = batch.trades
        equity_curve = self._decorate_drawdowns(batch.equity_points)
        report = self.report_builder.build_report(
            trades=trades,
            equity_curve=equity_curve,
            initial_cash=initial_cash,
            start_date=frame["timestamp"].iloc[0],
            end_date=frame["timestamp"].iloc[-1],
        )

        strategy = StrategyVersionRecord(
            strategy_key="factor_blend",
            strategy_name="Factor Blend",
            version=research_run_id,
            template="factor_blend",
            config={"research_run_id": research_run_id},
            version_name=f"Research {research_run_id}",
        )
        portfolio = PortfolioConfigRecord(symbols=[symbol], max_open_trades=1, position_size_pct=position_size_pct, stake_mode=stake_mode)
        research = ResearchConfigRecord()
        metadata = build_backtest_metadata(
            strategy=strategy,
            symbols=[symbol],
            initial_cash=initial_cash,
            fee_rate=fee_rate,
            portfolio=portfolio,
            research=research,
        )
        metadata["factor_research"] = {
            "run_id": research_run_id,
            "dataset_id": research_run["dataset_id"],
            "entry_threshold": entry_threshold,
            "exit_threshold": exit_threshold,
            "stoploss_pct": stoploss_pct,
            "takeprofit_pct": takeprofit_pct,
            "max_hold_bars": max_hold_bars,
            "blend": blend,
        }
        metadata["report"] = report

        return self._persist_backtest_run(
            symbol=symbol,
            timeframe=timeframe,
            start_date=frame["timestamp"].iloc[0],
            end_date=frame["timestamp"].iloc[-1],
            total_candles=len(frame),
            signals=signals,
            trades=trades,
            equity_curve=equity_curve,
            metadata=metadata,
        )

    def _persist_backtest_run(
        self,
        *,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
        total_candles: int,
        signals: list[BacktestSignalRecord],
        trades: list[BacktestTradeRecord],
        equity_curve: list[BacktestEquityPointRecord],
        metadata: dict[str, Any],
    ) -> int:
        with session_scope() as session:
            run = BacktestRun(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date,
                status="completed",
                execution_mode=BACKTEST_EXECUTION_MODE,
                engine=FACTOR_BLEND_ENGINE,
                total_candles=total_candles,
                total_signals=len(signals),
                buy_signals=sum(1 for item in signals if item.signal == "BUY"),
                sell_signals=sum(1 for item in signals if item.signal == "SELL"),
                hold_signals=max(total_candles - len(signals), 0),
                metadata_info=metadata,
            )
            session.add(run)
            session.flush()
            if signals:
                session.bulk_save_objects(
                    [
                        BacktestSignal(
                            backtest_id=run.id,
                            timestamp=item.timestamp,
                            price=item.price,
                            signal=item.signal,
                            confidence=item.confidence,
                            indicators=item.indicators,
                            reasoning=item.reasoning,
                        )
                        for item in signals
                    ]
                )
            if trades:
                session.bulk_save_objects(
                    [
                        BacktestTrade(
                            backtest_id=run.id,
                            pair=item.pair or symbol,
                            opened_at=item.opened_at,
                            closed_at=item.closed_at,
                            entry_price=item.entry_price,
                            exit_price=item.exit_price,
                            stake_amount=item.stake_amount,
                            amount=item.amount,
                            profit_abs=item.profit_abs,
                            profit_pct=item.profit_pct,
                            max_drawdown_pct=item.max_drawdown_pct,
                            duration_minutes=item.duration_minutes,
                            entry_tag=item.entry_tag,
                            exit_reason=item.exit_reason,
                            leverage=item.leverage,
                        )
                        for item in trades
                    ]
                )
            if equity_curve:
                session.bulk_save_objects(
                    [
                        BacktestEquityPoint(
                            backtest_id=run.id,
                            timestamp=item.timestamp,
                            equity=item.equity,
                            pnl_abs=item.pnl_abs,
                            drawdown_pct=item.drawdown_pct,
                        )
                        for item in equity_curve
                    ]
                )
            session.flush()
            return run.id

    def _decorate_drawdowns(self, equity_curve: list[BacktestEquityPointRecord]) -> list[BacktestEquityPointRecord]:
        peak = 0.0
        result = []
        for point in equity_curve:
            peak = max(peak, point.equity)
            drawdown = ((peak - point.equity) / peak * 100.0) if peak else 0.0
            result.append(
                BacktestEquityPointRecord(
                    timestamp=point.timestamp,
                    equity=point.equity,
                    pnl_abs=point.pnl_abs,
                    drawdown_pct=drawdown,
                )
            )
        return result
