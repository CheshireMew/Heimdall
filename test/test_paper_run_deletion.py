from __future__ import annotations

import asyncio
from contextlib import contextmanager
from datetime import datetime

from app.infra.db.schema import BacktestRun
from app.schemas.backtest import BacktestDeleteResponse
from app.services.backtest.paper_manager import PaperRunManager
from app.services.backtest.run_repository import BacktestRunRepository


def _scoped_session(session):
    @contextmanager
    def scope():
        yield session

    return scope


def test_delete_paper_run_updates_stop_state_and_removes_row(db_session, monkeypatch):
    run = BacktestRun(
        symbol="BTC/USDT",
        timeframe="1h",
        start_date=datetime(2026, 3, 28, 10, 0, 0),
        end_date=datetime(2026, 3, 28, 10, 0, 0),
        status="running",
        execution_mode="paper_live",
        engine="FreqtradePaper",
        metadata_info={
            "symbols": ["BTC/USDT"],
            "runtime_state": {
                "cash_balance": 10000,
                "last_processed": {"BTC/USDT": None},
                "last_synced_end": None,
                "positions": {},
            },
            "paper_live": {
                "cash_balance": 10000,
                "open_positions": 0,
                "positions": [],
                "last_updated": "2026-03-28T10:00:00",
            },
        },
    )
    db_session.add(run)
    db_session.flush()

    session_scope = _scoped_session(db_session)
    monkeypatch.setattr("app.services.backtest.paper_manager.session_scope", session_scope)
    monkeypatch.setattr("app.services.backtest.run_repository.session_scope", session_scope)

    manager = PaperRunManager(
        strategy_query_service=object(),
        freqtrade_service=object(),
        report_builder=object(),
        run_repository=BacktestRunRepository(),
    )

    result = asyncio.run(manager.delete_run(run.id))

    assert result == BacktestDeleteResponse(success=True, run_id=run.id, message="模拟盘记录已删除")
    assert db_session.get(BacktestRun, run.id) is None
