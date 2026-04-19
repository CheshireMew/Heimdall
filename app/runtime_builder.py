from __future__ import annotations

from app.runtime import AppRuntimeServices
from config import settings


def build_app_runtime_services() -> AppRuntimeServices:
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
    from app.services.sentiment_client import SentimentApiClient
    from app.services.sentiment_repository import SentimentRepository
    from app.services.sentiment_service import SentimentService
    from app.services.tools.app_service import ToolsAppService
    from app.services.tools.dca_service import DCAService
    from app.services.tools.pair_compare_service import PairCompareService

    exchange_gateway = ExchangeGateway(exchange_id=settings.EXCHANGE_ID)
    kline_store = KlineStore()
    market_data_service = MarketDataService(
        exchange_gateway=exchange_gateway,
        kline_store=kline_store,
    )
    realtime_service = RealtimeService()
    market_indicator_repository = MarketIndicatorRepository()
    indicator_service = IndicatorService(repository=market_indicator_repository)
    history_service = HistoryService()
    funding_rate_store = FundingRateStore()
    funding_rate_service = FundingRateService(store=funding_rate_store)
    funding_rate_app_service = FundingRateAppService(funding_rate_service=funding_rate_service)
    crypto_index_service = CryptoIndexService()
    binance_market_snapshot = BinanceMarketSnapshotService()
    market_query_app_service = MarketQueryAppService(
        realtime_service=realtime_service,
        history_service=history_service,
        binance_snapshot_service=binance_market_snapshot,
    )
    market_insight_app_service = MarketInsightAppService(
        indicator_service=indicator_service,
        crypto_index_service=crypto_index_service,
        market_query_service=market_query_app_service,
    )
    index_data_service = IndexDataService(kline_store=kline_store)
    binance_market_intel = BinanceMarketIntelService(snapshot_service=binance_market_snapshot)
    binance_web3_service = BinanceWeb3Service()
    backtest_run_repository = BacktestRunRepository()
    freqtrade_backtest_service = FreqtradeBacktestService(market_data_service=market_data_service)
    backtest_run_service = BacktestRunService(execution_engine=freqtrade_backtest_service)
    strategy_query_service = StrategyQueryService()
    strategy_write_service = StrategyWriteService()
    freqtrade_report_builder = FreqtradeReportBuilder()
    paper_run_manager = PaperRunManager(
        strategy_query_service=strategy_query_service,
        freqtrade_service=freqtrade_backtest_service,
        report_builder=freqtrade_report_builder,
        run_repository=backtest_run_repository,
    )
    backtest_command_service = BacktestCommandService(
        run_service=backtest_run_service,
        paper_manager=paper_run_manager,
        run_repository=backtest_run_repository,
        strategy_query_service=strategy_query_service,
        strategy_write_service=strategy_write_service,
    )
    backtest_query_service = BacktestQueryService(
        run_repository=backtest_run_repository,
        strategy_query_service=strategy_query_service,
    )
    sentiment_api_client = SentimentApiClient(settings.SENTIMENT_API_URL)
    sentiment_repository = SentimentRepository()
    sentiment_service = SentimentService(
        client=sentiment_api_client,
        repository=sentiment_repository,
    )
    dca_service = DCAService(
        market_data_service=market_data_service,
        sentiment_service=sentiment_service,
        index_data_service=index_data_service,
    )
    pair_compare_service = PairCompareService(
        market_data_service=market_data_service,
        index_data_service=index_data_service,
    )
    tools_app_service = ToolsAppService(
        dca_service=dca_service,
        pair_compare_service=pair_compare_service,
    )
    factor_research_repository = FactorResearchRepository()
    factor_research_service = FactorResearchService(
        market_data_service=market_data_service,
        indicator_repository=market_indicator_repository,
        repository=factor_research_repository,
    )
    factor_signal_execution_core = FactorSignalExecutionCore()
    factor_execution_service = FactorExecutionService(
        factor_service=factor_research_service,
        report_builder=freqtrade_report_builder,
        execution_core=factor_signal_execution_core,
    )
    factor_paper_persistence_service = FactorPaperPersistenceService(
        report_builder=freqtrade_report_builder,
        execution_core=factor_signal_execution_core,
    )
    factor_paper_run_manager = FactorPaperRunManager(
        factor_service=factor_research_service,
        run_repository=backtest_run_repository,
        report_builder=freqtrade_report_builder,
        execution_core=factor_signal_execution_core,
        persistence_service=factor_paper_persistence_service,
    )
    currency_rate_service = CurrencyRateService()

    return AppRuntimeServices(
        exchange_gateway=exchange_gateway,
        kline_store=kline_store,
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
        index_data_service=index_data_service,
        binance_market_snapshot=binance_market_snapshot,
        binance_market_intel=binance_market_intel,
        binance_web3_service=binance_web3_service,
        sentiment_api_client=sentiment_api_client,
        sentiment_repository=sentiment_repository,
        sentiment_service=sentiment_service,
        dca_service=dca_service,
        pair_compare_service=pair_compare_service,
        tools_app_service=tools_app_service,
        backtest_run_repository=backtest_run_repository,
        freqtrade_backtest_service=freqtrade_backtest_service,
        backtest_run_service=backtest_run_service,
        strategy_query_service=strategy_query_service,
        strategy_write_service=strategy_write_service,
        freqtrade_report_builder=freqtrade_report_builder,
        paper_run_manager=paper_run_manager,
        backtest_command_service=backtest_command_service,
        backtest_query_service=backtest_query_service,
        factor_research_repository=factor_research_repository,
        factor_research_service=factor_research_service,
        factor_execution_service=factor_execution_service,
        factor_signal_execution_core=factor_signal_execution_core,
        factor_paper_persistence_service=factor_paper_persistence_service,
        factor_paper_run_manager=factor_paper_run_manager,
        currency_rate_service=currency_rate_service,
    )
