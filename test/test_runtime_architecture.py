from __future__ import annotations

import ast
from pathlib import Path

import pytest

from app.runtime_builder import validate_runtime_services
from app.runtime import AppRuntimeServices
from app.runtime_refs import (
    BACKTEST_FREQTRADE_SERVICE,
    BACKTEST_PAPER_RUN_MANAGER,
    BACKTEST_QUERY_SERVICE,
    BACKTEST_REPORT_BUILDER,
    BACKTEST_RUN_REPOSITORY,
    BACKTEST_RUN_SERVICE,
    BACKTEST_STRATEGY_QUERY_SERVICE,
    BACKTEST_STRATEGY_WRITE_SERVICE,
    BACKTEST_COMMAND_SERVICE,
    FACTORS_EXECUTION_SERVICE,
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
    MARKET_BINANCE_WEB3_SERVICE,
    MARKET_CRYPTO_INDEX_SERVICE,
    MARKET_FUNDING_RATE_APP_SERVICE,
    MARKET_FUNDING_RATE_SERVICE,
    MARKET_FUNDING_RATE_STORE,
    MARKET_INDEX_DATA_SERVICE,
    MARKET_INDICATOR_REPOSITORY,
    MARKET_INDICATOR_SERVICE,
    MARKET_INSIGHT_APP_SERVICE,
    MARKET_MARKET_DATA_SERVICE,
    MARKET_QUERY_APP_SERVICE,
    MARKET_REALTIME_SERVICE,
    MARKET_WEBSOCKET_SERVICE,
    SYSTEM_CURRENCY_RATE_SERVICE,
    SYSTEM_FRED_API_CONFIG_SERVICE,
    SYSTEM_LLM_CONFIG_SERVICE,
    SYSTEM_MARKET_SCHEDULER_RUNTIME,
    TOOLS_DCA_SERVICE,
    TOOLS_PAIR_COMPARE_SERVICE,
    TOOLS_SENTIMENT_API_CLIENT,
    TOOLS_SENTIMENT_REPOSITORY,
    TOOLS_SENTIMENT_SERVICE,
    TOOLS_TOOLS_APP_SERVICE,
)


ROOT_DIR = Path(__file__).resolve().parents[1]
APP_DIR = ROOT_DIR / "app"


def _python_files(root: Path) -> list[Path]:
    return [
        path
        for path in root.rglob("*.py")
        if "__pycache__" not in path.parts
    ]


def _import_modules(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    return modules


def test_backend_contracts_have_single_source():
    assert not (APP_DIR / "schemas").exists()
    assert not (APP_DIR / "contracts" / "api").exists()
    scanned_roots = (APP_DIR, ROOT_DIR / "test", ROOT_DIR / "scripts")
    offenders = [
        path.relative_to(ROOT_DIR).as_posix()
        for root in scanned_roots
        for path in _python_files(root)
        for module in _import_modules(path)
        if module == "app.schemas"
        or module.startswith("app.schemas.")
        or module == "app.contracts.api"
        or module.startswith("app.contracts.api.")
    ]
    assert offenders == []


def test_services_do_not_depend_on_orm_schema_or_legacy_persistence_paths():
    legacy_prefixes = (
        "app.services.backtest.run_repository",
        "app.services.backtest.result_store",
        "app.services.backtest.serializers",
        "app.services.backtest.run_lifecycle",
        "app.services.backtest.strategy_catalog",
        "app.services.backtest.strategy_query_service",
        "app.services.backtest.strategy_write_service",
        "app.services.backtest.paper_manager",
        "app.services.backtest.run_service",
        "app.services.factors.repository",
        "app.services.factors.paper_persistence_service",
        "app.services.factors.paper_manager",
        "app.services.factors.execution",
        "app.services.market.kline_store",
        "app.services.market.funding_rate_store",
        "app.services.market.indicator_repository",
        "app.services.market.binance_market_research_store",
        "app.services.sentiment_repository",
        "app.services.data_retention",
        "app.services.paper_run_lifecycle",
        "app.services.market_cron",
    )
    forbidden_prefixes = ("app.infra.db.schema", *legacy_prefixes)
    offenders = [
        f"{path.relative_to(ROOT_DIR).as_posix()} -> {module}"
        for path in _python_files(APP_DIR / "services")
        for module in _import_modules(path)
        if any(module == prefix or module.startswith(f"{prefix}.") for prefix in forbidden_prefixes)
    ]
    assert offenders == []


def make_background_runtime_services() -> AppRuntimeServices:
    return AppRuntimeServices.from_entries({
        INFRA_EXCHANGE_GATEWAY: object(),
        INFRA_DATABASE_RUNTIME: object(),
        INFRA_KLINE_STORE: object(),
        INFRA_CACHE_SERVICE: object(),
        MARKET_MARKET_DATA_SERVICE: object(),
        MARKET_INDICATOR_REPOSITORY: object(),
        MARKET_FUNDING_RATE_STORE: object(),
        MARKET_BINANCE_MARKET_SNAPSHOT: object(),
        MARKET_BINANCE_MARKET_RESEARCH_STORE: object(),
        MARKET_BINANCE_MARKET_INTEL: object(),
        BACKTEST_RUN_REPOSITORY: object(),
        BACKTEST_FREQTRADE_SERVICE: object(),
        BACKTEST_STRATEGY_QUERY_SERVICE: object(),
        BACKTEST_REPORT_BUILDER: object(),
        BACKTEST_PAPER_RUN_MANAGER: object(),
        FACTORS_RESEARCH_REPOSITORY: object(),
        FACTORS_RESEARCH_SERVICE: object(),
        FACTORS_SIGNAL_EXECUTION_CORE: object(),
        FACTORS_PAPER_PERSISTENCE_SERVICE: object(),
        FACTORS_PAPER_RUN_MANAGER: object(),
        SYSTEM_MARKET_SCHEDULER_RUNTIME: object(),
    })


def make_api_runtime_services() -> AppRuntimeServices:
    return AppRuntimeServices.from_entries({
        INFRA_EXCHANGE_GATEWAY: object(),
        INFRA_DATABASE_RUNTIME: object(),
        INFRA_KLINE_STORE: object(),
        INFRA_CACHE_SERVICE: object(),
        MARKET_MARKET_DATA_SERVICE: object(),
        MARKET_REALTIME_SERVICE: object(),
        MARKET_INDICATOR_REPOSITORY: object(),
        MARKET_INDICATOR_SERVICE: object(),
        MARKET_FUNDING_RATE_STORE: object(),
        MARKET_FUNDING_RATE_SERVICE: object(),
        MARKET_FUNDING_RATE_APP_SERVICE: object(),
        MARKET_CRYPTO_INDEX_SERVICE: object(),
        MARKET_QUERY_APP_SERVICE: object(),
        MARKET_INSIGHT_APP_SERVICE: object(),
        MARKET_WEBSOCKET_SERVICE: object(),
        MARKET_INDEX_DATA_SERVICE: object(),
        MARKET_BINANCE_MARKET_SNAPSHOT: object(),
        MARKET_BINANCE_MARKET_RESEARCH_STORE: object(),
        MARKET_BINANCE_MARKET_INTEL: object(),
        MARKET_BINANCE_WEB3_SERVICE: object(),
        TOOLS_SENTIMENT_API_CLIENT: object(),
        TOOLS_SENTIMENT_REPOSITORY: object(),
        TOOLS_SENTIMENT_SERVICE: object(),
        TOOLS_DCA_SERVICE: object(),
        TOOLS_PAIR_COMPARE_SERVICE: object(),
        TOOLS_TOOLS_APP_SERVICE: object(),
        BACKTEST_RUN_REPOSITORY: object(),
        BACKTEST_FREQTRADE_SERVICE: object(),
        BACKTEST_RUN_SERVICE: object(),
        BACKTEST_STRATEGY_QUERY_SERVICE: object(),
        BACKTEST_STRATEGY_WRITE_SERVICE: object(),
        BACKTEST_REPORT_BUILDER: object(),
        BACKTEST_PAPER_RUN_MANAGER: object(),
        BACKTEST_COMMAND_SERVICE: object(),
        BACKTEST_QUERY_SERVICE: object(),
        FACTORS_RESEARCH_REPOSITORY: object(),
        FACTORS_RESEARCH_SERVICE: object(),
        FACTORS_EXECUTION_SERVICE: object(),
        FACTORS_SIGNAL_EXECUTION_CORE: object(),
        FACTORS_PAPER_PERSISTENCE_SERVICE: object(),
        FACTORS_PAPER_RUN_MANAGER: object(),
        SYSTEM_CURRENCY_RATE_SERVICE: object(),
        SYSTEM_LLM_CONFIG_SERVICE: object(),
        SYSTEM_FRED_API_CONFIG_SERVICE: object(),
    })


def test_background_role_validation_ignores_api_only_graph():
    services = make_background_runtime_services()

    validate_runtime_services(services, "background")
    with pytest.raises(RuntimeError, match="market.realtime_service"):
        validate_runtime_services(services, "api")


def test_api_role_validation_ignores_background_only_graph():
    services = make_api_runtime_services()

    validate_runtime_services(services, "api")
    with pytest.raises(RuntimeError, match="system.market_scheduler_runtime"):
        validate_runtime_services(services, "background")
