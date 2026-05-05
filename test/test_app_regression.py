from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

import pytest
from fastapi import Request
from fastapi.testclient import TestClient

import app.lifecycle as lifecycle_module
import app.main as main_module
import app.web as web_module
import app.background_runtime as background_runtime_module
from app.exceptions import unhandled_exception_handler
from app.runtime import AppRuntimeServices
from app.runtime_refs import (
    BACKTEST_FREQTRADE_SERVICE,
    BACKTEST_PAPER_RUN_MANAGER,
    BACKTEST_REPORT_BUILDER,
    BACKTEST_RUN_REPOSITORY,
    BACKTEST_STRATEGY_QUERY_SERVICE,
    FACTORS_PAPER_PERSISTENCE_SERVICE,
    FACTORS_PAPER_RUN_MANAGER,
    FACTORS_RESEARCH_REPOSITORY,
    FACTORS_RESEARCH_SERVICE,
    FACTORS_SIGNAL_EXECUTION_CORE,
    INFRA_CACHE_SERVICE,
    INFRA_DATABASE_RUNTIME,
    INFRA_EXCHANGE_GATEWAY,
    INFRA_KLINE_STORE,
    MARKET_BINANCE_MARKET_INTEL,
    MARKET_BINANCE_MARKET_RESEARCH_STORE,
    MARKET_BINANCE_MARKET_SNAPSHOT,
    MARKET_FUNDING_RATE_STORE,
    MARKET_INDICATOR_REPOSITORY,
    MARKET_MARKET_DATA_SERVICE,
    SYSTEM_MARKET_SCHEDULER_RUNTIME,
)


@pytest.mark.asyncio
async def test_lifespan_restores_and_stops_managers(monkeypatch):
    events: list[str] = []

    class FakeManager:
        async def restore_active_runs(self):
            events.append("restore")

        async def shutdown(self):
            events.append("shutdown")

    class FakeSchedulerRuntime:
        def start(self):
            events.append("start_scheduler")

        async def shutdown(self):
            events.append("scheduler_shutdown")

    class FakeSnapshot:
        async def start(self, **kwargs):
            events.append("snapshot_start")

        async def shutdown(self):
            events.append("snapshot_shutdown")

    class FakeSpotMarket:
        async def get_ticker_24hr(self):
            return {}

    class FakeUsdmMarket:
        async def get_ticker_24hr(self):
            return {}

        async def get_mark_price(self):
            return {}

    class FakeBinanceMarket:
        spot = FakeSpotMarket()
        usdm = FakeUsdmMarket()

        def start(self):
            events.append("binance_market_start")

        async def shutdown(self):
            events.append("binance_market_shutdown")

    class FakeDatabaseRuntime:
        def dispose(self):
            events.append("dispose_db")

    paper_manager = FakeManager()
    factor_manager = FakeManager()
    snapshot = FakeSnapshot()
    binance_market = FakeBinanceMarket()

    monkeypatch.setattr(lifecycle_module, "_init_db", lambda *_args: events.append("init_db"))
    monkeypatch.setattr(
        lifecycle_module,
        "build_app_runtime_services",
        lambda: AppRuntimeServices.from_entries({
            INFRA_EXCHANGE_GATEWAY: object(),
            INFRA_DATABASE_RUNTIME: FakeDatabaseRuntime(),
            INFRA_KLINE_STORE: object(),
            INFRA_CACHE_SERVICE: object(),
            MARKET_MARKET_DATA_SERVICE: object(),
            MARKET_INDICATOR_REPOSITORY: object(),
            MARKET_FUNDING_RATE_STORE: object(),
            MARKET_BINANCE_MARKET_SNAPSHOT: snapshot,
            MARKET_BINANCE_MARKET_INTEL: binance_market,
            MARKET_BINANCE_MARKET_RESEARCH_STORE: object(),
            BACKTEST_RUN_REPOSITORY: object(),
            BACKTEST_FREQTRADE_SERVICE: object(),
            BACKTEST_STRATEGY_QUERY_SERVICE: object(),
            BACKTEST_REPORT_BUILDER: object(),
            BACKTEST_PAPER_RUN_MANAGER: paper_manager,
            FACTORS_RESEARCH_REPOSITORY: object(),
            FACTORS_RESEARCH_SERVICE: object(),
            FACTORS_SIGNAL_EXECUTION_CORE: object(),
            FACTORS_PAPER_PERSISTENCE_SERVICE: object(),
            FACTORS_PAPER_RUN_MANAGER: factor_manager,
            SYSTEM_MARKET_SCHEDULER_RUNTIME: FakeSchedulerRuntime(),
        }),
    )
    monkeypatch.setattr(
        background_runtime_module._ProcessFileLock, "acquire", lambda self: True
    )
    monkeypatch.setattr(
        background_runtime_module._ProcessFileLock, "release", lambda self: None
    )
    async with lifecycle_module.lifespan(main_module.app):
        events.append("inside")
        await main_module.app.state.database_task
        await main_module.app.state.background_services_task
        await main_module.app.state.background_runtime.wait_until_started()

    assert events[0] == "inside"
    assert events.index("init_db") < events.index("start_scheduler")
    assert events.index("snapshot_start") < events.index("restore")
    assert events.index("snapshot_start") < events.index("binance_market_start")
    assert events.index("binance_market_start") < events.index("restore")
    assert events.count("restore") == 2
    assert events[-6:] == [
        "binance_market_shutdown",
        "snapshot_shutdown",
        "shutdown",
        "shutdown",
        "scheduler_shutdown",
        "dispose_db",
    ]


def test_root_returns_frontend_boot_payload_when_build_missing(
    api_harness, monkeypatch
):
    monkeypatch.setattr(web_module, "FRONTEND_DIST_DIR", Path("Z:/missing"))
    monkeypatch.setattr(
        web_module, "FRONTEND_INDEX_FILE", Path("Z:/missing/index.html")
    )

    response = api_harness["client"].get("/")

    assert response.status_code == 200
    assert response.json()["message"] == "Heimdall API is running"
    assert response.json()["docs"] == "/docs"


def test_root_and_spa_fallback_serve_built_frontend(api_harness, monkeypatch):
    dist_dir = web_module.BASE_DIR / "frontend" / "dist"
    assets_dir = dist_dir / "assets"
    dist_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    index_file = dist_dir / "index.html"
    asset_file = assets_dir / "app.js"
    original_index = (
        index_file.read_text(encoding="utf-8") if index_file.exists() else None
    )
    original_asset = (
        asset_file.read_text(encoding="utf-8") if asset_file.exists() else None
    )

    try:
        index_file.write_text("<html><body>frontend</body></html>", encoding="utf-8")
        asset_file.write_text("console.log('ok')", encoding="utf-8")

        monkeypatch.setattr(web_module, "FRONTEND_DIST_DIR", dist_dir)
        monkeypatch.setattr(web_module, "FRONTEND_INDEX_FILE", index_file)

        root_response = api_harness["client"].get("/")
        route_response = api_harness["client"].get("/backtest")
        asset_response = api_harness["client"].get("/assets/app.js")

        assert root_response.status_code == 200
        assert "frontend" in root_response.text
        assert route_response.status_code == 200
        assert "frontend" in route_response.text
        assert asset_response.status_code == 200
        assert "console.log" in asset_response.text
    finally:
        if original_index is None:
            index_file.unlink(missing_ok=True)
        else:
            index_file.write_text(original_index, encoding="utf-8")
        if original_asset is None:
            asset_file.unlink(missing_ok=True)
        else:
            asset_file.write_text(original_asset, encoding="utf-8")


@pytest.mark.asyncio
async def test_global_exception_handler_returns_internal_server_error():
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/boom",
            "headers": [],
            "scheme": "http",
            "server": ("testserver", 80),
            "client": ("testclient", 1234),
            "query_string": b"",
            "root_path": "",
        }
    )

    response = await unhandled_exception_handler(request, RuntimeError("boom"))

    assert response.status_code == 500
    assert response.body == b'{"detail":"Internal server error"}'


def test_frontend_fallback_rejects_unknown_reserved_paths(api_harness):
    response = api_harness["client"].get("/api/private")

    assert response.status_code == 404
