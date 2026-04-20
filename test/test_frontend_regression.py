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


def extract_api_route_calls(source: str) -> list[str]:
    return re.findall(r"apiRoute\(\s*['\"]([a-z0-9_]+)['\"]", source)


def strip_api_prefix(path: str) -> str:
    return path.removeprefix("/api/v1")


def test_frontend_api_paths_match_fastapi_routes():
    backend_routes = {
        route.name: strip_api_prefix(route.path)
        for route in main_module.app.routes
        if hasattr(route, "path") and getattr(route, "path").startswith("/api/v1")
    }
    generated_routes = read_frontend("api/routes.ts")
    api_files = [
        "modules/market/api.ts",
        "modules/tools/api.ts",
        "modules/backtest/api.ts",
        "modules/factors/api.ts",
        "modules/system/api.ts",
    ]

    used_routes = set()
    for file_path in api_files:
        source = read_frontend(file_path)
        assert not extract_request_calls(source), f"{file_path} still hard-codes request URLs"
        used_routes.update(extract_api_route_calls(source))

    for route_name in used_routes:
        assert route_name in backend_routes, route_name
        assert f"{route_name}: {backend_routes[route_name]!r}".replace("'", '"') in generated_routes


@pytest.mark.parametrize(
    ("file_path", "route_name"),
    [
        ("modules/backtest/api.ts", "start_backtest"),
        ("modules/factors/api.ts", "analyze_factors"),
        ("modules/factors/api.ts", "start_factor_backtest"),
        ("modules/factors/api.ts", "start_factor_paper_run"),
    ],
)
def test_frontend_long_tasks_use_dedicated_client(file_path: str, route_name: str):
    source = read_frontend(file_path)
    assert f"longTaskRequest.post(apiRoute('{route_name}'" in source


def test_page_snapshot_registry_and_helpers_are_stable():
    source = read_frontend("composables/pageSnapshot.ts")

    assert "const PAGE_SNAPSHOT_PREFIX = 'heimdall_page_snapshot:'" in source
    for key in ["dca", "compare", "factorResearch", "halving", "cryptoIndex", "backtest", "backtestEditor"]:
        assert re.search(rf"\b{key}:", source), key
    assert "readStringArray" in source
    assert "readEnum" in source
    assert "createPersistentPageSnapshot" in source
    assert "bind(sources:" in source
    assert "data: normalize(snapshot, fallback)" in source
    assert "{ deep: true, immediate: true }" in source


def test_generated_frontend_contracts_include_route_models():
    backtest_types = read_frontend("types/backtest.ts")
    factor_types = read_frontend("types/factor.ts")
    market_types = read_frontend("types/market.ts")

    assert "interface BacktestDeleteResponse" in backtest_types
    assert "interface FactorResearchRunListItemResponse" in factor_types
    assert "interface MarketHistoryResponse" in market_types
    assert "interface MarketHistoryBatchResponse" in market_types
    assert "interface OhlcvPointResponse" in market_types
    assert "interface GetMarketFullHistoryQueryParams" in market_types
    assert "GetMarketFullHistoryBatchQueryParamsMeta" in market_types
    assert not any(path.name.endswith("-frontend.ts") for path in (FRONTEND_DIR / "types").glob("*.ts"))


def test_frontend_business_code_uses_module_contract_boundaries():
    offenders = []
    for path in FRONTEND_DIR.rglob("*"):
        if path.suffix not in {".ts", ".vue"}:
            continue
        if path.name == "contracts.ts" or path.parent == FRONTEND_DIR / "types":
            continue
        source = path.read_text(encoding="utf-8")
        if "@/types" in source:
            offenders.append(path.relative_to(FRONTEND_DIR).as_posix())

    assert offenders == []


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
    base_catalog_source = read_frontend("modules/market/baseSymbolCatalog.ts")
    portfolio_source = read_frontend("views/tools/PortfolioBalance.vue")
    shared_source = read_frontend("modules/tools/portfolioBalance/shared.ts")
    generator_source = (ROOT_DIR / "scripts" / "generate_frontend_contracts.py").read_text(encoding="utf-8")

    assert "baseSymbolCatalog" in catalog_source
    assert not any(path.name.startswith("generated") and path.name.endswith("Catalog.ts") for path in (FRONTEND_DIR / "modules" / "market").glob("*.ts"))
    for symbol in ["USD", "USDT", "USDC"]:
        assert symbol in base_catalog_source

    assert "list_market_search_items" not in generator_source
    assert "asset_class: 'cash'" in base_catalog_source
    assert "USD_EQUIVALENT_SYMBOLS" in shared_source
    assert "['crypto', 'index', 'cash']" in portfolio_source


def test_portfolio_backtest_history_uses_page_cache():
    source = read_frontend("modules/tools/portfolioBalance/data.ts")

    assert "portfolioHistoryCache" in source
    assert "portfolioHistoryMapCache" in source
    assert "loadIndexHistory(item.marketSymbol, startText)" in source
    assert "loadCryptoHistoryMap(" in source


def test_market_history_api_requests_do_not_keep_a_second_cache():
    source = read_frontend("modules/market/api.ts")

    assert "historyResponseCache" not in source
    for route_name in [
        "get_market_full_history",
        "get_market_full_history_batch",
        "get_index_history",
        "get_index_pricing_history",
    ]:
        assert route_name in source


def test_frontend_navigation_uses_single_manifest():
    app_source = read_frontend("App.vue")
    router_source = read_frontend("router/index.ts")
    navigation_source = read_frontend("app/navigation.ts")

    assert "APP_ROUTE_DEFINITIONS" in navigation_source
    assert "APP_NAV_ITEMS" in navigation_source
    assert "APP_KEEP_ALIVE_ROUTE_NAMES" in navigation_source
    assert "APP_ROUTE_DEFINITIONS.map" in router_source
    assert "APP_NAV_SECTIONS.map" in app_source
    assert "APP_NAV_ITEMS.filter" in app_source


def test_market_frontend_uses_generated_query_contracts():
    market_types = read_frontend("types/market.ts")
    contracts_source = read_frontend("modules/market/contracts.ts")
    api_source = read_frontend("modules/market/api.ts")

    assert "interface GetMarketFullHistoryQueryParams" in market_types
    assert "interface GetMarketFullHistoryBatchQueryParams" in market_types
    assert "export const GetMarketFullHistoryBatchQueryParamsMeta" in market_types
    assert "repeatedKeys" in market_types
    assert "type RealtimeParams = GetRealtimeAnalysisQueryParams" in contracts_source
    assert "type FullHistoryParams = GetMarketFullHistoryQueryParams" in contracts_source
    assert "interface FullHistoryParams" not in contracts_source
    assert "CURRENT_PRICE_BATCH_QUERY_META" in contracts_source
    assert "FULL_HISTORY_BATCH_QUERY_META" in contracts_source
    assert "serializeApiQueryParams" in api_source
    assert "API_QUERY_META" in api_source
    assert "normalizePriceHistoryParams" not in api_source
    assert "serializeBatchFullHistoryParams" not in api_source
    assert "get_current_price_batch" in api_source
    assert "get_market_full_history_batch" in api_source


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
