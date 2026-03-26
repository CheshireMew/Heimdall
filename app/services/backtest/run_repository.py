from __future__ import annotations

from app.infra.db.database import session_scope
from app.infra.db.schema import BacktestEquityPoint, BacktestRun, BacktestSignal, BacktestTrade
from app.services.backtest.run_contract import normalize_run_metadata
from app.services.backtest.serializers import (
    serialize_backtest_equity_point,
    serialize_backtest_run,
    serialize_backtest_signal,
    serialize_backtest_trade,
)


class BacktestRunRepository:
    def repair_run_contracts(self) -> int:
        with session_scope() as session:
            runs = session.query(BacktestRun).all()
            updated = 0
            for run in runs:
                normalized_metadata, changed = normalize_run_metadata(run.metadata_info)
                if not changed:
                    continue
                run.metadata_info = normalized_metadata
                updated += 1
            if updated:
                session.flush()
            return updated

    def list_runs(self, execution_mode: str = "backtest") -> list[dict]:
        with session_scope() as session:
            runs = session.query(BacktestRun).order_by(BacktestRun.created_at.desc()).all()
            return [
                serialize_backtest_run(run, include_signals=False)
                for run in runs
                if self._matches_execution_mode(run, execution_mode)
            ]

    def get_run(self, backtest_id: int, page: int, page_size: int, execution_mode: str | None = None) -> dict | None:
        with session_scope() as session:
            backtest_run = session.query(BacktestRun).filter(BacktestRun.id == backtest_id).first()
            if not backtest_run:
                return None
            if execution_mode and not self._matches_execution_mode(backtest_run, execution_mode):
                return None

            total = session.query(BacktestSignal).filter(BacktestSignal.backtest_id == backtest_id).count()
            signals = (
                session.query(BacktestSignal)
                .filter(BacktestSignal.backtest_id == backtest_id)
                .order_by(BacktestSignal.timestamp.asc())
                .offset((page - 1) * page_size)
                .limit(page_size)
                .all()
            )
            trades = (
                session.query(BacktestTrade)
                .filter(BacktestTrade.backtest_id == backtest_id)
                .order_by(BacktestTrade.opened_at.asc())
                .all()
            )
            equity_points = (
                session.query(BacktestEquityPoint)
                .filter(BacktestEquityPoint.backtest_id == backtest_id)
                .order_by(BacktestEquityPoint.timestamp.asc())
                .all()
            )

            payload = serialize_backtest_run(backtest_run, include_signals=False)
            payload["signals"] = [serialize_backtest_signal(signal) for signal in signals]
            payload["trades"] = [serialize_backtest_trade(trade) for trade in trades]
            payload["equity_curve"] = [serialize_backtest_equity_point(point) for point in equity_points]
            payload["pagination"] = {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size,
            }
            return payload

    def _matches_execution_mode(self, run: BacktestRun, execution_mode: str) -> bool:
        metadata = run.metadata_info or {}
        current_mode = metadata.get("execution_mode") or "backtest"
        return current_mode == execution_mode
