from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from app.infra.cache import RedisService
    from app.infra.db import DatabaseRuntime
    from app.services.backtest.command_service import BacktestCommandService
    from app.services.backtest.freqtrade_report_builder import FreqtradeReportBuilder
    from app.services.backtest.freqtrade_service import FreqtradeBacktestService
    from app.services.backtest.paper_manager import PaperRunManager
    from app.services.backtest.query_service import BacktestQueryService
    from app.services.backtest.run_repository import BacktestRunRepository
    from app.services.backtest.run_service import BacktestRunService
    from app.services.backtest.strategy_query_service import StrategyQueryService
    from app.services.backtest.strategy_write_service import StrategyWriteService
    from app.services.currency_service import CurrencyRateService
    from app.services.factors.execution import FactorExecutionService
    from app.services.factors.paper_manager import FactorPaperRunManager
    from app.services.factors.paper_persistence_service import FactorPaperPersistenceService
    from app.services.factors.repository import FactorResearchRepository
    from app.services.factors.service import FactorResearchService
    from app.services.factors.signal_execution_core import FactorSignalExecutionCore
    from app.services.market.binance_market_intel_service import BinanceMarketIntelService
    from app.services.market.binance_market_snapshot_service import BinanceMarketSnapshotService
    from app.services.market.binance_web3_service import BinanceWeb3Service
    from app.services.market.crypto_index_service import CryptoIndexService
    from app.services.market.exchange_gateway import ExchangeGateway
    from app.services.market.funding_rate_app_service import FundingRateAppService
    from app.services.market.funding_rate_service import FundingRateService
    from app.services.market.funding_rate_store import FundingRateStore
    from app.services.market.history_service import HistoryService
    from app.services.market.indicator_repository import MarketIndicatorRepository
    from app.services.market.indicator_service import IndicatorService
    from app.services.market.index_data_service import IndexDataService
    from app.services.market.insight_app_service import MarketInsightAppService
    from app.services.market.kline_store import KlineStore
    from app.services.market.market_data_service import MarketDataService
    from app.services.market.query_app_service import MarketQueryAppService
    from app.services.market.realtime_service import RealtimeService
    from app.services.market.websocket_service import MarketWebSocketService
    from app.services.market_scheduler_runtime import MarketSchedulerRuntime
    from app.services.sentiment_client import SentimentApiClient
    from app.services.sentiment_repository import SentimentRepository
    from app.services.sentiment_service import SentimentService
    from app.services.tools.app_service import ToolsAppService
    from app.services.tools.dca_service import DCAService
    from app.services.tools.pair_compare_service import PairCompareService


RuntimeRole = Literal["all", "api", "background"]
RuntimeTarget = Literal["api", "background"]


RUNTIME_ROLE_TARGETS: dict[RuntimeRole, tuple[RuntimeTarget, ...]] = {
    "all": ("api", "background"),
    "api": ("api",),
    "background": ("background",),
}


def runtime_service(*targets: RuntimeTarget):
    return field(default=None, metadata={"runtime_targets": frozenset(targets)})


def runtime_role_targets(role: RuntimeRole) -> tuple[RuntimeTarget, ...]:
    return RUNTIME_ROLE_TARGETS[role]


def runtime_role_has_target(role: RuntimeRole, target: RuntimeTarget) -> bool:
    return target in runtime_role_targets(role)


def required_runtime_services(role: RuntimeRole) -> dict[str, tuple[str, ...]]:
    role_targets = set(runtime_role_targets(role))
    required: dict[str, list[str]] = {}
    for section_name, section_type in RUNTIME_SECTION_TYPES.items():
        section_required = required.setdefault(section_name, [])
        for section_field in fields(section_type):
            targets = set(section_field.metadata.get("runtime_targets", ()))
            if targets & role_targets:
                section_required.append(section_field.name)
    return {
        section_name: tuple(service_names)
        for section_name, service_names in required.items()
        if service_names
    }


@dataclass(slots=True)
class RuntimeSection:
    pass


@dataclass(slots=True)
class InfraRuntime(RuntimeSection):
    exchange_gateway: ExchangeGateway | None = runtime_service("api", "background")
    database_runtime: DatabaseRuntime | None = runtime_service("api", "background")
    kline_store: KlineStore | None = runtime_service("api", "background")
    cache_service: RedisService | None = runtime_service("api", "background")


@dataclass(slots=True)
class MarketRuntime(RuntimeSection):
    market_data_service: MarketDataService | None = runtime_service("api", "background")
    realtime_service: RealtimeService | None = runtime_service("api")
    market_indicator_repository: MarketIndicatorRepository | None = runtime_service("api", "background")
    indicator_service: IndicatorService | None = runtime_service("api")
    history_service: HistoryService | None = runtime_service("api")
    funding_rate_store: FundingRateStore | None = runtime_service("api")
    funding_rate_service: FundingRateService | None = runtime_service("api")
    funding_rate_app_service: FundingRateAppService | None = runtime_service("api")
    crypto_index_service: CryptoIndexService | None = runtime_service("api")
    market_query_app_service: MarketQueryAppService | None = runtime_service("api")
    market_insight_app_service: MarketInsightAppService | None = runtime_service("api")
    market_websocket_service: MarketWebSocketService | None = runtime_service("api")
    index_data_service: IndexDataService | None = runtime_service("api")
    binance_market_snapshot: BinanceMarketSnapshotService | None = runtime_service("background")
    binance_market_intel: BinanceMarketIntelService | None = runtime_service("api", "background")
    binance_web3_service: BinanceWeb3Service | None = runtime_service("api")


@dataclass(slots=True)
class ToolsRuntime(RuntimeSection):
    sentiment_api_client: SentimentApiClient | None = runtime_service("api")
    sentiment_repository: SentimentRepository | None = runtime_service("api")
    sentiment_service: SentimentService | None = runtime_service("api")
    dca_service: DCAService | None = runtime_service("api")
    pair_compare_service: PairCompareService | None = runtime_service("api")
    tools_app_service: ToolsAppService | None = runtime_service("api")


@dataclass(slots=True)
class BacktestRuntime(RuntimeSection):
    backtest_run_repository: BacktestRunRepository | None = runtime_service("api", "background")
    freqtrade_backtest_service: FreqtradeBacktestService | None = runtime_service("api", "background")
    backtest_run_service: BacktestRunService | None = runtime_service("api")
    strategy_query_service: StrategyQueryService | None = runtime_service("api", "background")
    strategy_write_service: StrategyWriteService | None = runtime_service("api")
    freqtrade_report_builder: FreqtradeReportBuilder | None = runtime_service("api", "background")
    paper_run_manager: PaperRunManager | None = runtime_service("api", "background")
    backtest_command_service: BacktestCommandService | None = runtime_service("api")
    backtest_query_service: BacktestQueryService | None = runtime_service("api")


@dataclass(slots=True)
class FactorRuntime(RuntimeSection):
    factor_research_repository: FactorResearchRepository | None = runtime_service("api", "background")
    factor_research_service: FactorResearchService | None = runtime_service("api", "background")
    factor_execution_service: FactorExecutionService | None = runtime_service("api")
    factor_signal_execution_core: FactorSignalExecutionCore | None = runtime_service("api", "background")
    factor_paper_persistence_service: FactorPaperPersistenceService | None = runtime_service("api", "background")
    factor_paper_run_manager: FactorPaperRunManager | None = runtime_service("api", "background")


@dataclass(slots=True)
class SystemRuntime(RuntimeSection):
    currency_rate_service: CurrencyRateService | None = runtime_service("api")
    market_scheduler_runtime: MarketSchedulerRuntime | None = runtime_service("background")


RUNTIME_SECTION_TYPES: dict[str, type[RuntimeSection]] = {
    "infra": InfraRuntime,
    "market": MarketRuntime,
    "tools": ToolsRuntime,
    "backtest": BacktestRuntime,
    "factors": FactorRuntime,
    "system": SystemRuntime,
}


@dataclass(slots=True)
class AppRuntimeServices:
    infra: InfraRuntime
    market: MarketRuntime
    tools: ToolsRuntime
    backtest: BacktestRuntime
    factors: FactorRuntime
    system: SystemRuntime

    def missing_required_services(
        self,
        role: RuntimeRole = "all",
    ) -> list[str]:
        role_map = required_runtime_services(role)
        missing: list[str] = []
        for section_field in fields(self):
            section = getattr(self, section_field.name)
            if not isinstance(section, RuntimeSection):
                continue
            required_fields = role_map.get(section_field.name, ())
            for service_name in required_fields:
                if getattr(section, service_name) is None:
                    missing.append(f"{section_field.name}.{service_name}")
        return missing

    def validate_required_services(
        self,
        role: RuntimeRole = "all",
    ) -> None:
        missing = self.missing_required_services(role)
        if missing:
            raise RuntimeError(f"Runtime services missing: {', '.join(missing)}")
