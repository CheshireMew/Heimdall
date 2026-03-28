from __future__ import annotations

from dataclasses import dataclass
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


@dataclass(slots=True)
class FactorBacktestPosition:
    opened_at: datetime
    entry_price: float
    amount: float
    stake_amount: float
    entry_score: float


class FactorExecutionService:
    def __init__(
        self,
        *,
        factor_service: FactorResearchService,
        report_builder: FreqtradeReportBuilder | None = None,
    ) -> None:
        self.factor_service = factor_service
        self.report_builder = report_builder or FreqtradeReportBuilder()

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

        cash_balance = float(initial_cash)
        position: FactorBacktestPosition | None = None
        signals: list[BacktestSignalRecord] = []
        trades: list[BacktestTradeRecord] = []
        equity_curve: list[BacktestEquityPointRecord] = []
        fee_ratio = fee_rate / 100.0

        for bar_index, row in enumerate(frame.itertuples(index=False), start=1):
            price = float(row.close)
            score = float(row.composite_score or 0.0)
            label_column = f"label::{request_payload['horizon_bars']}"
            future_return = float(getattr(row, label_column.replace("::", "__"), 0.0) or 0.0)
            timestamp = row.timestamp

            if position:
                held_bars = max(bar_index - self._opened_bar_index(equity_curve, position.opened_at), 0)
                profit_ratio = self._profit_ratio(position, price, fee_ratio)
                should_exit = (
                    profit_ratio <= stoploss_pct
                    or profit_ratio >= takeprofit_pct
                    or score <= exit_threshold
                    or held_bars >= max_hold_bars
                )
                if should_exit:
                    trade = self._close_position(position, price, timestamp, fee_ratio, symbol)
                    cash_balance += trade.stake_amount + trade.profit_abs
                    trades.append(trade)
                    signals.append(
                        BacktestSignalRecord(
                            timestamp=timestamp,
                            price=price,
                            signal="SELL",
                            confidence=100.0,
                            indicators={
                                "composite_score": score,
                                "future_return": future_return,
                                "research_run_id": research_run_id,
                            },
                            reasoning="Factor blend exit",
                        )
                    )
                    position = None

            if position is None and score >= entry_threshold:
                stake_amount = min(
                    cash_balance,
                    initial_cash * (position_size_pct / 100.0) if stake_mode == "fixed" else cash_balance * (position_size_pct / 100.0),
                )
                if stake_amount > 0:
                    notional = stake_amount / (1.0 + fee_ratio) if fee_ratio < 1 else 0.0
                    amount = notional / price if price > 0 else 0.0
                    if amount > 0:
                        cash_balance -= stake_amount
                        position = FactorBacktestPosition(
                            opened_at=timestamp,
                            entry_price=price,
                            amount=amount,
                            stake_amount=stake_amount,
                            entry_score=score,
                        )
                        signals.append(
                            BacktestSignalRecord(
                                timestamp=timestamp,
                                price=price,
                                signal="BUY",
                                confidence=100.0,
                                indicators={
                                    "composite_score": score,
                                    "future_return": future_return,
                                    "research_run_id": research_run_id,
                                },
                                reasoning="Factor blend entry",
                            )
                        )

            equity = cash_balance
            if position:
                equity += position.amount * price * (1.0 - fee_ratio)
            equity_curve.append(
                BacktestEquityPointRecord(
                    timestamp=timestamp,
                    equity=equity,
                    pnl_abs=equity - initial_cash,
                    drawdown_pct=0.0,
                )
            )

        if position and equity_curve:
            last_row = frame.iloc[-1]
            trade = self._close_position(position, float(last_row["close"]), last_row["timestamp"], fee_ratio, symbol, exit_reason="force_close")
            cash_balance += trade.stake_amount + trade.profit_abs
            trades.append(trade)
            signals.append(
                BacktestSignalRecord(
                    timestamp=last_row["timestamp"],
                    price=float(last_row["close"]),
                    signal="SELL",
                    confidence=100.0,
                    indicators={
                        "composite_score": float(last_row["composite_score"] or 0.0),
                        "research_run_id": research_run_id,
                    },
                    reasoning="Factor blend force close",
                )
            )
            equity_curve[-1] = BacktestEquityPointRecord(
                timestamp=last_row["timestamp"],
                equity=cash_balance,
                pnl_abs=cash_balance - initial_cash,
                drawdown_pct=0.0,
            )

        equity_curve = self._decorate_drawdowns(equity_curve)
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

    def _opened_bar_index(self, equity_curve: list[BacktestEquityPointRecord], opened_at: datetime) -> int:
        for index, point in enumerate(equity_curve, start=1):
            if point.timestamp >= opened_at:
                return index
        return len(equity_curve) + 1

    def _profit_ratio(self, position: FactorBacktestPosition, price: float, fee_ratio: float) -> float:
        net_value = position.amount * price * (1.0 - fee_ratio)
        if position.stake_amount <= 0:
            return 0.0
        return (net_value - position.stake_amount) / position.stake_amount

    def _close_position(
        self,
        position: FactorBacktestPosition,
        price: float,
        timestamp: datetime,
        fee_ratio: float,
        symbol: str,
        exit_reason: str = "factor_exit",
    ) -> BacktestTradeRecord:
        gross = position.amount * price
        net = gross * (1.0 - fee_ratio)
        profit_abs = net - position.stake_amount
        duration_minutes = max(int((timestamp - position.opened_at).total_seconds() // 60), 0)
        return BacktestTradeRecord(
            opened_at=position.opened_at,
            closed_at=timestamp,
            entry_price=position.entry_price,
            exit_price=price,
            stake_amount=position.stake_amount,
            amount=position.amount,
            profit_abs=profit_abs,
            profit_pct=(profit_abs / position.stake_amount * 100.0) if position.stake_amount else 0.0,
            duration_minutes=duration_minutes,
            entry_tag="factor_entry",
            exit_reason=exit_reason,
            leverage=1.0,
            pair=symbol,
        )

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
