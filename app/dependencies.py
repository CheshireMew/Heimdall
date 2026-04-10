from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from config import settings

if TYPE_CHECKING:
    from app.services.backtest.command_service import BacktestCommandService
    from app.services.backtest.freqtrade_service import FreqtradeBacktestService
    from app.services.backtest.paper_manager import PaperRunManager
    from app.services.backtest.paper_persistence_service import PaperPersistenceService
    from app.services.backtest.paper_position_service import PaperPositionService
    from app.services.backtest.paper_runtime_service import PaperRuntimeService
    from app.services.backtest.query_service import BacktestQueryService
    from app.services.backtest.run_repository import BacktestRunRepository
    from app.services.backtest.run_service import BacktestRunService
    from app.services.backtest.strategy_runtime import StrategyRuntime
    from app.services.backtest.strategy_query_service import StrategyQueryService
    from app.services.backtest.strategy_write_service import StrategyWriteService
    from app.services.factors.execution import FactorExecutionService
    from app.services.factors.paper_manager import FactorPaperRunManager
    from app.services.factors.paper_persistence_service import FactorPaperPersistenceService
    from app.services.factors.repository import FactorResearchRepository
    from app.services.factors.signal_execution_core import FactorSignalExecutionCore
    from app.services.factors.service import FactorResearchService
    from app.services.market.app_service import MarketAppService
    from app.services.market.crypto_index_app_service import CryptoIndexAppService
    from app.services.market.exchange_gateway import ExchangeGateway
    from app.services.market.funding_rate_service import FundingRateService
    from app.services.market.funding_rate_store import FundingRateStore
    from app.services.market.history_service import HistoryService
    from app.services.market.indicator_service import IndicatorService
    from app.services.market.indicator_repository import MarketIndicatorRepository
    from app.services.market.kline_store import KlineStore
    from app.services.market.market_data_service import MarketDataService
    from app.services.market.realtime_service import RealtimeService
    from app.services.sentiment_client import SentimentApiClient
    from app.services.sentiment_repository import SentimentRepository
    from app.services.sentiment_service import SentimentService
    from app.services.tools.app_service import ToolsAppService
    from app.services.tools.dca_service import DCAService
    from app.services.tools.pair_compare_service import PairCompareService


@lru_cache(maxsize=1)
def get_exchange_gateway() -> ExchangeGateway:
    from app.services.market.exchange_gateway import ExchangeGateway

    return ExchangeGateway(exchange_id=settings.EXCHANGE_ID)


@lru_cache(maxsize=1)
def get_kline_store() -> KlineStore:
    from app.services.market.kline_store import KlineStore

    return KlineStore()


@lru_cache(maxsize=1)
def get_market_data_service() -> MarketDataService:
    """Get or create the unified market data service."""
    from app.services.market.market_data_service import MarketDataService

    return MarketDataService(
        exchange_gateway=get_exchange_gateway(),
        kline_store=get_kline_store(),
    )


@lru_cache(maxsize=1)
def get_crypto_index_service() -> CryptoIndexAppService:
    """Get or create a singleton crypto index application service."""
    from app.services.market.crypto_index_app_service import CryptoIndexAppService
    from app.services.market.crypto_index_service import CryptoIndexService

    return CryptoIndexAppService(CryptoIndexService())


@lru_cache(maxsize=1)
def get_realtime_service() -> RealtimeService:
    from app.services.market.realtime_service import RealtimeService

    return RealtimeService()


@lru_cache(maxsize=1)
def get_indicator_service() -> IndicatorService:
    from app.services.market.indicator_service import IndicatorService

    return IndicatorService(repository=get_market_indicator_repository())


@lru_cache(maxsize=1)
def get_history_service() -> HistoryService:
    from app.services.market.history_service import HistoryService

    return HistoryService()


@lru_cache(maxsize=1)
def get_funding_rate_service() -> FundingRateService:
    from app.services.market.funding_rate_service import FundingRateService

    return FundingRateService(store=get_funding_rate_store())


@lru_cache(maxsize=1)
def get_market_app_service() -> MarketAppService:
    from app.services.market.app_service import MarketAppService

    return MarketAppService(
        crypto_index_service=get_crypto_index_service(),
        realtime_service=get_realtime_service(),
        indicator_service=get_indicator_service(),
        history_service=get_history_service(),
        funding_rate_service=get_funding_rate_service(),
    )


@lru_cache(maxsize=1)
def get_backtest_run_repository() -> BacktestRunRepository:
    from app.services.backtest.run_repository import BacktestRunRepository

    return BacktestRunRepository()


@lru_cache(maxsize=1)
def get_freqtrade_backtest_service() -> FreqtradeBacktestService:
    from app.services.backtest.freqtrade_service import FreqtradeBacktestService

    return FreqtradeBacktestService(market_data_service=get_market_data_service())


@lru_cache(maxsize=1)
def get_backtest_run_service() -> BacktestRunService:
    from app.services.backtest.run_service import BacktestRunService

    return BacktestRunService(engine=get_freqtrade_backtest_service())


@lru_cache(maxsize=1)
def get_strategy_query_service() -> StrategyQueryService:
    from app.services.backtest.strategy_query_service import StrategyQueryService

    return StrategyQueryService()


@lru_cache(maxsize=1)
def get_strategy_write_service() -> StrategyWriteService:
    from app.services.backtest.strategy_write_service import StrategyWriteService

    return StrategyWriteService()


@lru_cache(maxsize=1)
def get_backtest_command_service() -> BacktestCommandService:
    from app.services.backtest.command_service import BacktestCommandService

    return BacktestCommandService(
        run_service=get_backtest_run_service(),
        paper_manager=get_paper_run_manager(),
        run_repository=get_backtest_run_repository(),
        strategy_query_service=get_strategy_query_service(),
        strategy_write_service=get_strategy_write_service(),
    )


@lru_cache(maxsize=1)
def get_backtest_query_service() -> BacktestQueryService:
    from app.services.backtest.query_service import BacktestQueryService

    return BacktestQueryService(
        run_repository=get_backtest_run_repository(),
        strategy_query_service=get_strategy_query_service(),
    )


@lru_cache(maxsize=1)
def get_strategy_runtime() -> StrategyRuntime:
    from app.services.backtest.strategy_runtime import StrategyRuntime

    return StrategyRuntime()


@lru_cache(maxsize=1)
def get_freqtrade_report_builder():
    from app.services.backtest.freqtrade_report_builder import FreqtradeReportBuilder

    return FreqtradeReportBuilder()


@lru_cache(maxsize=1)
def get_paper_position_service() -> PaperPositionService:
    from app.services.backtest.paper_position_service import PaperPositionService

    return PaperPositionService()


@lru_cache(maxsize=1)
def get_paper_runtime_service() -> PaperRuntimeService:
    from app.services.backtest.paper_runtime_service import PaperRuntimeService

    return PaperRuntimeService(
        market_data_service=get_market_data_service(),
        runtime=get_strategy_runtime(),
    )


@lru_cache(maxsize=1)
def get_paper_persistence_service() -> PaperPersistenceService:
    from app.services.backtest.paper_persistence_service import PaperPersistenceService

    return PaperPersistenceService(
        report_builder=get_freqtrade_report_builder(),
        position_service=get_paper_position_service(),
    )


@lru_cache(maxsize=1)
def get_paper_run_manager() -> PaperRunManager:
    from app.services.backtest.paper_manager import PaperRunManager

    return PaperRunManager(
        strategy_query_service=get_strategy_query_service(),
        runtime=get_strategy_runtime(),
        report_builder=get_freqtrade_report_builder(),
        position_service=get_paper_position_service(),
        persistence_service=get_paper_persistence_service(),
        runtime_service=get_paper_runtime_service(),
        run_repository=get_backtest_run_repository(),
    )


@lru_cache(maxsize=1)
def get_sentiment_service() -> SentimentService:
    from app.services.sentiment_service import SentimentService

    return SentimentService(
        client=get_sentiment_api_client(),
        repository=get_sentiment_repository(),
    )


@lru_cache(maxsize=1)
def get_dca_service() -> DCAService:
    from app.services.tools.dca_service import DCAService

    return DCAService(
        market_data_service=get_market_data_service(),
        sentiment_service=get_sentiment_service(),
    )


@lru_cache(maxsize=1)
def get_pair_compare_service() -> PairCompareService:
    from app.services.tools.pair_compare_service import PairCompareService

    return PairCompareService(market_data_service=get_market_data_service())


@lru_cache(maxsize=1)
def get_tools_app_service() -> ToolsAppService:
    from app.services.tools.app_service import ToolsAppService

    return ToolsAppService(
        dca_service=get_dca_service(),
        pair_compare_service=get_pair_compare_service(),
    )


@lru_cache(maxsize=1)
def get_factor_research_service() -> FactorResearchService:
    from app.services.factors.service import FactorResearchService

    return FactorResearchService(
        market_data_service=get_market_data_service(),
        indicator_repository=get_market_indicator_repository(),
        repository=get_factor_research_repository(),
    )


@lru_cache(maxsize=1)
def get_factor_execution_service() -> FactorExecutionService:
    from app.services.factors.execution import FactorExecutionService

    return FactorExecutionService(
        factor_service=get_factor_research_service(),
        report_builder=get_freqtrade_report_builder(),
        execution_core=get_factor_signal_execution_core(),
    )


@lru_cache(maxsize=1)
def get_factor_signal_execution_core() -> FactorSignalExecutionCore:
    from app.services.factors.signal_execution_core import FactorSignalExecutionCore

    return FactorSignalExecutionCore()


@lru_cache(maxsize=1)
def get_market_indicator_repository() -> MarketIndicatorRepository:
    from app.services.market.indicator_repository import MarketIndicatorRepository

    return MarketIndicatorRepository()


@lru_cache(maxsize=1)
def get_funding_rate_store() -> FundingRateStore:
    from app.services.market.funding_rate_store import FundingRateStore

    return FundingRateStore()


@lru_cache(maxsize=1)
def get_sentiment_api_client() -> SentimentApiClient:
    from app.services.sentiment_client import SentimentApiClient

    return SentimentApiClient(settings.SENTIMENT_API_URL)


@lru_cache(maxsize=1)
def get_sentiment_repository() -> SentimentRepository:
    from app.services.sentiment_repository import SentimentRepository

    return SentimentRepository()


@lru_cache(maxsize=1)
def get_factor_research_repository() -> FactorResearchRepository:
    from app.services.factors.repository import FactorResearchRepository

    return FactorResearchRepository()


@lru_cache(maxsize=1)
def get_factor_paper_persistence_service() -> FactorPaperPersistenceService:
    from app.services.factors.paper_persistence_service import FactorPaperPersistenceService

    return FactorPaperPersistenceService(
        report_builder=get_freqtrade_report_builder(),
        execution_core=get_factor_signal_execution_core(),
    )


@lru_cache(maxsize=1)
def get_factor_paper_run_manager() -> FactorPaperRunManager:
    from app.services.factors.paper_manager import FactorPaperRunManager

    return FactorPaperRunManager(
        factor_service=get_factor_research_service(),
        report_builder=get_freqtrade_report_builder(),
        execution_core=get_factor_signal_execution_core(),
        persistence_service=get_factor_paper_persistence_service(),
        run_repository=get_backtest_run_repository(),
    )


def get_settings():
    """
    Return the global settings object.
    Useful for overriding settings in tests.
    """
    return settings
