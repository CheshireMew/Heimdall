from __future__ import annotations

from typing import Any, Callable

from app.runtime_definition import RuntimeBuildContext, RuntimeServiceDefinition
from app.runtime_lifecycle import shutdown_service, start_binance_market_page_refresher, start_binance_snapshot
from app.runtime_refs import (
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
    SYSTEM_LLM_CONFIG_SERVICE,
)


def _build_llm_client_factory(llm_config_service) -> Callable[[], Any]:
    from app.infra.llm_client import LLMClient

    return lambda: LLMClient(llm_config=llm_config_service.read_effective_config())


def _build_market_data_service(ctx: RuntimeBuildContext):
    from app.services.market.market_data_service import MarketDataService

    return MarketDataService(
        exchange_gateway=ctx.require(INFRA_EXCHANGE_GATEWAY),
        kline_store=ctx.require(INFRA_KLINE_STORE),
        cache_service=ctx.require(INFRA_CACHE_SERVICE),
    )


def _build_realtime_service(_ctx: RuntimeBuildContext):
    from app.services.market.realtime_service import RealtimeService

    return RealtimeService()


def _build_market_indicator_repository(ctx: RuntimeBuildContext):
    from app.infra.persistence.market.indicator_repository import MarketIndicatorRepository

    return MarketIndicatorRepository(database_runtime=ctx.require(INFRA_DATABASE_RUNTIME))


def _build_indicator_service(ctx: RuntimeBuildContext):
    from app.services.market.indicator_service import IndicatorService

    return IndicatorService(repository=ctx.require(MARKET_INDICATOR_REPOSITORY))


def _build_funding_rate_store(ctx: RuntimeBuildContext):
    from app.infra.persistence.market.funding_rate_store import FundingRateStore

    return FundingRateStore(database_runtime=ctx.require(INFRA_DATABASE_RUNTIME))


def _build_funding_rate_service(ctx: RuntimeBuildContext):
    from app.services.market.funding_rate_service import FundingRateService

    return FundingRateService(store=ctx.require(MARKET_FUNDING_RATE_STORE))


def _build_funding_rate_app_service(ctx: RuntimeBuildContext):
    from app.services.market.funding_rate_app_service import FundingRateAppService

    return FundingRateAppService(funding_rate_service=ctx.require(MARKET_FUNDING_RATE_SERVICE))


def _build_crypto_index_service(ctx: RuntimeBuildContext):
    from app.services.market.crypto_index_service import CryptoIndexService

    return CryptoIndexService(cache_service=ctx.require(INFRA_CACHE_SERVICE))


def _build_market_query_app_service(ctx: RuntimeBuildContext):
    from app.services.market.query_app_service import MarketQueryAppService

    return MarketQueryAppService(
        market_data_service=ctx.require(MARKET_MARKET_DATA_SERVICE),
        realtime_service=ctx.require(MARKET_REALTIME_SERVICE),
        binance_snapshot_service=ctx.require(MARKET_BINANCE_MARKET_SNAPSHOT),
        llm_client_factory=_build_llm_client_factory(ctx.require(SYSTEM_LLM_CONFIG_SERVICE)),
    )


def _build_market_insight_app_service(ctx: RuntimeBuildContext):
    from app.services.market.insight_app_service import MarketInsightAppService

    return MarketInsightAppService(
        indicator_service=ctx.require(MARKET_INDICATOR_SERVICE),
        crypto_index_service=ctx.require(MARKET_CRYPTO_INDEX_SERVICE),
        market_query_service=ctx.require(MARKET_QUERY_APP_SERVICE),
        llm_client_factory=_build_llm_client_factory(ctx.require(SYSTEM_LLM_CONFIG_SERVICE)),
    )


def _build_market_websocket_service(_ctx: RuntimeBuildContext):
    from app.services.market.websocket_service import MarketWebSocketService

    return MarketWebSocketService()


def _build_index_data_service(ctx: RuntimeBuildContext):
    from app.services.market.index_data_service import IndexDataService

    return IndexDataService(kline_store=ctx.require(INFRA_KLINE_STORE))


def _build_binance_market_snapshot(ctx: RuntimeBuildContext):
    return ctx.require(MARKET_BINANCE_MARKET_INTEL).snapshot_service


def _build_binance_market_research_store(ctx: RuntimeBuildContext):
    from app.infra.persistence.market.binance_market_research_store import BinanceMarketResearchStore

    return BinanceMarketResearchStore(database_runtime=ctx.require(INFRA_DATABASE_RUNTIME))


def _build_binance_market_intel(ctx: RuntimeBuildContext):
    from app.services.market.binance_market_intel_service import BinanceMarketIntelService

    return BinanceMarketIntelService(
        research_store=ctx.require(MARKET_BINANCE_MARKET_RESEARCH_STORE),
        funding_rate_store=ctx.require(MARKET_FUNDING_RATE_STORE),
        cache_service=ctx.require(INFRA_CACHE_SERVICE),
    )


def _build_binance_web3_service(ctx: RuntimeBuildContext):
    from app.services.market.binance_web3_service import BinanceWeb3Service

    return BinanceWeb3Service(
        cache_service=ctx.require(INFRA_CACHE_SERVICE),
        kline_store=ctx.require(INFRA_KLINE_STORE),
    )


MARKET_SERVICE_DEFINITIONS: tuple[RuntimeServiceDefinition, ...] = (
    RuntimeServiceDefinition(
        MARKET_MARKET_DATA_SERVICE,
        frozenset({"api", "background"}),
        _build_market_data_service,
        deps=(INFRA_EXCHANGE_GATEWAY, INFRA_KLINE_STORE, INFRA_CACHE_SERVICE),
    ),
    RuntimeServiceDefinition(MARKET_REALTIME_SERVICE, frozenset({"api"}), _build_realtime_service),
    RuntimeServiceDefinition(
        MARKET_INDICATOR_REPOSITORY,
        frozenset({"api", "background"}),
        _build_market_indicator_repository,
        deps=(INFRA_DATABASE_RUNTIME,),
    ),
    RuntimeServiceDefinition(
        MARKET_INDICATOR_SERVICE,
        frozenset({"api"}),
        _build_indicator_service,
        deps=(MARKET_INDICATOR_REPOSITORY,),
    ),
    RuntimeServiceDefinition(
        MARKET_FUNDING_RATE_STORE,
        frozenset({"api", "background"}),
        _build_funding_rate_store,
        deps=(INFRA_DATABASE_RUNTIME,),
    ),
    RuntimeServiceDefinition(
        MARKET_FUNDING_RATE_SERVICE,
        frozenset({"api"}),
        _build_funding_rate_service,
        deps=(MARKET_FUNDING_RATE_STORE,),
    ),
    RuntimeServiceDefinition(
        MARKET_FUNDING_RATE_APP_SERVICE,
        frozenset({"api"}),
        _build_funding_rate_app_service,
        deps=(MARKET_FUNDING_RATE_SERVICE,),
    ),
    RuntimeServiceDefinition(
        MARKET_CRYPTO_INDEX_SERVICE,
        frozenset({"api"}),
        _build_crypto_index_service,
        deps=(INFRA_CACHE_SERVICE,),
    ),
    RuntimeServiceDefinition(
        MARKET_BINANCE_MARKET_RESEARCH_STORE,
        frozenset({"api", "background"}),
        _build_binance_market_research_store,
        deps=(INFRA_DATABASE_RUNTIME,),
    ),
    RuntimeServiceDefinition(
        MARKET_QUERY_APP_SERVICE,
        frozenset({"api"}),
        _build_market_query_app_service,
        deps=(MARKET_MARKET_DATA_SERVICE, MARKET_REALTIME_SERVICE, MARKET_BINANCE_MARKET_SNAPSHOT, SYSTEM_LLM_CONFIG_SERVICE),
    ),
    RuntimeServiceDefinition(
        MARKET_INSIGHT_APP_SERVICE,
        frozenset({"api"}),
        _build_market_insight_app_service,
        deps=(MARKET_INDICATOR_SERVICE, MARKET_CRYPTO_INDEX_SERVICE, MARKET_QUERY_APP_SERVICE, SYSTEM_LLM_CONFIG_SERVICE),
    ),
    RuntimeServiceDefinition(MARKET_WEBSOCKET_SERVICE, frozenset({"api"}), _build_market_websocket_service),
    RuntimeServiceDefinition(
        MARKET_INDEX_DATA_SERVICE,
        frozenset({"api"}),
        _build_index_data_service,
        deps=(INFRA_KLINE_STORE,),
    ),
    RuntimeServiceDefinition(
        MARKET_BINANCE_MARKET_INTEL,
        frozenset({"api", "background"}),
        _build_binance_market_intel,
        deps=(
            INFRA_CACHE_SERVICE,
            MARKET_BINANCE_MARKET_RESEARCH_STORE,
            MARKET_FUNDING_RATE_STORE,
        ),
        background_start=start_binance_market_page_refresher,
        background_stop=shutdown_service,
        background_start_order=25,
        background_stop_order=5,
    ),
    RuntimeServiceDefinition(
        MARKET_BINANCE_MARKET_SNAPSHOT,
        frozenset({"api", "background"}),
        _build_binance_market_snapshot,
        deps=(MARKET_BINANCE_MARKET_INTEL,),
        background_start=start_binance_snapshot,
        background_stop=shutdown_service,
        background_start_order=20,
        background_stop_order=10,
    ),
    RuntimeServiceDefinition(
        MARKET_BINANCE_WEB3_SERVICE,
        frozenset({"api"}),
        _build_binance_web3_service,
        deps=(INFRA_CACHE_SERVICE, INFRA_KLINE_STORE),
    ),
)
