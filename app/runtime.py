from __future__ import annotations

from dataclasses import dataclass, fields
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


RUNTIME_SERVICE_GRAPH: dict[RuntimeTarget, dict[str, tuple[str, ...]]] = {
    "api": {
        "infra": ("exchange_gateway", "database_runtime", "kline_store", "cache_service"),
        "market": (
            "market_data_service",
            "realtime_service",
            "market_indicator_repository",
            "indicator_service",
            "history_service",
            "funding_rate_store",
            "funding_rate_service",
            "funding_rate_app_service",
            "crypto_index_service",
            "market_query_app_service",
            "market_insight_app_service",
            "market_websocket_service",
            "index_data_service",
            "binance_market_intel",
            "binance_web3_service",
        ),
        "tools": (
            "sentiment_api_client",
            "sentiment_repository",
            "sentiment_service",
            "dca_service",
            "pair_compare_service",
            "tools_app_service",
        ),
        "backtest": (
            "backtest_run_repository",
            "freqtrade_backtest_service",
            "backtest_run_service",
            "strategy_query_service",
            "strategy_write_service",
            "freqtrade_report_builder",
            "paper_run_manager",
            "backtest_command_service",
            "backtest_query_service",
        ),
        "factors": (
            "factor_research_repository",
            "factor_research_service",
            "factor_execution_service",
            "factor_signal_execution_core",
            "factor_paper_persistence_service",
            "factor_paper_run_manager",
        ),
        "system": ("currency_rate_service",),
    },
    "background": {
        "infra": ("database_runtime", "cache_service"),
        "market": (
            "market_data_service",
            "market_indicator_repository",
            "binance_market_snapshot",
            "binance_market_intel",
        ),
        "backtest": (
            "backtest_run_repository",
            "freqtrade_backtest_service",
            "strategy_query_service",
            "freqtrade_report_builder",
            "paper_run_manager",
        ),
        "factors": (
            "factor_research_repository",
            "factor_research_service",
            "factor_signal_execution_core",
            "factor_paper_persistence_service",
            "factor_paper_run_manager",
        ),
        "system": ("market_scheduler_runtime",),
    },
}


def runtime_role_targets(role: RuntimeRole) -> tuple[RuntimeTarget, ...]:
    return RUNTIME_ROLE_TARGETS[role]


def runtime_role_has_target(role: RuntimeRole, target: RuntimeTarget) -> bool:
    return target in runtime_role_targets(role)


def required_runtime_services(role: RuntimeRole) -> dict[str, tuple[str, ...]]:
    required: dict[str, list[str]] = {}
    for target in runtime_role_targets(role):
        for section_name, service_names in RUNTIME_SERVICE_GRAPH[target].items():
            section_required = required.setdefault(section_name, [])
            for service_name in service_names:
                if service_name not in section_required:
                    section_required.append(service_name)
    return {
        section_name: tuple(service_names)
        for section_name, service_names in required.items()
    }


@dataclass(slots=True)
class RuntimeSection:
    pass


@dataclass(slots=True)
class InfraRuntime(RuntimeSection):
    exchange_gateway: ExchangeGateway | None = None
    database_runtime: DatabaseRuntime | None = None
    kline_store: KlineStore | None = None
    cache_service: RedisService | None = None


@dataclass(slots=True)
class MarketRuntime(RuntimeSection):
    market_data_service: MarketDataService | None = None
    realtime_service: RealtimeService | None = None
    market_indicator_repository: MarketIndicatorRepository | None = None
    indicator_service: IndicatorService | None = None
    history_service: HistoryService | None = None
    funding_rate_store: FundingRateStore | None = None
    funding_rate_service: FundingRateService | None = None
    funding_rate_app_service: FundingRateAppService | None = None
    crypto_index_service: CryptoIndexService | None = None
    market_query_app_service: MarketQueryAppService | None = None
    market_insight_app_service: MarketInsightAppService | None = None
    market_websocket_service: MarketWebSocketService | None = None
    index_data_service: IndexDataService | None = None
    binance_market_snapshot: BinanceMarketSnapshotService | None = None
    binance_market_intel: BinanceMarketIntelService | None = None
    binance_web3_service: BinanceWeb3Service | None = None


@dataclass(slots=True)
class ToolsRuntime(RuntimeSection):
    sentiment_api_client: SentimentApiClient | None = None
    sentiment_repository: SentimentRepository | None = None
    sentiment_service: SentimentService | None = None
    dca_service: DCAService | None = None
    pair_compare_service: PairCompareService | None = None
    tools_app_service: ToolsAppService | None = None


@dataclass(slots=True)
class BacktestRuntime(RuntimeSection):
    backtest_run_repository: BacktestRunRepository | None = None
    freqtrade_backtest_service: FreqtradeBacktestService | None = None
    backtest_run_service: BacktestRunService | None = None
    strategy_query_service: StrategyQueryService | None = None
    strategy_write_service: StrategyWriteService | None = None
    freqtrade_report_builder: FreqtradeReportBuilder | None = None
    paper_run_manager: PaperRunManager | None = None
    backtest_command_service: BacktestCommandService | None = None
    backtest_query_service: BacktestQueryService | None = None


@dataclass(slots=True)
class FactorRuntime(RuntimeSection):
    factor_research_repository: FactorResearchRepository | None = None
    factor_research_service: FactorResearchService | None = None
    factor_execution_service: FactorExecutionService | None = None
    factor_signal_execution_core: FactorSignalExecutionCore | None = None
    factor_paper_persistence_service: FactorPaperPersistenceService | None = None
    factor_paper_run_manager: FactorPaperRunManager | None = None


@dataclass(slots=True)
class SystemRuntime(RuntimeSection):
    currency_rate_service: CurrencyRateService | None = None
    market_scheduler_runtime: MarketSchedulerRuntime | None = None


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
