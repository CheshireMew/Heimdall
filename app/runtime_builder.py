from __future__ import annotations

from app.runtime import (
    AppRuntimeServices,
    BacktestRuntime,
    FactorRuntime,
    InfraRuntime,
    MarketRuntime,
    SystemRuntime,
    ToolsRuntime,
    runtime_role_has_target,
)
from config import settings


def build_app_runtime_services() -> AppRuntimeServices:
    from app.infra.db import build_database_runtime
    from app.infra.cache import build_cache_service
    from app.infra.llm_client import LLMClient
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
    from app.services.llm_config_service import read_effective_llm_config
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
    from app.services.market_scheduler_runtime import MarketSchedulerRuntime
    from app.services.market.websocket_service import MarketWebSocketService
    from app.services.sentiment_client import SentimentApiClient
    from app.services.sentiment_repository import SentimentRepository
    from app.services.sentiment_service import SentimentService
    from app.services.tools.app_service import ToolsAppService
    from app.services.tools.dca_service import DCAService
    from app.services.tools.pair_compare_service import PairCompareService

    runtime_role = settings.APP_RUNTIME_ROLE
    build_api_runtime = runtime_role_has_target(runtime_role, "api")
    build_background_runtime = runtime_role_has_target(runtime_role, "background")
    build_execution_runtime = build_api_runtime or build_background_runtime

    database_runtime = build_database_runtime(settings)
    cache_service = build_cache_service(settings)
    exchange_gateway = ExchangeGateway(exchange_id=settings.EXCHANGE_ID)
    # LLM 配置属于服务层运行时状态；infra client 只消费已经解析好的配置，避免底层反向依赖业务服务。
    def build_llm_client() -> LLMClient:
        return LLMClient(llm_config=read_effective_llm_config())

    kline_store = KlineStore(database_runtime=database_runtime)
    market_data_service = MarketDataService(
        exchange_gateway=exchange_gateway,
        kline_store=kline_store,
        cache_service=cache_service,
    )
    market_indicator_repository = MarketIndicatorRepository(database_runtime=database_runtime)
    realtime_service = RealtimeService() if build_api_runtime else None
    indicator_service = (
        IndicatorService(repository=market_indicator_repository)
        if build_api_runtime
        else None
    )
    history_service = HistoryService() if build_api_runtime else None
    funding_rate_store = FundingRateStore(database_runtime=database_runtime) if build_api_runtime else None
    funding_rate_service = (
        FundingRateService(store=funding_rate_store)
        if funding_rate_store is not None
        else None
    )
    funding_rate_app_service = (
        FundingRateAppService(funding_rate_service=funding_rate_service)
        if funding_rate_service is not None
        else None
    )
    crypto_index_service = CryptoIndexService(cache_service=cache_service) if build_api_runtime else None
    binance_market_snapshot = BinanceMarketSnapshotService() if build_background_runtime else None
    market_query_app_service = (
        MarketQueryAppService(
            market_data_service=market_data_service,
            realtime_service=realtime_service,
            history_service=history_service,
            binance_snapshot_service=binance_market_snapshot,
            llm_client_factory=build_llm_client,
        )
        if realtime_service is not None and history_service is not None
        else None
    )
    market_insight_app_service = (
        MarketInsightAppService(
            indicator_service=indicator_service,
            crypto_index_service=crypto_index_service,
            market_query_service=market_query_app_service,
            llm_client_factory=build_llm_client,
        )
        if indicator_service is not None
        and crypto_index_service is not None
        and market_query_app_service is not None
        else None
    )
    market_websocket_service = MarketWebSocketService() if build_api_runtime else None
    index_data_service = IndexDataService(kline_store=kline_store) if build_api_runtime else None
    binance_market_intel = (
        BinanceMarketIntelService(
            snapshot_service=binance_market_snapshot,
            cache_service=cache_service,
        )
        if build_api_runtime or build_background_runtime
        else None
    )
    binance_web3_service = BinanceWeb3Service(cache_service=cache_service) if build_api_runtime else None
    backtest_run_repository = (
        BacktestRunRepository(database_runtime=database_runtime)
        if build_execution_runtime
        else None
    )
    freqtrade_backtest_service = (
        FreqtradeBacktestService(market_data_service=market_data_service)
        if build_execution_runtime
        else None
    )
    backtest_run_service = (
        BacktestRunService(
            execution_engine=freqtrade_backtest_service,
            database_runtime=database_runtime,
        )
        if build_api_runtime and freqtrade_backtest_service is not None
        else None
    )
    strategy_query_service = (
        StrategyQueryService(database_runtime=database_runtime)
        if build_execution_runtime
        else None
    )
    strategy_write_service = (
        StrategyWriteService(database_runtime=database_runtime)
        if build_api_runtime
        else None
    )
    freqtrade_report_builder = FreqtradeReportBuilder() if build_execution_runtime else None
    paper_run_manager = (
        PaperRunManager(
            strategy_query_service=strategy_query_service,
            freqtrade_service=freqtrade_backtest_service,
            report_builder=freqtrade_report_builder,
            run_repository=backtest_run_repository,
            database_runtime=database_runtime,
        )
        if strategy_query_service is not None
        and freqtrade_backtest_service is not None
        and freqtrade_report_builder is not None
        and backtest_run_repository is not None
        else None
    )
    backtest_command_service = (
        BacktestCommandService(
            run_service=backtest_run_service,
            paper_manager=paper_run_manager,
            run_repository=backtest_run_repository,
            strategy_query_service=strategy_query_service,
            strategy_write_service=strategy_write_service,
        )
        if backtest_run_service is not None
        and paper_run_manager is not None
        and backtest_run_repository is not None
        and strategy_query_service is not None
        and strategy_write_service is not None
        else None
    )
    backtest_query_service = (
        BacktestQueryService(
            run_repository=backtest_run_repository,
            strategy_query_service=strategy_query_service,
        )
        if build_api_runtime
        and backtest_run_repository is not None
        and strategy_query_service is not None
        else None
    )
    sentiment_api_client = SentimentApiClient(settings.SENTIMENT_API_URL) if build_api_runtime else None
    sentiment_repository = (
        SentimentRepository(database_runtime=database_runtime)
        if build_api_runtime
        else None
    )
    sentiment_service = (
        SentimentService(
            client=sentiment_api_client,
            repository=sentiment_repository,
        )
        if sentiment_api_client is not None and sentiment_repository is not None
        else None
    )
    dca_service = (
        DCAService(
            market_data_service=market_data_service,
            sentiment_service=sentiment_service,
            index_data_service=index_data_service,
        )
        if sentiment_service is not None and index_data_service is not None
        else None
    )
    pair_compare_service = (
        PairCompareService(
            market_data_service=market_data_service,
            index_data_service=index_data_service,
        )
        if index_data_service is not None
        else None
    )
    tools_app_service = (
        ToolsAppService(
            dca_service=dca_service,
            pair_compare_service=pair_compare_service,
            cache_service=cache_service,
        )
        if dca_service is not None and pair_compare_service is not None
        else None
    )
    factor_research_repository = (
        FactorResearchRepository(database_runtime=database_runtime)
        if build_execution_runtime
        else None
    )
    factor_research_service = (
        FactorResearchService(
            market_data_service=market_data_service,
            indicator_repository=market_indicator_repository,
            repository=factor_research_repository,
        )
        if factor_research_repository is not None
        else None
    )
    factor_signal_execution_core = FactorSignalExecutionCore() if build_execution_runtime else None
    factor_execution_service = (
        FactorExecutionService(
            factor_service=factor_research_service,
            report_builder=freqtrade_report_builder,
            execution_core=factor_signal_execution_core,
            database_runtime=database_runtime,
        )
        if build_api_runtime
        and factor_research_service is not None
        and freqtrade_report_builder is not None
        and factor_signal_execution_core is not None
        else None
    )
    factor_paper_persistence_service = (
        FactorPaperPersistenceService(
            report_builder=freqtrade_report_builder,
            execution_core=factor_signal_execution_core,
        )
        if freqtrade_report_builder is not None
        and factor_signal_execution_core is not None
        else None
    )
    factor_paper_run_manager = (
        FactorPaperRunManager(
            factor_service=factor_research_service,
            run_repository=backtest_run_repository,
            report_builder=freqtrade_report_builder,
            execution_core=factor_signal_execution_core,
            persistence_service=factor_paper_persistence_service,
            database_runtime=database_runtime,
        )
        if factor_research_service is not None
        and backtest_run_repository is not None
        and freqtrade_report_builder is not None
        and factor_signal_execution_core is not None
        and factor_paper_persistence_service is not None
        else None
    )
    currency_rate_service = CurrencyRateService() if build_api_runtime else None
    market_scheduler_runtime = (
        MarketSchedulerRuntime(database_runtime=database_runtime)
        if build_background_runtime
        else None
    )

    services = AppRuntimeServices(
        infra=InfraRuntime(
            exchange_gateway=exchange_gateway,
            database_runtime=database_runtime,
            kline_store=kline_store,
            cache_service=cache_service,
        ),
        market=MarketRuntime(
            market_data_service=market_data_service,
            realtime_service=realtime_service,
            market_indicator_repository=market_indicator_repository,
            indicator_service=indicator_service,
            history_service=history_service,
            funding_rate_store=funding_rate_store,
            funding_rate_service=funding_rate_service,
            funding_rate_app_service=funding_rate_app_service,
            crypto_index_service=crypto_index_service,
            market_query_app_service=market_query_app_service,
            market_insight_app_service=market_insight_app_service,
            market_websocket_service=market_websocket_service,
            index_data_service=index_data_service,
            binance_market_snapshot=binance_market_snapshot,
            binance_market_intel=binance_market_intel,
            binance_web3_service=binance_web3_service,
        ),
        tools=ToolsRuntime(
            sentiment_api_client=sentiment_api_client,
            sentiment_repository=sentiment_repository,
            sentiment_service=sentiment_service,
            dca_service=dca_service,
            pair_compare_service=pair_compare_service,
            tools_app_service=tools_app_service,
        ),
        backtest=BacktestRuntime(
            backtest_run_repository=backtest_run_repository,
            freqtrade_backtest_service=freqtrade_backtest_service,
            backtest_run_service=backtest_run_service,
            strategy_query_service=strategy_query_service,
            strategy_write_service=strategy_write_service,
            freqtrade_report_builder=freqtrade_report_builder,
            paper_run_manager=paper_run_manager,
            backtest_command_service=backtest_command_service,
            backtest_query_service=backtest_query_service,
        ),
        factors=FactorRuntime(
            factor_research_repository=factor_research_repository,
            factor_research_service=factor_research_service,
            factor_execution_service=factor_execution_service,
            factor_signal_execution_core=factor_signal_execution_core,
            factor_paper_persistence_service=factor_paper_persistence_service,
            factor_paper_run_manager=factor_paper_run_manager,
        ),
        system=SystemRuntime(
            currency_rate_service=currency_rate_service,
            market_scheduler_runtime=market_scheduler_runtime,
        ),
    )
    services.validate_required_services(runtime_role)
    return services
