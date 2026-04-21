from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


RuntimeRole = Literal["all", "api", "background"]
RuntimeTarget = Literal["api", "background"]


RUNTIME_ROLE_TARGETS: dict[RuntimeRole, tuple[RuntimeTarget, ...]] = {
    "all": ("api", "background"),
    "api": ("api",),
    "background": ("background",),
}


def runtime_role_targets(role: RuntimeRole) -> tuple[RuntimeTarget, ...]:
    return RUNTIME_ROLE_TARGETS[role]


def runtime_role_has_target(role: RuntimeRole, target: RuntimeTarget) -> bool:
    return target in runtime_role_targets(role)


@dataclass(slots=True)
class InfraRuntime:
    exchange_gateway: Any | None = None
    database_runtime: Any | None = None
    kline_store: Any | None = None
    cache_service: Any | None = None


@dataclass(slots=True)
class MarketRuntime:
    market_data_service: Any | None = None
    realtime_service: Any | None = None
    market_indicator_repository: Any | None = None
    indicator_service: Any | None = None
    history_service: Any | None = None
    funding_rate_store: Any | None = None
    funding_rate_service: Any | None = None
    funding_rate_app_service: Any | None = None
    crypto_index_service: Any | None = None
    market_query_app_service: Any | None = None
    market_insight_app_service: Any | None = None
    market_websocket_service: Any | None = None
    index_data_service: Any | None = None
    binance_market_snapshot: Any | None = None
    binance_market_intel: Any | None = None
    binance_web3_service: Any | None = None


@dataclass(slots=True)
class ToolsRuntime:
    sentiment_api_client: Any | None = None
    sentiment_repository: Any | None = None
    sentiment_service: Any | None = None
    dca_service: Any | None = None
    pair_compare_service: Any | None = None
    tools_app_service: Any | None = None


@dataclass(slots=True)
class BacktestRuntime:
    backtest_run_repository: Any | None = None
    freqtrade_backtest_service: Any | None = None
    backtest_run_service: Any | None = None
    strategy_query_service: Any | None = None
    strategy_write_service: Any | None = None
    freqtrade_report_builder: Any | None = None
    paper_run_manager: Any | None = None
    backtest_command_service: Any | None = None
    backtest_query_service: Any | None = None


@dataclass(slots=True)
class FactorRuntime:
    factor_research_repository: Any | None = None
    factor_research_service: Any | None = None
    factor_execution_service: Any | None = None
    factor_signal_execution_core: Any | None = None
    factor_paper_persistence_service: Any | None = None
    factor_paper_run_manager: Any | None = None


@dataclass(slots=True)
class SystemRuntime:
    currency_rate_service: Any | None = None
    market_scheduler_runtime: Any | None = None


@dataclass(slots=True)
class AppRuntimeServices:
    infra: InfraRuntime
    market: MarketRuntime
    tools: ToolsRuntime
    backtest: BacktestRuntime
    factors: FactorRuntime
    system: SystemRuntime

    @classmethod
    def empty(cls) -> AppRuntimeServices:
        return cls(
            infra=InfraRuntime(),
            market=MarketRuntime(),
            tools=ToolsRuntime(),
            backtest=BacktestRuntime(),
            factors=FactorRuntime(),
            system=SystemRuntime(),
        )

    def _section(self, section_name: str):
        try:
            return getattr(self, section_name)
        except AttributeError as exc:
            raise RuntimeError(f"Unknown runtime section: {section_name}") from exc

    def get_service(self, ref) -> Any | None:
        section = self._section(ref.section)
        if not hasattr(section, ref.name):
            raise RuntimeError(f"Unknown runtime service: {ref.key}")
        return getattr(section, ref.name)

    def set_service(self, ref, service: Any) -> None:
        section = self._section(ref.section)
        if not hasattr(section, ref.name):
            raise RuntimeError(f"Unknown runtime service: {ref.key}")
        setattr(section, ref.name, service)

    def require_service(self, ref) -> Any:
        service = self.get_service(ref)
        if service is None:
            raise RuntimeError(f"Runtime service is not initialized: {ref.key}")
        return service

    def missing_required_services(self, role: RuntimeRole = "all") -> list[str]:
        from app.runtime_graph import active_service_definitions

        missing: list[str] = []
        for definition in active_service_definitions(role):
            if self.get_service(definition.ref) is None:
                missing.append(definition.ref.key)
        return missing

    def validate_required_services(self, role: RuntimeRole = "all") -> None:
        missing = self.missing_required_services(role)
        if missing:
            raise RuntimeError(f"Runtime services missing: {', '.join(missing)}")
