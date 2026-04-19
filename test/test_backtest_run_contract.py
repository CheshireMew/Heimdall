from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime

import pytest

from app.infra.db.schema import BacktestRun
from app.schemas.backtest import BacktestPortfolioRequest
from app.services.backtest.run_repository import BacktestRunRepository
from app.services.backtest.run_contract import update_paper_metadata
from app.services.backtest.serializers import serialize_backtest_run


def _scoped_session(session):
    @contextmanager
    def scope():
        yield session

    return scope


def test_repository_filters_by_execution_mode_in_query(db_session, monkeypatch):
    db_session.add_all(
        [
            BacktestRun(
                symbol="BTC/USDT",
                timeframe="1h",
                start_date=datetime(2026, 1, 1),
                end_date=datetime(2026, 1, 2),
                status="completed",
                execution_mode="backtest",
                engine="Freqtrade",
                metadata_info={"strategy_key": "alpha"},
            ),
            BacktestRun(
                symbol="ETH/USDT",
                timeframe="1h",
                start_date=datetime(2026, 1, 3),
                end_date=datetime(2026, 1, 4),
                status="running",
                execution_mode="paper_live",
                engine="FreqtradePaper",
                metadata_info={"strategy_key": "beta"},
            ),
        ]
    )
    db_session.flush()
    monkeypatch.setattr("app.services.backtest.run_repository.session_scope", _scoped_session(db_session))

    repository = BacktestRunRepository()
    runs = repository.list_runs("paper_live")

    assert len(runs) == 1
    assert runs[0]["symbol"] == "ETH/USDT"
    assert runs[0]["metadata"]["execution_mode"] == "paper_live"
    assert runs[0]["metadata"]["engine"] == "FreqtradePaper"


def test_serializer_projects_mode_and_engine_from_columns():
    run = BacktestRun(
        id=7,
        symbol="BTC/USDT",
        timeframe="4h",
        start_date=datetime(2026, 2, 1),
        end_date=datetime(2026, 2, 2),
        created_at=datetime(2026, 2, 3),
        status="completed",
        execution_mode="paper_live",
        engine="FactorBlendPaper",
        metadata_info={"strategy_key": "factor_blend", "report": {"profit_pct": 12.5}},
    )

    payload = serialize_backtest_run(run)

    assert payload["metadata"]["strategy_key"] == "factor_blend"
    assert payload["metadata"]["execution_mode"] == "paper_live"
    assert payload["metadata"]["engine"] == "FactorBlendPaper"
    assert payload["report"] == {"profit_pct": 12.5}


def test_update_paper_metadata_preserves_last_synced_end():
    payload = update_paper_metadata(
        {"symbols": ["BTC/USDT"]},
        runtime_state={
            "cash_balance": 10000,
            "last_processed": {"BTC/USDT": 1710000000000},
            "last_synced_end": 1710000000000,
            "positions": {},
        },
        last_updated="2026-03-28T10:00:00",
    )

    assert payload["runtime_state"]["last_synced_end"] == 1710000000000


def test_backtest_portfolio_symbols_use_market_catalog_contract():
    payload = BacktestPortfolioRequest(symbols=["btc", "ETH/USDT", "btc/usdt"])

    assert payload.symbols == ["BTC/USDT", "ETH/USDT"]


def test_backtest_portfolio_rejects_unknown_symbol():
    with pytest.raises(ValueError, match="回测不支持的交易对"):
        BacktestPortfolioRequest(symbols=["BAD\\USDT"])
