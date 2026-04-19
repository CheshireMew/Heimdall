from __future__ import annotations

from datetime import datetime
from typing import Any

from app.infra.db.schema import BacktestEquityPoint, BacktestRun
from app.services.backtest.freqtrade_report_builder import FreqtradeReportBuilder
from app.services.backtest.result_store import build_signal_rows, build_trade_rows
from app.contracts.backtest import BacktestEquityPointRecord, BacktestSignalRecord, BacktestTradeRecord
from app.services.backtest.run_contract import update_paper_metadata

from .signal_execution_core import FactorSignalExecutionCore, FactorSignalPosition


class FactorPaperPersistenceService:
    def __init__(
        self,
        *,
        report_builder: FreqtradeReportBuilder,
        execution_core: FactorSignalExecutionCore,
    ) -> None:
        self.report_builder = report_builder
        self.execution_core = execution_core

    def persist_increment(
        self,
        *,
        session,
        run: BacktestRun,
        metadata: dict[str, Any],
        runtime_state: dict[str, Any],
        position: FactorSignalPosition | None,
        cash_balance: float,
        new_signals: list[BacktestSignalRecord],
        new_trades: list[BacktestTradeRecord],
        new_equity_points: list[BacktestEquityPointRecord],
        now: datetime,
    ) -> None:
        if new_signals:
            session.bulk_save_objects(build_signal_rows(run_id=run.id, signals=new_signals))
        if new_trades:
            session.bulk_save_objects(build_trade_rows(run_id=run.id, trades=new_trades, default_pair=run.symbol))

        if new_equity_points:
            peak = max(
                [
                    point.equity
                    for point in session.query(BacktestEquityPoint)
                    .filter(BacktestEquityPoint.backtest_id == run.id)
                    .all()
                ],
                default=float(metadata.get("initial_cash", 0.0)),
            )
            persisted = []
            for item in new_equity_points:
                peak = max(peak, item.equity)
                drawdown = ((peak - item.equity) / peak * 100.0) if peak else 0.0
                persisted.append(
                    BacktestEquityPoint(
                        backtest_id=run.id,
                        timestamp=item.timestamp,
                        equity=item.equity,
                        pnl_abs=item.pnl_abs,
                        drawdown_pct=drawdown,
                    )
                )
            session.bulk_save_objects(persisted)
        session.flush()

        run.total_candles += len(new_equity_points)
        run.total_signals += len(new_signals)
        run.buy_signals += sum(1 for item in new_signals if item.signal == "BUY")
        run.sell_signals += sum(1 for item in new_signals if item.signal == "SELL")
        run.hold_signals = max(run.total_candles - run.total_signals, 0)
        run.end_date = max((item.timestamp for item in new_equity_points), default=run.end_date or now)

        trades = (
            session.query(BacktestTrade)
            .filter(BacktestTrade.backtest_id == run.id)
            .order_by(BacktestTrade.opened_at.asc())
            .all()
        )
        equity = (
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
            for item in trades
        ]
        equity_records = [
            BacktestEquityPointRecord(
                timestamp=item.timestamp,
                equity=item.equity,
                pnl_abs=item.pnl_abs,
                drawdown_pct=item.drawdown_pct,
            )
            for item in equity
        ]
        report = self.report_builder.build_report(
            trades=trade_records,
            equity_curve=equity_records,
            initial_cash=float(metadata.get("initial_cash", 0.0)),
            start_date=run.start_date,
            end_date=run.end_date or now,
        )
        symbol = str((metadata.get("symbols") or [run.symbol])[0])
        serialized_position = self.execution_core.serialize_position(position, symbol=symbol)
        runtime_payload = {
            **{
                key: value
                for key, value in runtime_state.items()
                if key not in {"cash_balance", "positions", "last_processed"}
            },
            "cash_balance": cash_balance,
            "last_processed": dict(runtime_state.get("last_processed") or {}),
            "positions": {symbol: serialized_position} if serialized_position else {},
        }
        run.metadata_info = update_paper_metadata(
            metadata,
            runtime_state=runtime_payload,
            last_updated=now.isoformat(),
            report=report,
        )
        session.flush()
