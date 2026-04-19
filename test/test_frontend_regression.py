from __future__ import annotations

import re
from pathlib import Path

import pytest

import app.main as main_module


ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT_DIR / "frontend" / "src"


def read_frontend(path: str) -> str:
    return (FRONTEND_DIR / path).read_text(encoding="utf-8")


def extract_backend_routes() -> set[str]:
    return {
        route.path
        for route in main_module.app.routes
        if hasattr(route, "path")
    }


def normalize_frontend_path(path: str) -> str:
    if path.startswith("/tools/"):
        return f"/api/v1{path}"
    return f"/api/v1{path}"


def extract_request_calls(source: str) -> list[tuple[str, str]]:
    pattern = re.compile(r"(request|longTaskRequest)\.(get|post|delete)\(\s*([`'])(.+?)\3", re.DOTALL)
    return [(client, path) for client, _, _, path in pattern.findall(source)]


def path_template_to_regex(path: str) -> re.Pattern[str]:
    normalized = re.sub(r"\$\{[^}]+\}", "__PARAM__", path)
    escaped = re.escape(normalized).replace("__PARAM__", r"[^/]+")
    return re.compile(f"^{escaped}$")


def test_frontend_api_paths_match_fastapi_routes():
    backend_routes = extract_backend_routes()
    api_files = [
        "modules/market/api.ts",
        "modules/tools/api.ts",
        "modules/backtest/api.ts",
        "modules/factors/api.ts",
    ]

    for file_path in api_files:
        for _, frontend_path in extract_request_calls(read_frontend(file_path)):
            route_pattern = path_template_to_regex(normalize_frontend_path(frontend_path))
            assert any(route_pattern.match(route) for route in backend_routes), f"{file_path} -> {frontend_path} has no backend route"


@pytest.mark.parametrize(
    ("file_path", "endpoint"),
    [
        ("modules/backtest/api.ts", "/backtest/start"),
        ("modules/factors/api.ts", "/factor-research/analyze"),
        ("modules/factors/api.ts", "/factor-research/runs/${runId}/backtest"),
        ("modules/factors/api.ts", "/factor-research/runs/${runId}/paper"),
    ],
)
def test_frontend_long_tasks_use_dedicated_client(file_path: str, endpoint: str):
    source = read_frontend(file_path)
    assert f"longTaskRequest.post('{endpoint}'" in source or f"longTaskRequest.post(`{endpoint}`" in source


def test_page_snapshot_registry_and_helpers_are_stable():
    source = read_frontend("composables/pageSnapshot.ts")

    assert "const PAGE_SNAPSHOT_PREFIX = 'heimdall_page_snapshot:'" in source
    for key in ["dca", "compare", "factorResearch", "halving", "cryptoIndex", "backtest", "backtestEditor"]:
        assert re.search(rf"\b{key}:", source), key
    assert "readStringArray" in source
    assert "readEnum" in source
    assert "bindPageSnapshot" in source
    assert "{ deep: true, immediate: true }" in source


def test_generated_frontend_contracts_include_route_models():
    backtest_types = read_frontend("types/backtest.ts")
    factor_types = read_frontend("types/factor.ts")
    market_types = read_frontend("types/market.ts")
    market_frontend_types = read_frontend("types/market-frontend.ts")

    assert "interface BacktestDeleteResponse" in backtest_types
    assert "interface FactorResearchRunListItemResponse" in factor_types
    assert "interface MarketHistoryResponse" in market_types
    assert "interface MarketHistoryBatchResponse" in market_types
    assert "interface OhlcvPointResponse" in market_types
    assert "OHLCVRaw" not in market_frontend_types
    assert "BatchFullHistoryResponse" not in market_frontend_types


def test_market_store_cache_contract_is_stable():
    source = read_frontend("modules/market/store.ts")

    assert "heimdall_market_cache" not in source
    assert "localStorage" not in source
    assert "sessionStorage" not in source
    assert "_readKlineSlice" in source
    assert "cachedData.length >= limit" in source
    assert "return this._readKlineSlice(cachedData, limit)" in source
    assert "10000" in source
    assert "300000" in source
    assert "60000" in source
    assert "marketApi.getLatestKlines" in source
    assert "marketApi.getIndicators" in source
    assert "Extreme Greed" in source


def test_symbol_search_supports_usd_equivalent_cash_assets():
    catalog_source = read_frontend("modules/market/symbolCatalog.ts")
    generated_catalog_source = read_frontend("modules/market/generatedSymbolCatalog.ts")
    portfolio_source = read_frontend("views/tools/PortfolioBalance.vue")
    shared_source = read_frontend("modules/tools/portfolioBalance/shared.ts")

    assert "generatedSymbolCatalog" in catalog_source
    for symbol in ["USD", "USDT", "USDC"]:
        assert symbol in generated_catalog_source

    assert '"asset_class": "cash"' in generated_catalog_source
    assert "USD_EQUIVALENT_SYMBOLS" in shared_source
    assert "['crypto', 'index', 'cash']" in portfolio_source


def test_portfolio_backtest_history_uses_page_cache():
    source = read_frontend("modules/tools/portfolioBalance/data.ts")

    assert "portfolioHistoryCache" in source
    assert "portfolioHistoryMapCache" in source
    assert "loadIndexHistory(item.marketSymbol, startText)" in source
    assert "loadCryptoHistoryMap(" in source


def test_market_history_api_requests_are_memoized():
    source = read_frontend("modules/market/api.ts")

    assert "historyResponseCache" in source
    for endpoint in [
        "full_history",
        "full_history_batch",
        "indexes_history",
        "indexes_pricing_history",
    ]:
        assert endpoint in source


def test_backtest_and_factor_formatting_entry_points_are_present():
    backtest_source = read_frontend("modules/backtest/useBacktestRunFormatting.ts")
    factor_source = read_frontend("modules/factors/useFactorResearchFormatting.ts")

    for token in [
        "latestRunsByVersion",
        "versionCompareOptions",
        "toggleCompareRun",
        "toggleVersionCompare",
        "paper_live",
        "compareRunLabel",
    ]:
        assert token in backtest_source

    for token in [
        "factorChipClass",
        "categoryChipClass",
        "scoreClass",
        "correlationClass",
        "formatPct",
        "formatNumber",
        "formatDate",
    ]:
        assert token in factor_source


def test_backtest_detail_history_panel_exposes_delete_action():
    source = read_frontend("modules/backtest/useBacktestDetailPage.ts")

    assert "const deleteRun = async (runId: number, mode: BacktestRunMode) => {" in source
    assert "await runs.deleteRun(runId, mode)" in source
    assert "deleteRun," in source
