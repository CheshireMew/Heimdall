from __future__ import annotations

from datetime import datetime
from typing import Any

from app.infra.db.schema import BacktestEquityPoint, BacktestRun, BacktestSignal, BacktestTrade
from app.services.backtest.freqtrade_report_builder import FreqtradeReportBuilder
from app.services.backtest.models import BacktestEquityPointRecord, BacktestSignalRecord, BacktestTradeRecord
from app.services.backtest.run_contract import update_paper_metadata

from .paper_position_service import PaperPosition, PaperPositionService


class PaperPersistenceService:
    def __init__(self, *, report_builder: FreqtradeReportBuilder, position_service: PaperPositionService) -> None:
        self.report_builder = report_builder
        self.position_service = position_service

    def persist_increment(
        self,
        *,
        session,
        run: BacktestRun,
        metadata: dict[str, Any],
        runtime_state: dict[str, Any],
        positions: dict[str, PaperPosition],
        cash_balance: float,
        new_signals: list[BacktestSignalRecord],
        new_trades: list[BacktestTradeRecord],
        new_equity_points: list[BacktestEquityPointRecord],
        now: datetime,
    ) -> None:
        if new_signals:
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
                    for item in new_signals
                ]
            )
        if new_trades:
            session.bulk_save_objects(
                [
                    BacktestTrade(
                        backtest_id=run.id,
                        pair=item.pair or run.symbol,
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
                    for item in new_trades
                ]
            )

        all_equity_rows = (
            session.query(BacktestEquityPoint)
            .filter(BacktestEquityPoint.backtest_id == run.id)
            .order_by(BacktestEquityPoint.timestamp.asc())
            .all()
        )
        highest_equity = max([point.equity for point in all_equity_rows], default=float(metadata.get("initial_cash", 0.0)))
        persisted_equity_points: list[BacktestEquityPoint] = []
        for item in new_equity_points:
            highest_equity = max(highest_equity, item.equity)
            drawdown_pct = ((highest_equity - item.equity) / highest_equity * 100.0) if highest_equity else 0.0
            persisted_equity_points.append(
                BacktestEquityPoint(
                    backtest_id=run.id,
                    timestamp=item.timestamp,
                    equity=item.equity,
                    pnl_abs=item.pnl_abs,
                    drawdown_pct=drawdown_pct,
                )
            )
        if persisted_equity_points:
            session.bulk_save_objects(persisted_equity_points)
        session.flush()

        run.total_signals += len(new_signals)
        run.buy_signals += sum(1 for item in new_signals if item.signal == "BUY")
        run.sell_signals += sum(1 for item in new_signals if item.signal == "SELL")
        run.hold_signals = max(run.total_candles - run.total_signals, 0)
        run.end_date = max((item.timestamp for item in new_equity_points), default=run.end_date or now)

        all_trades = (
            session.query(BacktestTrade)
            .filter(BacktestTrade.backtest_id == run.id)
            .order_by(BacktestTrade.opened_at.asc())
            .all()
        )
        all_equity = (
            session.query(BacktestEquityPoint)
            .filter(BacktestEquityPoint.backtest_id == run.id)
            .order_by(BacktestEquityPoint.timestamp.asc())
            .all()
        )
        trade_records = [
            BacktestTradeRecord(
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
                pair=item.pair,
            )
            for item in all_trades
        ]
        equity_records = [
            BacktestEquityPointRecord(
                timestamp=item.timestamp,
                equity=item.equity,
                pnl_abs=item.pnl_abs,
                drawdown_pct=item.drawdown_pct,
            )
            for item in all_equity
        ]
        report = self.report_builder.build_report(
            trades=trade_records,
            equity_curve=equity_records,
            initial_cash=float(metadata.get("initial_cash", 0.0)),
            start_date=run.start_date,
            end_date=run.end_date or now,
        )
        report["strategy"] = {
            "key": metadata.get("strategy_key"),
            "name": metadata.get("strategy_name"),
            "version": metadata.get("strategy_version"),
            "template": metadata.get("strategy_template"),
        }
        report["portfolio"] = {
            **(metadata.get("portfolio") or {}),
            "stake_currency": self.report_builder.quote_currency((metadata.get("symbols") or [run.symbol])[0]),
        }
        serialized_positions = self.position_service.serialize_positions(positions)
        runtime_payload = {
            "cash_balance": cash_balance,
            "last_processed": runtime_state.get("last_processed") or {},
            "positions": serialized_positions,
        }
        run.metadata_info = update_paper_metadata(
            metadata,
            runtime_state=runtime_payload,
            last_updated=now.isoformat(),
            report=report,
        )
        session.flush()
