from __future__ import annotations

from datetime import datetime
from typing import Any

from app.infra.db.database import DatabaseRuntime
from app.infra.db.schema import BacktestRun
from app.services.backtest.freqtrade_report_builder import FreqtradeReportBuilder
from app.services.backtest.result_store import store_run_rows
from app.contracts.backtest import (
    BacktestPortfolioConfig,
    BacktestResearchConfig,
    BacktestEquityPointRecord,
    BacktestSignalRecord,
    BacktestTradeRecord,
    StrategyVersionRecord,
)
from app.services.backtest.run_contract import BACKTEST_EXECUTION_MODE, FACTOR_BLEND_ENGINE, build_backtest_metadata, parse_run_metadata
from app.services.backtest.run_lifecycle import RUN_STATUS_COMPLETED
from app.services.backtest.strategy_support import blank_strategy_version_config_model
from app.services.executor import run_sync
from app.services.factors.service import FactorResearchService
from app.services.factors.signal_execution_core import FactorSignalContext, FactorSignalExecutionCore


class FactorExecutionService:
    def __init__(
        self,
        *,
        factor_service: FactorResearchService,
        report_builder: FreqtradeReportBuilder,
        execution_core: FactorSignalExecutionCore,
        database_runtime: DatabaseRuntime,
    ) -> None:
        self.factor_service = factor_service
        self.report_builder = report_builder
        self.execution_core = execution_core
        self.database_runtime = database_runtime

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

        request_payload = research_run.request.model_dump()
        blend = research_run.blend.model_dump()
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
            config=blank_strategy_version_config_model().model_dump(),
            version_name=f"Research {research_run_id}",
        )
        portfolio = BacktestPortfolioConfig(symbols=[symbol], max_open_trades=1, position_size_pct=position_size_pct, stake_mode=stake_mode)
        research = BacktestResearchConfig()
        metadata = parse_run_metadata(
            build_backtest_metadata(
                strategy=strategy,
                symbols=[symbol],
                initial_cash=initial_cash,
                fee_rate=fee_rate,
                portfolio=portfolio,
                research=research,
            )
        ).model_copy(
            update={
                "factor_research": {
                    "run_id": research_run_id,
                    "dataset_id": research_run.dataset_id,
                    "entry_threshold": entry_threshold,
                    "exit_threshold": exit_threshold,
                    "stoploss_pct": stoploss_pct,
                    "takeprofit_pct": takeprofit_pct,
                    "max_hold_bars": max_hold_bars,
                    "blend": blend,
                },
                "report": report,
            }
        ).model_dump()

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

    async def run_backtest_async(
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
        return await run_sync(
            lambda: self.run_backtest(
                research_run_id=research_run_id,
                initial_cash=initial_cash,
                fee_rate=fee_rate,
                position_size_pct=position_size_pct,
                stake_mode=stake_mode,
                entry_threshold=entry_threshold,
                exit_threshold=exit_threshold,
                stoploss_pct=stoploss_pct,
                takeprofit_pct=takeprofit_pct,
                max_hold_bars=max_hold_bars,
            )
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
        with self.database_runtime.session_scope() as session:
            run = BacktestRun(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date,
                status=RUN_STATUS_COMPLETED,
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
            store_run_rows(
                session=session,
                run_id=run.id,
                signals=signals,
                trades=trades,
                equity_curve=equity_curve,
                default_pair=symbol,
            )
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
