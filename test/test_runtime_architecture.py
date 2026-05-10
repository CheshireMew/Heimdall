from __future__ import annotations

import ast
from collections import defaultdict
from pathlib import Path

import pytest

from app.runtime_builder import validate_runtime_services
from app.runtime import AppRuntimeServices
from app.runtime_refs import (
    BACKTEST_FREQTRADE_SERVICE,
    BACKTEST_RUN_MUTATION_SERVICE,
    BACKTEST_PAPER_RUN_MANAGER,
    BACKTEST_QUERY_SERVICE,
    BACKTEST_REPORT_BUILDER,
    BACKTEST_RUN_REPOSITORY,
    BACKTEST_RUN_SERVICE,
    BACKTEST_STRATEGY_DEFINITION_STORE,
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
    MARKET_DLI_CACHE,
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


def test_infra_persistence_does_not_depend_on_services():
    offenders = [
        f"{path.relative_to(ROOT_DIR).as_posix()} -> {module}"
        for path in _python_files(APP_DIR / "infra" / "persistence")
        for module in _import_modules(path)
        if module == "app.services" or module.startswith("app.services.")
    ]
    assert offenders == []


def test_infra_persistence_does_not_assemble_api_dtos():
    offenders = [
        f"{path.relative_to(ROOT_DIR).as_posix()} -> {module}"
        for path in _python_files(APP_DIR / "infra" / "persistence")
        for module in _import_modules(path)
        if module == "app.contracts.dto" or module.startswith("app.contracts.dto.")
    ]
    assert offenders == []


def test_backtest_use_cases_live_in_application_boundary_only():
    legacy_files = [
        APP_DIR / "services" / "backtest" / "command_service.py",
        APP_DIR / "services" / "backtest" / "query_service.py",
        APP_DIR / "services" / "backtest" / "strategy_evolution_service.py",
    ]
    assert [path.relative_to(ROOT_DIR).as_posix() for path in legacy_files if path.exists()] == []

    legacy_modules = (
        "app.services.backtest.command_service",
        "app.services.backtest.query_service",
        "app.services.backtest.strategy_evolution_service",
    )
    offenders = [
        f"{path.relative_to(ROOT_DIR).as_posix()} -> {module}"
        for root in (APP_DIR, ROOT_DIR / "test", ROOT_DIR / "scripts")
        for path in _python_files(root)
        for module in _import_modules(path)
        if any(module == legacy or module.startswith(f"{legacy}.") for legacy in legacy_modules)
    ]
    assert offenders == []


def test_paper_run_mutation_service_only_persists_final_payloads():
    source = (APP_DIR / "infra" / "persistence" / "backtest" / "run_mutation_service.py").read_text(encoding="utf-8")

    for removed_helper in [
        "replace_paper_snapshot",
        "persist_factor_paper_increment",
        "mark_paper_stopped",
        "update_paper_metadata",
        "report_builder",
        "execution_core",
    ]:
        assert removed_helper not in source


def test_domain_does_not_depend_on_infra_application_or_services():
    forbidden_prefixes = ("app.infra", "app.application", "app.services", "app.contracts.dto")
    offenders = [
        f"{path.relative_to(ROOT_DIR).as_posix()} -> {module}"
        for path in _python_files(APP_DIR / "domain")
        for module in _import_modules(path)
        if any(module == prefix or module.startswith(f"{prefix}.") for prefix in forbidden_prefixes)
    ]
    assert offenders == []


def test_backtest_domain_contracts_have_no_dto_shadow_source():
    moved_contracts = {
        "strategy_contract.py": "strategy.py",
        "backtest_result.py": "backtest_result.py",
        "json_types.py": "json_types.py",
    }
    for old_name, new_name in moved_contracts.items():
        assert not (APP_DIR / "contracts" / "dto" / old_name).exists()
        assert (APP_DIR / "contracts" / new_name).exists()

    legacy_modules = (
        "app.contracts.dto.strategy_contract",
        "app.contracts.dto.backtest_result",
        "app.contracts.dto.json_types",
    )
    offenders = [
        f"{path.relative_to(ROOT_DIR).as_posix()} -> {module}"
        for root in (APP_DIR, ROOT_DIR / "test", ROOT_DIR / "scripts")
        for path in _python_files(root)
        for module in _import_modules(path)
        if any(module == legacy or module.startswith(f"{legacy}.") for legacy in legacy_modules)
    ]
    assert offenders == []


def test_backtest_domain_and_services_do_not_depend_on_api_dtos():
    scanned_roots = (APP_DIR / "domain" / "backtest", APP_DIR / "services" / "backtest")
    offenders = [
        f"{path.relative_to(ROOT_DIR).as_posix()} -> {module}"
        for root in scanned_roots
        for path in _python_files(root)
        for module in _import_modules(path)
        if module == "app.contracts.dto" or module.startswith("app.contracts.dto.")
    ]
    assert offenders == []


def test_services_do_not_assemble_api_dtos():
    offenders = [
        f"{path.relative_to(ROOT_DIR).as_posix()} -> {module}"
        for path in _python_files(APP_DIR / "services")
        for module in _import_modules(path)
        if module == "app.contracts.dto" or module.startswith("app.contracts.dto.")
    ]
    assert offenders == []


def test_backtest_run_metadata_has_no_wide_response_model():
    removed_symbol = "BacktestRunMetadataResponse"
    offenders = [
        path.relative_to(ROOT_DIR).as_posix()
        for root in (APP_DIR, ROOT_DIR / "test", ROOT_DIR / "scripts")
        for path in _python_files(root)
        if path != Path(__file__).resolve()
        and removed_symbol in path.read_text(encoding="utf-8-sig")
    ]
    assert offenders == []


def test_application_does_not_open_orm_boundary_directly():
    offenders = [
        path.relative_to(ROOT_DIR).as_posix()
        for path in _python_files(APP_DIR / "application")
        if "session_scope(" in path.read_text(encoding="utf-8-sig")
        or any(
            module == "app.infra.db.schema" or module.startswith("app.infra.db.schema.")
            for module in _import_modules(path)
        )
    ]
    assert offenders == []


def test_application_boundary_uses_ports_instead_of_concrete_infra_or_services():
    forbidden_prefixes = ("app.infra.db", "app.infra.persistence", "app.services")
    offenders = [
        f"{path.relative_to(ROOT_DIR).as_posix()} -> {module}"
        for path in _python_files(APP_DIR / "application")
        for module in _import_modules(path)
        if any(module == prefix or module.startswith(f"{prefix}.") for prefix in forbidden_prefixes)
    ]
    assert offenders == []


def test_backtest_run_lifecycle_status_has_contract_source_only():
    lifecycle_source = (APP_DIR / "infra" / "persistence" / "backtest" / "run_lifecycle.py").read_text(encoding="utf-8")
    contract_source = (APP_DIR / "contracts" / "backtest_run.py").read_text(encoding="utf-8")

    for symbol in ["RUN_STATUS_RUNNING", "RUN_STATUS_COMPLETED", "RUN_STATUS_FAILED", "RUN_STATUS_STOPPED"]:
        assert f"{symbol} =" not in lifecycle_source
        assert f"{symbol} =" in contract_source


def test_runtime_role_controls_registered_api_surface():
    from app.main import create_app

    background_paths = {getattr(route, "path", "") for route in create_app("background").routes}
    api_paths = {getattr(route, "path", "") for route in create_app("api").routes}

    assert "/health" in background_paths
    assert not any(path.startswith("/api/v1") for path in background_paths)
    assert "/api/v1/status" in api_paths


def test_frontend_generated_contracts_are_current():
    from scripts import generate_frontend_contracts as generator

    grouped_models = defaultdict(list)
    grouped_query_params = defaultdict(list)
    for contract in generator.collect_route_contract_models():
        grouped_models[contract.target_file].append(contract.model)
    for contract in generator.collect_route_query_param_contracts():
        grouped_query_params[contract.target_file].append(contract)

    changed = []
    for filename in generator.TARGET_FILES:
        expected = generator.render_file(
            grouped_models.get(filename, []),
            grouped_query_params.get(filename, []),
        )
        actual = (generator.FRONTEND_TYPES_DIR / filename).read_text(encoding="utf-8")
        if actual != expected:
            changed.append(str((generator.FRONTEND_TYPES_DIR / filename).relative_to(ROOT_DIR)))
    expected_routes = generator.render_api_routes()
    actual_routes = (generator.FRONTEND_API_DIR / "routes.ts").read_text(encoding="utf-8")
    if actual_routes != expected_routes:
        changed.append(str((generator.FRONTEND_API_DIR / "routes.ts").relative_to(ROOT_DIR)))

    assert changed == []


def make_background_runtime_services() -> AppRuntimeServices:
    return AppRuntimeServices.from_entries({
        INFRA_EXCHANGE_GATEWAY: object(),
        INFRA_DATABASE_RUNTIME: object(),
        INFRA_KLINE_STORE: object(),
        INFRA_CACHE_SERVICE: object(),
        MARKET_MARKET_DATA_SERVICE: object(),
        MARKET_INDICATOR_REPOSITORY: object(),
        MARKET_DLI_CACHE: object(),
        MARKET_FUNDING_RATE_STORE: object(),
        MARKET_BINANCE_MARKET_SNAPSHOT: object(),
        MARKET_BINANCE_MARKET_RESEARCH_STORE: object(),
        MARKET_BINANCE_MARKET_INTEL: object(),
        BACKTEST_RUN_REPOSITORY: object(),
        BACKTEST_RUN_MUTATION_SERVICE: object(),
        BACKTEST_FREQTRADE_SERVICE: object(),
        BACKTEST_STRATEGY_DEFINITION_STORE: object(),
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
        MARKET_DLI_CACHE: object(),
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
        BACKTEST_RUN_MUTATION_SERVICE: object(),
        BACKTEST_FREQTRADE_SERVICE: object(),
        BACKTEST_RUN_SERVICE: object(),
        BACKTEST_STRATEGY_DEFINITION_STORE: object(),
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
