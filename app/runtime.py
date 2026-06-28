from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, cast

from config import settings

if TYPE_CHECKING:
    from app.infra.cache import RedisService
    from app.infra.db.database import DatabaseRuntime
    from app.infra.persistence.market.binance_market_research_store import BinanceMarketResearchStore
    from app.infra.persistence.market.indicator_repository import MarketIndicatorRepository
    from app.infra.persistence.market.kline_store import KlineStore
    from app.infra.persistence.sentiment_repository import SentimentRepository
    from app.services.currency_service import CurrencyRateService
    from app.services.fred_api_config_service import FredApiConfigService
    from app.services.llm_config_service import LlmConfigService
    from app.services.market.binance_market_intel_service import BinanceMarketIntelService
    from app.services.market.binance_market_snapshot_service import BinanceMarketSnapshotService
    from app.services.market.binance_web3_heat_rank_service import BinanceWeb3HeatRankService
    from app.services.market.binance_web3_rank_gateway import BinanceWeb3RankGateway
    from app.services.market.binance_web3_tokens import BinanceWeb3TokenService
    from app.services.market.dli_cache import DliLiquidityCache
    from app.services.market.exchange_gateway import ExchangeGateway
    from app.services.market.index_data_service import IndexDataService
    from app.services.market.indicator_service import IndicatorService
    from app.services.market.insight_app_service import MarketInsightAppService
    from app.services.market.market_data_service import MarketDataService
    from app.services.market.query_app_service import MarketQueryAppService
    from app.services.market.realtime_service import RealtimeService
    from app.services.market.websocket_service import MarketWebSocketService
    from app.services.market_scheduler_runtime import MarketSchedulerRuntime
    from app.services.sentiment_client import SentimentApiClient
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


def runtime_role_targets(role: RuntimeRole) -> tuple[RuntimeTarget, ...]:
    return RUNTIME_ROLE_TARGETS[role]


def runtime_role_has_target(role: RuntimeRole, target: RuntimeTarget) -> bool:
    return target in runtime_role_targets(role)


@dataclass(slots=True)
class AppRuntimeServices:
    database_runtime: "DatabaseRuntime"
    cache_service: "RedisService"
    exchange_gateway: "ExchangeGateway | None" = None
    kline_store: "KlineStore | None" = None
    market_data_service: "MarketDataService | None" = None
    realtime_service: "RealtimeService | None" = None
    market_indicator_repository: "MarketIndicatorRepository | None" = None
    dli_cache: "DliLiquidityCache | None" = None
    indicator_service: "IndicatorService | None" = None
    market_query_service: "MarketQueryAppService | None" = None
    market_insight_service: "MarketInsightAppService | None" = None
    market_websocket_service: "MarketWebSocketService | None" = None
    index_data_service: "IndexDataService | None" = None
    binance_market_research_store: "BinanceMarketResearchStore | None" = None
    binance_market_intel: "BinanceMarketIntelService | None" = None
    binance_market_snapshot: "BinanceMarketSnapshotService | None" = None
    binance_web3_ranks: "BinanceWeb3RankGateway | None" = None
    binance_web3_heat_ranks: "BinanceWeb3HeatRankService | None" = None
    binance_web3_tokens: "BinanceWeb3TokenService | None" = None
    sentiment_api_client: "SentimentApiClient | None" = None
    sentiment_repository: "SentimentRepository | None" = None
    sentiment_service: "SentimentService | None" = None
    dca_service: "DCAService | None" = None
    pair_compare_service: "PairCompareService | None" = None
    tools_app_service: "ToolsAppService | None" = None
    currency_rate_service: "CurrencyRateService | None" = None
    llm_config_service: "LlmConfigService | None" = None
    fred_api_config_service: "FredApiConfigService | None" = None
    market_scheduler_runtime: "MarketSchedulerRuntime | None" = None

    def require(self, name: str) -> object:
        service = getattr(self, name, None)
        if service is None:
            raise RuntimeError(f"Runtime service is not initialized: {name}")
        return service

    def dispose(self) -> None:
        from app.infra.executor import shutdown_blocking_executors

        self.database_runtime.dispose()
        shutdown_blocking_executors()


API_REQUIRED_SERVICES = (
    "database_runtime",
    "cache_service",
    "exchange_gateway",
    "kline_store",
    "market_data_service",
    "realtime_service",
    "market_indicator_repository",
    "dli_cache",
    "indicator_service",
    "market_query_service",
    "market_insight_service",
    "market_websocket_service",
    "index_data_service",
    "binance_market_research_store",
    "binance_market_intel",
    "binance_market_snapshot",
    "binance_web3_ranks",
    "binance_web3_heat_ranks",
    "binance_web3_tokens",
    "sentiment_api_client",
    "sentiment_repository",
    "sentiment_service",
    "dca_service",
    "pair_compare_service",
    "tools_app_service",
    "currency_rate_service",
    "llm_config_service",
    "fred_api_config_service",
)
BACKGROUND_REQUIRED_SERVICES = (
    "database_runtime",
    "cache_service",
    "market_indicator_repository",
    "dli_cache",
    "market_scheduler_runtime",
)


def _llm_client_factory(llm_config_service):
    from app.infra.llm_client import LLMClient

    return lambda: LLMClient(llm_config=llm_config_service.read_effective_config())


def build_app_runtime_services(role: RuntimeRole | None = None) -> AppRuntimeServices:
    resolved_role = role or settings.APP_RUNTIME_ROLE

    from app.infra.cache import build_cache_service
    from app.infra.db import build_database_runtime

    database_runtime = build_database_runtime(settings)
    cache_service = build_cache_service(settings)
    services = AppRuntimeServices(database_runtime=database_runtime, cache_service=cache_service)

    if runtime_role_has_target(resolved_role, "background") or runtime_role_has_target(resolved_role, "api"):
        from app.infra.persistence.market.indicator_repository import MarketIndicatorRepository
        from app.services.market.dli_cache import DliLiquidityCache

        services.market_indicator_repository = MarketIndicatorRepository(database_runtime=database_runtime)
        services.dli_cache = DliLiquidityCache(cache_service=cache_service)

    if runtime_role_has_target(resolved_role, "api"):
        from app.infra.persistence.market.binance_market_research_store import BinanceMarketResearchStore
        from app.infra.persistence.market.kline_store import KlineStore
        from app.infra.persistence.sentiment_repository import SentimentRepository
        from app.services.currency_service import CurrencyRateService
        from app.services.fred_api_config_service import FredApiConfigService
        from app.services.llm_config_service import LlmConfigService
        from app.services.market.binance_api_support import BinanceApiSupport
        from app.services.market.binance_market_intel_service import BinanceMarketIntelService
        from app.services.market.binance_web3_heat_rank_service import BinanceWeb3HeatRankService
        from app.services.market.binance_web3_rank_gateway import BinanceWeb3RankGateway
        from app.services.market.binance_web3_tokens import BinanceWeb3TokenService
        from app.services.market.exchange_gateway import ExchangeGateway
        from app.services.market.index_data_service import IndexDataService
        from app.services.market.indicator_service import IndicatorService
        from app.services.market.insight_app_service import MarketInsightAppService
        from app.services.market.market_data_service import MarketDataService
        from app.services.market.query_app_service import MarketQueryAppService
        from app.services.market.realtime_service import RealtimeService
        from app.services.market.websocket_service import MarketWebSocketService
        from app.services.sentiment_client import SentimentApiClient
        from app.services.sentiment_service import SentimentService
        from app.services.tools.app_service import ToolsAppService
        from app.services.tools.dca_service import DCAService
        from app.services.tools.pair_compare_service import PairCompareService

        services.exchange_gateway = ExchangeGateway(exchange_id=settings.EXCHANGE_ID)
        services.kline_store = KlineStore(database_runtime=database_runtime)
        services.market_data_service = MarketDataService(
            exchange_gateway=services.exchange_gateway,
            kline_store=services.kline_store,
            cache_service=cache_service,
        )
        services.realtime_service = RealtimeService()
        services.indicator_service = IndicatorService(
            repository=cast("MarketIndicatorRepository", services.require("market_indicator_repository")),
            dli_cache=cast("DliLiquidityCache", services.require("dli_cache")),
        )
        services.currency_rate_service = CurrencyRateService()
        services.llm_config_service = LlmConfigService()
        services.fred_api_config_service = FredApiConfigService()
        services.binance_market_research_store = BinanceMarketResearchStore(database_runtime=database_runtime)
        services.binance_market_intel = BinanceMarketIntelService(
            research_store=services.binance_market_research_store,
            cache_service=cache_service,
        )
        services.binance_market_snapshot = services.binance_market_intel.snapshot_service
        services.market_query_service = MarketQueryAppService(
            market_data_service=services.market_data_service,
            realtime_service=services.realtime_service,
            binance_snapshot_service=services.binance_market_snapshot,
            llm_client_factory=_llm_client_factory(services.llm_config_service),
        )
        services.market_insight_service = MarketInsightAppService(
            indicator_service=services.indicator_service,
            market_query_service=services.market_query_service,
            llm_client_factory=_llm_client_factory(services.llm_config_service),
        )
        services.market_websocket_service = MarketWebSocketService()
        services.index_data_service = IndexDataService(kline_store=services.kline_store)
        services.binance_web3_ranks = BinanceWeb3RankGateway(
            BinanceApiSupport(
                base_url=settings.BINANCE_WEB3_BASE_URL,
                cache_namespace="binance:web3",
                user_agent="binance-web3/2.1 (Skill)",
                cache_service=cache_service,
            )
        )
        services.binance_web3_heat_ranks = BinanceWeb3HeatRankService(services.binance_web3_ranks)
        services.binance_web3_tokens = BinanceWeb3TokenService(
            web3_client=BinanceApiSupport(
                base_url=settings.BINANCE_WEB3_BASE_URL,
                cache_namespace="binance:web3",
                user_agent="binance-web3/2.1 (Skill)",
                cache_service=cache_service,
            ),
            kline_client=BinanceApiSupport(
                base_url="https://dquery.sintral.io",
                cache_namespace="binance:web3:kline",
                user_agent="binance-web3/1.1 (Skill)",
                cache_service=cache_service,
            ),
            kline_store=services.kline_store,
        )
        services.sentiment_api_client = SentimentApiClient(settings.SENTIMENT_API_URL)
        services.sentiment_repository = SentimentRepository(database_runtime=database_runtime)
        services.sentiment_service = SentimentService(
            client=services.sentiment_api_client,
            repository=services.sentiment_repository,
        )
        services.dca_service = DCAService(
            market_data_service=services.market_data_service,
            sentiment_service=services.sentiment_service,
            index_data_service=services.index_data_service,
        )
        services.pair_compare_service = PairCompareService(
            market_data_service=services.market_data_service,
            index_data_service=services.index_data_service,
        )
        services.tools_app_service = ToolsAppService(
            dca_service=services.dca_service,
            pair_compare_service=services.pair_compare_service,
            cache_service=cache_service,
        )

    if runtime_role_has_target(resolved_role, "background"):
        from app.infra.persistence.data_retention import cleanup_old_data
        from app.services.market_scheduler_runtime import MarketSchedulerRuntime

        services.market_scheduler_runtime = MarketSchedulerRuntime(
            indicator_repository=cast("MarketIndicatorRepository", services.require("market_indicator_repository")),
            cleanup_old_data=lambda: cleanup_old_data(database_runtime),
            dli_cache=cast("DliLiquidityCache", services.require("dli_cache")),
        )

    validate_runtime_services(services, resolved_role)
    return services


def missing_required_services(services: AppRuntimeServices, role: RuntimeRole = "all") -> list[str]:
    required = []
    if runtime_role_has_target(role, "api"):
        required.extend(API_REQUIRED_SERVICES)
    if runtime_role_has_target(role, "background"):
        required.extend(BACKGROUND_REQUIRED_SERVICES)
    return [name for name in dict.fromkeys(required) if getattr(services, name, None) is None]


def validate_runtime_services(services: AppRuntimeServices, role: RuntimeRole = "all") -> None:
    missing = missing_required_services(services, role)
    if missing:
        raise RuntimeError(f"Runtime services missing: {', '.join(missing)}")
