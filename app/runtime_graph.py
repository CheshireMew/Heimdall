from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from app.runtime import AppRuntimeServices, RuntimeRole, RuntimeTarget, runtime_role_targets
from config import settings


BackgroundLifecycleRunner = Callable[[Any, AppRuntimeServices], Awaitable[None] | None]
RuntimeFactory = Callable[["RuntimeBuildContext"], Any]


@dataclass(frozen=True, slots=True)
class RuntimeServiceRef:
    section: str
    name: str

    @property
    def key(self) -> str:
        return f"{self.section}.{self.name}"


@dataclass(frozen=True, slots=True)
class RuntimeServiceDefinition:
    ref: RuntimeServiceRef
    targets: frozenset[RuntimeTarget]
    build: RuntimeFactory
    deps: tuple[RuntimeServiceRef, ...] = ()
    optional_deps: tuple[RuntimeServiceRef, ...] = ()
    background_start: BackgroundLifecycleRunner | None = None
    background_stop: BackgroundLifecycleRunner | None = None
    background_start_order: int = 0
    background_stop_order: int = 0


@dataclass(slots=True)
class RuntimeBuildContext:
    role: RuntimeRole
    services: AppRuntimeServices

    def require(self, ref: RuntimeServiceRef):
        return self.services.require_service(ref)

    def optional(self, ref: RuntimeServiceRef):
        return self.services.get_service(ref)


INFRA_EXCHANGE_GATEWAY = RuntimeServiceRef("infra", "exchange_gateway")
INFRA_DATABASE_RUNTIME = RuntimeServiceRef("infra", "database_runtime")
INFRA_KLINE_STORE = RuntimeServiceRef("infra", "kline_store")
INFRA_CACHE_SERVICE = RuntimeServiceRef("infra", "cache_service")

MARKET_MARKET_DATA_SERVICE = RuntimeServiceRef("market", "market_data_service")
MARKET_REALTIME_SERVICE = RuntimeServiceRef("market", "realtime_service")
MARKET_INDICATOR_REPOSITORY = RuntimeServiceRef("market", "market_indicator_repository")
MARKET_INDICATOR_SERVICE = RuntimeServiceRef("market", "indicator_service")
MARKET_HISTORY_SERVICE = RuntimeServiceRef("market", "history_service")
MARKET_FUNDING_RATE_STORE = RuntimeServiceRef("market", "funding_rate_store")
MARKET_FUNDING_RATE_SERVICE = RuntimeServiceRef("market", "funding_rate_service")
MARKET_FUNDING_RATE_APP_SERVICE = RuntimeServiceRef("market", "funding_rate_app_service")
MARKET_CRYPTO_INDEX_SERVICE = RuntimeServiceRef("market", "crypto_index_service")
MARKET_QUERY_APP_SERVICE = RuntimeServiceRef("market", "market_query_app_service")
MARKET_INSIGHT_APP_SERVICE = RuntimeServiceRef("market", "market_insight_app_service")
MARKET_WEBSOCKET_SERVICE = RuntimeServiceRef("market", "market_websocket_service")
MARKET_INDEX_DATA_SERVICE = RuntimeServiceRef("market", "index_data_service")
MARKET_BINANCE_MARKET_SNAPSHOT = RuntimeServiceRef("market", "binance_market_snapshot")
MARKET_BINANCE_MARKET_INTEL = RuntimeServiceRef("market", "binance_market_intel")
MARKET_BINANCE_WEB3_SERVICE = RuntimeServiceRef("market", "binance_web3_service")

TOOLS_SENTIMENT_API_CLIENT = RuntimeServiceRef("tools", "sentiment_api_client")
TOOLS_SENTIMENT_REPOSITORY = RuntimeServiceRef("tools", "sentiment_repository")
TOOLS_SENTIMENT_SERVICE = RuntimeServiceRef("tools", "sentiment_service")
TOOLS_DCA_SERVICE = RuntimeServiceRef("tools", "dca_service")
TOOLS_PAIR_COMPARE_SERVICE = RuntimeServiceRef("tools", "pair_compare_service")
TOOLS_TOOLS_APP_SERVICE = RuntimeServiceRef("tools", "tools_app_service")

BACKTEST_RUN_REPOSITORY = RuntimeServiceRef("backtest", "backtest_run_repository")
BACKTEST_FREQTRADE_SERVICE = RuntimeServiceRef("backtest", "freqtrade_backtest_service")
BACKTEST_RUN_SERVICE = RuntimeServiceRef("backtest", "backtest_run_service")
BACKTEST_STRATEGY_QUERY_SERVICE = RuntimeServiceRef("backtest", "strategy_query_service")
BACKTEST_STRATEGY_WRITE_SERVICE = RuntimeServiceRef("backtest", "strategy_write_service")
BACKTEST_REPORT_BUILDER = RuntimeServiceRef("backtest", "freqtrade_report_builder")
BACKTEST_PAPER_RUN_MANAGER = RuntimeServiceRef("backtest", "paper_run_manager")
BACKTEST_COMMAND_SERVICE = RuntimeServiceRef("backtest", "backtest_command_service")
BACKTEST_QUERY_SERVICE = RuntimeServiceRef("backtest", "backtest_query_service")

FACTORS_RESEARCH_REPOSITORY = RuntimeServiceRef("factors", "factor_research_repository")
FACTORS_RESEARCH_SERVICE = RuntimeServiceRef("factors", "factor_research_service")
FACTORS_EXECUTION_SERVICE = RuntimeServiceRef("factors", "factor_execution_service")
FACTORS_SIGNAL_EXECUTION_CORE = RuntimeServiceRef("factors", "factor_signal_execution_core")
FACTORS_PAPER_PERSISTENCE_SERVICE = RuntimeServiceRef("factors", "factor_paper_persistence_service")
FACTORS_PAPER_RUN_MANAGER = RuntimeServiceRef("factors", "factor_paper_run_manager")

SYSTEM_CURRENCY_RATE_SERVICE = RuntimeServiceRef("system", "currency_rate_service")
SYSTEM_MARKET_SCHEDULER_RUNTIME = RuntimeServiceRef("system", "market_scheduler_runtime")


def _build_database_runtime(_ctx: RuntimeBuildContext):
    from app.infra.db import build_database_runtime

    return build_database_runtime(settings)


def _build_cache_service(_ctx: RuntimeBuildContext):
    from app.infra.cache import build_cache_service

    return build_cache_service(settings)


def _build_exchange_gateway(_ctx: RuntimeBuildContext):
    from app.services.market.exchange_gateway import ExchangeGateway

    return ExchangeGateway(exchange_id=settings.EXCHANGE_ID)


def _build_kline_store(ctx: RuntimeBuildContext):
    from app.services.market.kline_store import KlineStore

    return KlineStore(database_runtime=ctx.require(INFRA_DATABASE_RUNTIME))


def _build_llm_client_factory() -> Callable[[], Any]:
    from app.infra.llm_client import LLMClient
    from app.services.llm_config_service import read_effective_llm_config

    # LLM client 只消费已经收口后的业务配置，避免 infra 反向读取业务状态。
    return lambda: LLMClient(llm_config=read_effective_llm_config())


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
    from app.services.market.indicator_repository import MarketIndicatorRepository

    return MarketIndicatorRepository(database_runtime=ctx.require(INFRA_DATABASE_RUNTIME))


def _build_indicator_service(ctx: RuntimeBuildContext):
    from app.services.market.indicator_service import IndicatorService

    return IndicatorService(repository=ctx.require(MARKET_INDICATOR_REPOSITORY))


def _build_history_service(_ctx: RuntimeBuildContext):
    from app.services.market.history_service import HistoryService

    return HistoryService()


def _build_funding_rate_store(ctx: RuntimeBuildContext):
    from app.services.market.funding_rate_store import FundingRateStore

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
        history_service=ctx.require(MARKET_HISTORY_SERVICE),
        binance_snapshot_service=ctx.optional(MARKET_BINANCE_MARKET_SNAPSHOT),
        llm_client_factory=_build_llm_client_factory(),
    )


def _build_market_insight_app_service(ctx: RuntimeBuildContext):
    from app.services.market.insight_app_service import MarketInsightAppService

    return MarketInsightAppService(
        indicator_service=ctx.require(MARKET_INDICATOR_SERVICE),
        crypto_index_service=ctx.require(MARKET_CRYPTO_INDEX_SERVICE),
        market_query_service=ctx.require(MARKET_QUERY_APP_SERVICE),
        llm_client_factory=_build_llm_client_factory(),
    )


def _build_market_websocket_service(_ctx: RuntimeBuildContext):
    from app.services.market.websocket_service import MarketWebSocketService

    return MarketWebSocketService()


def _build_index_data_service(ctx: RuntimeBuildContext):
    from app.services.market.index_data_service import IndexDataService

    return IndexDataService(kline_store=ctx.require(INFRA_KLINE_STORE))


def _build_binance_market_snapshot(_ctx: RuntimeBuildContext):
    from app.services.market.binance_market_snapshot_service import BinanceMarketSnapshotService

    return BinanceMarketSnapshotService()


def _build_binance_market_intel(ctx: RuntimeBuildContext):
    from app.services.market.binance_market_intel_service import BinanceMarketIntelService

    return BinanceMarketIntelService(
        snapshot_service=ctx.optional(MARKET_BINANCE_MARKET_SNAPSHOT),
        cache_service=ctx.require(INFRA_CACHE_SERVICE),
    )


def _build_binance_web3_service(ctx: RuntimeBuildContext):
    from app.services.market.binance_web3_service import BinanceWeb3Service

    return BinanceWeb3Service(cache_service=ctx.require(INFRA_CACHE_SERVICE))


def _build_sentiment_api_client(_ctx: RuntimeBuildContext):
    from app.services.sentiment_client import SentimentApiClient

    return SentimentApiClient(settings.SENTIMENT_API_URL)


def _build_sentiment_repository(ctx: RuntimeBuildContext):
    from app.services.sentiment_repository import SentimentRepository

    return SentimentRepository(database_runtime=ctx.require(INFRA_DATABASE_RUNTIME))


def _build_sentiment_service(ctx: RuntimeBuildContext):
    from app.services.sentiment_service import SentimentService

    return SentimentService(
        client=ctx.require(TOOLS_SENTIMENT_API_CLIENT),
        repository=ctx.require(TOOLS_SENTIMENT_REPOSITORY),
    )


def _build_dca_service(ctx: RuntimeBuildContext):
    from app.services.tools.dca_service import DCAService

    return DCAService(
        market_data_service=ctx.require(MARKET_MARKET_DATA_SERVICE),
        sentiment_service=ctx.require(TOOLS_SENTIMENT_SERVICE),
        index_data_service=ctx.require(MARKET_INDEX_DATA_SERVICE),
    )


def _build_pair_compare_service(ctx: RuntimeBuildContext):
    from app.services.tools.pair_compare_service import PairCompareService

    return PairCompareService(
        market_data_service=ctx.require(MARKET_MARKET_DATA_SERVICE),
        index_data_service=ctx.require(MARKET_INDEX_DATA_SERVICE),
    )


def _build_tools_app_service(ctx: RuntimeBuildContext):
    from app.services.tools.app_service import ToolsAppService

    return ToolsAppService(
        dca_service=ctx.require(TOOLS_DCA_SERVICE),
        pair_compare_service=ctx.require(TOOLS_PAIR_COMPARE_SERVICE),
        cache_service=ctx.require(INFRA_CACHE_SERVICE),
    )


def _build_backtest_run_repository(ctx: RuntimeBuildContext):
    from app.services.backtest.run_repository import BacktestRunRepository

    return BacktestRunRepository(database_runtime=ctx.require(INFRA_DATABASE_RUNTIME))


def _build_freqtrade_backtest_service(ctx: RuntimeBuildContext):
    from app.services.backtest.freqtrade_service import FreqtradeBacktestService

    return FreqtradeBacktestService(market_data_service=ctx.require(MARKET_MARKET_DATA_SERVICE))


def _build_backtest_run_service(ctx: RuntimeBuildContext):
    from app.services.backtest.run_service import BacktestRunService

    return BacktestRunService(
        execution_engine=ctx.require(BACKTEST_FREQTRADE_SERVICE),
        database_runtime=ctx.require(INFRA_DATABASE_RUNTIME),
    )


def _build_strategy_query_service(ctx: RuntimeBuildContext):
    from app.services.backtest.strategy_query_service import StrategyQueryService

    return StrategyQueryService(database_runtime=ctx.require(INFRA_DATABASE_RUNTIME))


def _build_strategy_write_service(ctx: RuntimeBuildContext):
    from app.services.backtest.strategy_write_service import StrategyWriteService

    return StrategyWriteService(database_runtime=ctx.require(INFRA_DATABASE_RUNTIME))


def _build_freqtrade_report_builder(_ctx: RuntimeBuildContext):
    from app.services.backtest.freqtrade_report_builder import FreqtradeReportBuilder

    return FreqtradeReportBuilder()


def _build_paper_run_manager(ctx: RuntimeBuildContext):
    from app.services.backtest.paper_manager import PaperRunManager

    return PaperRunManager(
        strategy_query_service=ctx.require(BACKTEST_STRATEGY_QUERY_SERVICE),
        freqtrade_service=ctx.require(BACKTEST_FREQTRADE_SERVICE),
        report_builder=ctx.require(BACKTEST_REPORT_BUILDER),
        run_repository=ctx.require(BACKTEST_RUN_REPOSITORY),
        database_runtime=ctx.require(INFRA_DATABASE_RUNTIME),
    )


def _build_backtest_command_service(ctx: RuntimeBuildContext):
    from app.services.backtest.command_service import BacktestCommandService

    return BacktestCommandService(
        run_service=ctx.require(BACKTEST_RUN_SERVICE),
        paper_manager=ctx.require(BACKTEST_PAPER_RUN_MANAGER),
        run_repository=ctx.require(BACKTEST_RUN_REPOSITORY),
        strategy_query_service=ctx.require(BACKTEST_STRATEGY_QUERY_SERVICE),
        strategy_write_service=ctx.require(BACKTEST_STRATEGY_WRITE_SERVICE),
    )


def _build_backtest_query_service(ctx: RuntimeBuildContext):
    from app.services.backtest.query_service import BacktestQueryService

    return BacktestQueryService(
        run_repository=ctx.require(BACKTEST_RUN_REPOSITORY),
        strategy_query_service=ctx.require(BACKTEST_STRATEGY_QUERY_SERVICE),
    )


def _build_factor_research_repository(ctx: RuntimeBuildContext):
    from app.services.factors.repository import FactorResearchRepository

    return FactorResearchRepository(database_runtime=ctx.require(INFRA_DATABASE_RUNTIME))


def _build_factor_research_service(ctx: RuntimeBuildContext):
    from app.services.factors.service import FactorResearchService

    return FactorResearchService(
        market_data_service=ctx.require(MARKET_MARKET_DATA_SERVICE),
        indicator_repository=ctx.require(MARKET_INDICATOR_REPOSITORY),
        repository=ctx.require(FACTORS_RESEARCH_REPOSITORY),
    )


def _build_factor_execution_service(ctx: RuntimeBuildContext):
    from app.services.factors.execution import FactorExecutionService

    return FactorExecutionService(
        factor_service=ctx.require(FACTORS_RESEARCH_SERVICE),
        report_builder=ctx.require(BACKTEST_REPORT_BUILDER),
        execution_core=ctx.require(FACTORS_SIGNAL_EXECUTION_CORE),
        database_runtime=ctx.require(INFRA_DATABASE_RUNTIME),
    )


def _build_factor_signal_execution_core(_ctx: RuntimeBuildContext):
    from app.services.factors.signal_execution_core import FactorSignalExecutionCore

    return FactorSignalExecutionCore()


def _build_factor_paper_persistence_service(ctx: RuntimeBuildContext):
    from app.services.factors.paper_persistence_service import FactorPaperPersistenceService

    return FactorPaperPersistenceService(
        report_builder=ctx.require(BACKTEST_REPORT_BUILDER),
        execution_core=ctx.require(FACTORS_SIGNAL_EXECUTION_CORE),
    )


def _build_factor_paper_run_manager(ctx: RuntimeBuildContext):
    from app.services.factors.paper_manager import FactorPaperRunManager

    return FactorPaperRunManager(
        factor_service=ctx.require(FACTORS_RESEARCH_SERVICE),
        run_repository=ctx.require(BACKTEST_RUN_REPOSITORY),
        report_builder=ctx.require(BACKTEST_REPORT_BUILDER),
        execution_core=ctx.require(FACTORS_SIGNAL_EXECUTION_CORE),
        persistence_service=ctx.require(FACTORS_PAPER_PERSISTENCE_SERVICE),
        database_runtime=ctx.require(INFRA_DATABASE_RUNTIME),
    )


def _build_currency_rate_service(_ctx: RuntimeBuildContext):
    from app.services.currency_service import CurrencyRateService

    return CurrencyRateService()


def _build_market_scheduler_runtime(ctx: RuntimeBuildContext):
    from app.services.market_scheduler_runtime import MarketSchedulerRuntime

    return MarketSchedulerRuntime(database_runtime=ctx.require(INFRA_DATABASE_RUNTIME))


async def _start_market_scheduler(service, _runtime_services: AppRuntimeServices) -> None:
    service.start()


async def _start_binance_snapshot(service, runtime_services: AppRuntimeServices) -> None:
    binance_market = runtime_services.require_service(MARKET_BINANCE_MARKET_INTEL)
    await service.start(
        spot_ticker_loader=binance_market.spot.get_ticker_24hr,
        usdm_ticker_loader=binance_market.usdm.get_ticker_24hr,
        usdm_mark_loader=binance_market.usdm.get_mark_price,
    )


async def _restore_paper_runs(service, _runtime_services: AppRuntimeServices) -> None:
    await service.restore_active_runs()


async def _shutdown_service(service, _runtime_services: AppRuntimeServices) -> None:
    await service.shutdown()


RUNTIME_SERVICE_DEFINITIONS: tuple[RuntimeServiceDefinition, ...] = (
    RuntimeServiceDefinition(INFRA_DATABASE_RUNTIME, frozenset({"api", "background"}), _build_database_runtime),
    RuntimeServiceDefinition(INFRA_CACHE_SERVICE, frozenset({"api", "background"}), _build_cache_service),
    RuntimeServiceDefinition(INFRA_EXCHANGE_GATEWAY, frozenset({"api", "background"}), _build_exchange_gateway),
    RuntimeServiceDefinition(
        INFRA_KLINE_STORE,
        frozenset({"api", "background"}),
        _build_kline_store,
        deps=(INFRA_DATABASE_RUNTIME,),
    ),
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
    RuntimeServiceDefinition(MARKET_HISTORY_SERVICE, frozenset({"api"}), _build_history_service),
    RuntimeServiceDefinition(
        MARKET_FUNDING_RATE_STORE,
        frozenset({"api"}),
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
        MARKET_BINANCE_MARKET_SNAPSHOT,
        frozenset({"background"}),
        _build_binance_market_snapshot,
        background_start=_start_binance_snapshot,
        background_stop=_shutdown_service,
        background_start_order=20,
        background_stop_order=10,
    ),
    RuntimeServiceDefinition(
        MARKET_QUERY_APP_SERVICE,
        frozenset({"api"}),
        _build_market_query_app_service,
        deps=(
            MARKET_MARKET_DATA_SERVICE,
            MARKET_REALTIME_SERVICE,
            MARKET_HISTORY_SERVICE,
        ),
        optional_deps=(MARKET_BINANCE_MARKET_SNAPSHOT,),
    ),
    RuntimeServiceDefinition(
        MARKET_INSIGHT_APP_SERVICE,
        frozenset({"api"}),
        _build_market_insight_app_service,
        deps=(MARKET_INDICATOR_SERVICE, MARKET_CRYPTO_INDEX_SERVICE, MARKET_QUERY_APP_SERVICE),
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
        deps=(INFRA_CACHE_SERVICE,),
        optional_deps=(MARKET_BINANCE_MARKET_SNAPSHOT,),
    ),
    RuntimeServiceDefinition(
        MARKET_BINANCE_WEB3_SERVICE,
        frozenset({"api"}),
        _build_binance_web3_service,
        deps=(INFRA_CACHE_SERVICE,),
    ),
    RuntimeServiceDefinition(TOOLS_SENTIMENT_API_CLIENT, frozenset({"api"}), _build_sentiment_api_client),
    RuntimeServiceDefinition(
        TOOLS_SENTIMENT_REPOSITORY,
        frozenset({"api"}),
        _build_sentiment_repository,
        deps=(INFRA_DATABASE_RUNTIME,),
    ),
    RuntimeServiceDefinition(
        TOOLS_SENTIMENT_SERVICE,
        frozenset({"api"}),
        _build_sentiment_service,
        deps=(TOOLS_SENTIMENT_API_CLIENT, TOOLS_SENTIMENT_REPOSITORY),
    ),
    RuntimeServiceDefinition(
        TOOLS_DCA_SERVICE,
        frozenset({"api"}),
        _build_dca_service,
        deps=(MARKET_MARKET_DATA_SERVICE, TOOLS_SENTIMENT_SERVICE, MARKET_INDEX_DATA_SERVICE),
    ),
    RuntimeServiceDefinition(
        TOOLS_PAIR_COMPARE_SERVICE,
        frozenset({"api"}),
        _build_pair_compare_service,
        deps=(MARKET_MARKET_DATA_SERVICE, MARKET_INDEX_DATA_SERVICE),
    ),
    RuntimeServiceDefinition(
        TOOLS_TOOLS_APP_SERVICE,
        frozenset({"api"}),
        _build_tools_app_service,
        deps=(TOOLS_DCA_SERVICE, TOOLS_PAIR_COMPARE_SERVICE, INFRA_CACHE_SERVICE),
    ),
    RuntimeServiceDefinition(
        BACKTEST_RUN_REPOSITORY,
        frozenset({"api", "background"}),
        _build_backtest_run_repository,
        deps=(INFRA_DATABASE_RUNTIME,),
    ),
    RuntimeServiceDefinition(
        BACKTEST_FREQTRADE_SERVICE,
        frozenset({"api", "background"}),
        _build_freqtrade_backtest_service,
        deps=(MARKET_MARKET_DATA_SERVICE,),
    ),
    RuntimeServiceDefinition(
        BACKTEST_RUN_SERVICE,
        frozenset({"api"}),
        _build_backtest_run_service,
        deps=(BACKTEST_FREQTRADE_SERVICE, INFRA_DATABASE_RUNTIME),
    ),
    RuntimeServiceDefinition(
        BACKTEST_STRATEGY_QUERY_SERVICE,
        frozenset({"api", "background"}),
        _build_strategy_query_service,
        deps=(INFRA_DATABASE_RUNTIME,),
    ),
    RuntimeServiceDefinition(
        BACKTEST_STRATEGY_WRITE_SERVICE,
        frozenset({"api"}),
        _build_strategy_write_service,
        deps=(INFRA_DATABASE_RUNTIME,),
    ),
    RuntimeServiceDefinition(BACKTEST_REPORT_BUILDER, frozenset({"api", "background"}), _build_freqtrade_report_builder),
    RuntimeServiceDefinition(
        BACKTEST_PAPER_RUN_MANAGER,
        frozenset({"api", "background"}),
        _build_paper_run_manager,
        deps=(
            BACKTEST_STRATEGY_QUERY_SERVICE,
            BACKTEST_FREQTRADE_SERVICE,
            BACKTEST_REPORT_BUILDER,
            BACKTEST_RUN_REPOSITORY,
            INFRA_DATABASE_RUNTIME,
        ),
        background_start=_restore_paper_runs,
        background_stop=_shutdown_service,
        background_start_order=30,
        background_stop_order=30,
    ),
    RuntimeServiceDefinition(
        BACKTEST_COMMAND_SERVICE,
        frozenset({"api"}),
        _build_backtest_command_service,
        deps=(
            BACKTEST_RUN_SERVICE,
            BACKTEST_PAPER_RUN_MANAGER,
            BACKTEST_RUN_REPOSITORY,
            BACKTEST_STRATEGY_QUERY_SERVICE,
            BACKTEST_STRATEGY_WRITE_SERVICE,
        ),
    ),
    RuntimeServiceDefinition(
        BACKTEST_QUERY_SERVICE,
        frozenset({"api"}),
        _build_backtest_query_service,
        deps=(BACKTEST_RUN_REPOSITORY, BACKTEST_STRATEGY_QUERY_SERVICE),
    ),
    RuntimeServiceDefinition(
        FACTORS_RESEARCH_REPOSITORY,
        frozenset({"api", "background"}),
        _build_factor_research_repository,
        deps=(INFRA_DATABASE_RUNTIME,),
    ),
    RuntimeServiceDefinition(
        FACTORS_RESEARCH_SERVICE,
        frozenset({"api", "background"}),
        _build_factor_research_service,
        deps=(MARKET_MARKET_DATA_SERVICE, MARKET_INDICATOR_REPOSITORY, FACTORS_RESEARCH_REPOSITORY),
    ),
    RuntimeServiceDefinition(
        FACTORS_EXECUTION_SERVICE,
        frozenset({"api"}),
        _build_factor_execution_service,
        deps=(FACTORS_RESEARCH_SERVICE, BACKTEST_REPORT_BUILDER, FACTORS_SIGNAL_EXECUTION_CORE, INFRA_DATABASE_RUNTIME),
    ),
    RuntimeServiceDefinition(
        FACTORS_SIGNAL_EXECUTION_CORE,
        frozenset({"api", "background"}),
        _build_factor_signal_execution_core,
    ),
    RuntimeServiceDefinition(
        FACTORS_PAPER_PERSISTENCE_SERVICE,
        frozenset({"api", "background"}),
        _build_factor_paper_persistence_service,
        deps=(BACKTEST_REPORT_BUILDER, FACTORS_SIGNAL_EXECUTION_CORE),
    ),
    RuntimeServiceDefinition(
        FACTORS_PAPER_RUN_MANAGER,
        frozenset({"api", "background"}),
        _build_factor_paper_run_manager,
        deps=(
            FACTORS_RESEARCH_SERVICE,
            BACKTEST_RUN_REPOSITORY,
            BACKTEST_REPORT_BUILDER,
            FACTORS_SIGNAL_EXECUTION_CORE,
            FACTORS_PAPER_PERSISTENCE_SERVICE,
            INFRA_DATABASE_RUNTIME,
        ),
        background_start=_restore_paper_runs,
        background_stop=_shutdown_service,
        background_start_order=40,
        background_stop_order=20,
    ),
    RuntimeServiceDefinition(SYSTEM_CURRENCY_RATE_SERVICE, frozenset({"api"}), _build_currency_rate_service),
    RuntimeServiceDefinition(
        SYSTEM_MARKET_SCHEDULER_RUNTIME,
        frozenset({"background"}),
        _build_market_scheduler_runtime,
        deps=(INFRA_DATABASE_RUNTIME,),
        background_start=_start_market_scheduler,
        background_stop=_shutdown_service,
        background_start_order=10,
        background_stop_order=40,
    ),
)

def active_service_definitions(role: RuntimeRole) -> tuple[RuntimeServiceDefinition, ...]:
    active_targets = set(runtime_role_targets(role))
    return tuple(
        definition
        for definition in RUNTIME_SERVICE_DEFINITIONS
        if definition.targets & active_targets
    )


def _topologically_sorted_service_definitions(
    definitions: tuple[RuntimeServiceDefinition, ...],
) -> list[RuntimeServiceDefinition]:
    remaining = {definition.ref: definition for definition in definitions}
    active_refs = set(remaining)
    ordered: list[RuntimeServiceDefinition] = []

    missing_required_edges = [
        f"{definition.ref.key} -> {dependency.key}"
        for definition in definitions
        for dependency in definition.deps
        if dependency not in active_refs
    ]
    if missing_required_edges:
        # required/optional 的唯一边界在 RuntimeServiceDefinition；缺失 required 边说明 role 图本身错误。
        raise RuntimeError(
            "Runtime service graph has inactive required dependencies: "
            + ", ".join(sorted(missing_required_edges))
        )

    while remaining:
        ready = sorted(
            (
                definition
                for definition in remaining.values()
                if all(
                    dep not in remaining
                    for dep in definition.deps
                    + tuple(dep for dep in definition.optional_deps if dep in active_refs)
                )
            ),
            key=lambda definition: definition.ref.key,
        )
        if not ready:
            cycle = ", ".join(sorted(ref.key for ref in remaining))
            raise RuntimeError(f"Runtime service graph contains a cycle: {cycle}")
        for definition in ready:
            ordered.append(definition)
            remaining.pop(definition.ref, None)
    return ordered


def build_app_runtime_services(role: RuntimeRole | None = None) -> AppRuntimeServices:
    resolved_role = role or settings.APP_RUNTIME_ROLE
    services = AppRuntimeServices.empty()
    context = RuntimeBuildContext(role=resolved_role, services=services)
    definitions = active_service_definitions(resolved_role)

    for definition in _topologically_sorted_service_definitions(definitions):
        services.set_service(definition.ref, definition.build(context))

    services.validate_required_services(resolved_role)
    return services


def background_start_definitions() -> tuple[RuntimeServiceDefinition, ...]:
    return tuple(
        sorted(
            (
                definition
                for definition in active_service_definitions("background")
                if definition.background_start is not None
            ),
            key=lambda definition: (definition.background_start_order, definition.ref.key),
        )
    )


def background_stop_definitions() -> tuple[RuntimeServiceDefinition, ...]:
    return tuple(
        sorted(
            (
                definition
                for definition in active_service_definitions("background")
                if definition.background_stop is not None
            ),
            key=lambda definition: (definition.background_stop_order, definition.ref.key),
        )
    )
