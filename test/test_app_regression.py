from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import Request
from fastapi.testclient import TestClient

import app.main as main_module
from app.infra.db.database import _build_kline_symbol_contract_statements


@pytest.mark.asyncio
async def test_lifespan_restores_and_stops_managers(monkeypatch):
    events: list[str] = []

    class FakeManager:
        async def restore_active_runs(self):
            events.append("restore")

        async def shutdown(self):
            events.append("shutdown")

    class FakeScheduler:
        running = True

        def shutdown(self):
            events.append("scheduler_shutdown")

    paper_manager = FakeManager()
    factor_manager = FakeManager()

    monkeypatch.setattr(main_module, "_init_db", lambda: events.append("init_db"))
    monkeypatch.setattr(main_module, "get_paper_run_manager", lambda: paper_manager)
    monkeypatch.setattr(main_module, "get_factor_paper_run_manager", lambda: factor_manager)
    monkeypatch.setattr(
        main_module,
        "_import_market_cron_module",
        lambda: SimpleNamespace(
            start_scheduler=lambda: events.append("start_scheduler"),
            scheduler=FakeScheduler(),
        ),
    )

    async with main_module.lifespan(main_module.app):
        events.append("inside")
        await main_module.app.state.database_task
        await main_module.app.state.background_services_task

    assert events[0] == "inside"
    assert events.index("init_db") < events.index("start_scheduler")
    assert events.count("restore") == 2
    assert events[-3:] == ["shutdown", "shutdown", "scheduler_shutdown"]


def test_root_returns_frontend_boot_payload_when_build_missing(api_harness, monkeypatch):
    monkeypatch.setattr(main_module, "FRONTEND_DIST_DIR", Path("Z:/missing"))
    monkeypatch.setattr(main_module, "FRONTEND_INDEX_FILE", Path("Z:/missing/index.html"))

    response = api_harness["client"].get("/")

    assert response.status_code == 200
    assert response.json()["message"] == "Heimdall API is running"
    assert response.json()["docs"] == "/docs"


def test_kline_symbol_contract_migrates_short_postgres_column():
    assert _build_kline_symbol_contract_statements("postgresql", 20) == [
        "ALTER TABLE klines ALTER COLUMN symbol TYPE VARCHAR(80)"
    ]
    assert _build_kline_symbol_contract_statements("postgresql", 80) == []


def test_root_and_spa_fallback_serve_built_frontend(api_harness, monkeypatch):
    dist_dir = main_module.BASE_DIR / "frontend" / "dist"
    assets_dir = dist_dir / "assets"
    dist_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    index_file = dist_dir / "index.html"
    asset_file = assets_dir / "app.js"
    original_index = index_file.read_text(encoding="utf-8") if index_file.exists() else None
    original_asset = asset_file.read_text(encoding="utf-8") if asset_file.exists() else None

    try:
        index_file.write_text("<html><body>frontend</body></html>", encoding="utf-8")
        asset_file.write_text("console.log('ok')", encoding="utf-8")

        monkeypatch.setattr(main_module, "FRONTEND_DIST_DIR", dist_dir)
        monkeypatch.setattr(main_module, "FRONTEND_INDEX_FILE", index_file)

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

    response = await main_module.global_exception_handler(request, RuntimeError("boom"))

    assert response.status_code == 500
    assert response.body == b'{"detail":"Internal server error"}'


def test_frontend_fallback_rejects_unknown_reserved_paths(api_harness):
    response = api_harness["client"].get("/api/private")

    assert response.status_code == 404
