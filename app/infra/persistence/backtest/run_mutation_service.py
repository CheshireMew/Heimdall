from __future__ import annotations

from datetime import datetime
from typing import Any

from app.contracts.backtest import BacktestEquityPointRecord, BacktestSignalRecord, BacktestTradeRecord
from app.contracts.backtest_run import (
    StoredBacktestRun,
    parse_run_metadata,
)
from app.infra.db.database import DatabaseRuntime
from app.infra.db.schema import BacktestEquityPoint, BacktestRun, BacktestTrade
from app.infra.persistence.backtest.result_store import (
    build_signal_rows,
    build_trade_rows,
    equity_point_record_from_row,
    replace_run_rows,
    result_signal_counts,
    store_run_rows,
    trade_record_from_row,
)


class BacktestRunMutationService:
    def __init__(self, *, database_runtime: DatabaseRuntime) -> None:
        self.database_runtime = database_runtime

    def create_run(
        self,
        *,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
        status: str,
        execution_mode: str,
        engine: str,
        metadata: dict[str, Any],
        total_candles: int = 0,
        total_signals: int = 0,
        buy_signals: int = 0,
        sell_signals: int = 0,
        hold_signals: int = 0,
        initial_equity: BacktestEquityPointRecord | None = None,
    ) -> int:
        with self.database_runtime.session_scope() as session:
            run = BacktestRun(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date,
                status=status,
                execution_mode=execution_mode,
                engine=engine,
                total_candles=total_candles,
                total_signals=total_signals,
                buy_signals=buy_signals,
                sell_signals=sell_signals,
                hold_signals=hold_signals,
                metadata_info=metadata,
            )
            session.add(run)
            session.flush()
            if initial_equity is not None:
                session.add(
                    BacktestEquityPoint(
                        backtest_id=run.id,
                        timestamp=initial_equity.timestamp,
                        equity=initial_equity.equity,
                        pnl_abs=initial_equity.pnl_abs,
                        drawdown_pct=initial_equity.drawdown_pct,
                    )
                )
                session.flush()
            return int(run.id)

    def store_completed_result(
        self,
        *,
        run_id: int,
        result,
        default_pair: str,
        metadata: dict[str, Any],
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        clear_existing: bool = False,
    ) -> None:
        with self.database_runtime.session_scope() as session:
            run = session.query(BacktestRun).filter(BacktestRun.id == run_id).first()
            if not run:
                raise ValueError(f"回测记录不存在: {run_id}")
            replace_run_rows(
                session=session,
                run_id=run_id,
                result=result,
                default_pair=default_pair,
                clear_existing=clear_existing,
            )
            buy_count, sell_count, hold_count = result_signal_counts(result)
            run.start_date = start_date or run.start_date
            run.end_date = end_date or result.end_date
            run.status = "completed"
            run.total_candles = int(result.total_candles)
            run.total_signals = len(result.signals)
            run.buy_signals = buy_count
            run.sell_signals = sell_count
            run.hold_signals = hold_count
            run.metadata_info = metadata
            session.flush()

    def get_run(self, run_id: int) -> StoredBacktestRun | None:
        with self.database_runtime.session_scope() as session:
            run = session.query(BacktestRun).filter(BacktestRun.id == run_id).first()
            if not run:
                return None
            return StoredBacktestRun(
                id=int(run.id),
                symbol=run.symbol,
                timeframe=run.timeframe,
                start_date=run.start_date,
                end_date=run.end_date,
                status=run.status,
                execution_mode=run.execution_mode,
                engine=run.engine,
                metadata=parse_run_metadata(run.metadata_info),
            )

    def mark_run_failed(self, *, run_id: int, metadata: dict[str, Any]) -> bool:
        with self.database_runtime.session_scope() as session:
            run = session.query(BacktestRun).filter(BacktestRun.id == run_id).first()
            if not run:
                return False
            run.status = "failed"
            run.metadata_info = metadata
            session.flush()
            return True

    def store_completed_rows(
        self,
        *,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
        status: str,
        execution_mode: str,
        engine: str,
        total_candles: int,
        signals: list[BacktestSignalRecord],
        trades: list[BacktestTradeRecord],
        equity_curve: list[BacktestEquityPointRecord],
        metadata: dict[str, Any],
    ) -> int:
        run_id = self.create_run(
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            status=status,
            execution_mode=execution_mode,
            engine=engine,
            total_candles=total_candles,
            total_signals=len(signals),
            buy_signals=sum(1 for item in signals if item.signal == "BUY"),
            sell_signals=sum(1 for item in signals if item.signal == "SELL"),
            hold_signals=max(total_candles - len(signals), 0),
            metadata=metadata,
        )
        with self.database_runtime.session_scope() as session:
            store_run_rows(
                session=session,
                run_id=run_id,
                signals=signals,
                trades=trades,
                equity_curve=equity_curve,
                default_pair=symbol,
            )
        return run_id

    def get_running_paper_run(self, *, run_id: int, engine: str) -> StoredBacktestRun | None:
        with self.database_runtime.session_scope() as session:
            run = session.query(BacktestRun).filter(BacktestRun.id == run_id).first()
            if not run:
                return None
            if run.execution_mode != "paper_live" or run.engine != engine or run.status != "running":
                return None
            return StoredBacktestRun(
                id=int(run.id),
                symbol=run.symbol,
                timeframe=run.timeframe,
                start_date=run.start_date,
                end_date=run.end_date,
                status=run.status,
                execution_mode=run.execution_mode,
                engine=run.engine,
                metadata=parse_run_metadata(run.metadata_info),
            )

    def store_paper_snapshot(
        self,
        *,
        run_id: int,
        engine: str,
        result,
        default_pair: str,
        metadata: dict[str, Any],
        end_date: datetime,
    ) -> None:
        with self.database_runtime.session_scope() as session:
            run = session.query(BacktestRun).filter(BacktestRun.id == run_id).first()
            if not run:
                raise ValueError(f"模拟盘记录不存在: {run_id}")
            if run.execution_mode != "paper_live" or run.engine != engine:
                raise ValueError(f"模拟盘记录类型不匹配: {run_id}")
            replace_run_rows(
                session=session,
                run_id=run.id,
                result=result,
                default_pair=default_pair,
                clear_existing=True,
            )
            buy_count, sell_count, hold_count = result_signal_counts(result)
            run.end_date = end_date
            run.total_candles = int(result.total_candles)
            run.total_signals = len(result.signals)
            run.buy_signals = buy_count
            run.sell_signals = sell_count
            run.hold_signals = hold_count
            run.metadata_info = metadata
            session.flush()

    def list_trade_records(self, run_id: int) -> list[BacktestTradeRecord]:
        with self.database_runtime.session_scope() as session:
            trades = (
                session.query(BacktestTrade)
                .filter(BacktestTrade.backtest_id == run_id)
                .order_by(BacktestTrade.opened_at.asc())
                .all()
            )
            return [trade_record_from_row(item) for item in trades]

    def list_equity_records(self, run_id: int) -> list[BacktestEquityPointRecord]:
        with self.database_runtime.session_scope() as session:
            equity = (
                session.query(BacktestEquityPoint)
                .filter(BacktestEquityPoint.backtest_id == run_id)
                .order_by(BacktestEquityPoint.timestamp.asc())
                .all()
            )
            return [equity_point_record_from_row(item) for item in equity]

    def append_factor_paper_increment(
        self,
        *,
        run_id: int,
        new_signals: list[BacktestSignalRecord],
        new_trades: list[BacktestTradeRecord],
        new_equity_points: list[BacktestEquityPointRecord],
        metadata: dict[str, Any],
        end_date: datetime,
    ) -> None:
        with self.database_runtime.session_scope() as session:
            run = session.query(BacktestRun).filter(BacktestRun.id == run_id).first()
            if not run:
                raise ValueError(f"因子模拟盘记录不存在: {run_id}")
            if new_signals:
                session.bulk_save_objects(build_signal_rows(run_id=run.id, signals=new_signals))
            if new_trades:
                session.bulk_save_objects(build_trade_rows(run_id=run.id, trades=new_trades, default_pair=run.symbol))
            if new_equity_points:
                session.bulk_save_objects([
                    BacktestEquityPoint(
                        backtest_id=run.id,
                        timestamp=item.timestamp,
                        equity=item.equity,
                        pnl_abs=item.pnl_abs,
                        drawdown_pct=item.drawdown_pct,
                    )
                    for item in new_equity_points
                ])
            session.flush()

            run.total_candles += len(new_equity_points)
            run.total_signals += len(new_signals)
            run.buy_signals += sum(1 for item in new_signals if item.signal == "BUY")
            run.sell_signals += sum(1 for item in new_signals if item.signal == "SELL")
            run.hold_signals = max(run.total_candles - run.total_signals, 0)
            run.end_date = end_date
            run.metadata_info = metadata
            session.flush()

    def get_paper_run(self, *, run_id: int, engine: str) -> StoredBacktestRun | None:
        with self.database_runtime.session_scope() as session:
            run = session.query(BacktestRun).filter(BacktestRun.id == run_id).first()
            if not run:
                return None
            if run.execution_mode != "paper_live" or run.engine != engine:
                return None
            return StoredBacktestRun(
                id=int(run.id),
                symbol=run.symbol,
                timeframe=run.timeframe,
                start_date=run.start_date,
                end_date=run.end_date,
                status=run.status,
                execution_mode=run.execution_mode,
                engine=run.engine,
                metadata=parse_run_metadata(run.metadata_info),
            )

    def set_paper_status(
        self,
        *,
        run_id: int,
        engine: str,
        status: str,
        metadata: dict[str, Any],
    ) -> None:
        with self.database_runtime.session_scope() as session:
            run = session.query(BacktestRun).filter(BacktestRun.id == run_id).first()
            if not run:
                return
            if run.execution_mode != "paper_live" or run.engine != engine:
                return
            run.status = status
            run.metadata_info = metadata
            session.flush()
