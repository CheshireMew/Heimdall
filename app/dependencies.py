from functools import lru_cache
from config import settings
from app.services.backtest.command_service import BacktestCommandService
from app.services.backtest.freqtrade_service import FreqtradeBacktestService
from app.services.backtest.paper_manager import PaperRunManager
from app.services.backtest.query_service import BacktestQueryService
from app.services.backtest.run_repository import BacktestRunRepository
from app.services.backtest.run_service import BacktestRunService
from app.services.backtest.strategy_query_service import StrategyQueryService
from app.services.backtest.strategy_write_service import StrategyWriteService
from app.services.factors.execution import FactorExecutionService
from app.services.factors.paper_manager import FactorPaperRunManager
from app.services.factors import FactorResearchService
from app.services.market.exchange_gateway import ExchangeGateway
from app.services.market.kline_store import KlineStore
from app.services.market.app_service import MarketAppService
from app.services.market.funding_rate_service import FundingRateService
from app.services.market.history_service import HistoryService
from app.services.market.indicator_service import IndicatorService
from app.services.market.market_data_service import MarketDataService
from app.services.market.crypto_index_service import CryptoIndexService
from app.services.market.crypto_index_app_service import CryptoIndexAppService
from app.services.market.realtime_service import RealtimeService
from app.services.sentiment_service import SentimentService
from app.services.tools.app_service import ToolsAppService
from app.services.tools.dca_service import DCAService
from app.services.tools.pair_compare_service import PairCompareService

@lru_cache(maxsize=1)
def get_exchange_gateway() -> ExchangeGateway:
    return ExchangeGateway(exchange_id=settings.EXCHANGE_ID)


@lru_cache(maxsize=1)
def get_kline_store() -> KlineStore:
    return KlineStore()


@lru_cache(maxsize=1)
def get_market_data_service() -> MarketDataService:
    """Get or create the unified market data service."""
    return MarketDataService(
        exchange_gateway=get_exchange_gateway(),
        kline_store=get_kline_store(),
    )

@lru_cache(maxsize=1)
def get_crypto_index_service() -> CryptoIndexAppService:
    """
    Get or create a singleton crypto index application service.
    """
    return CryptoIndexAppService(CryptoIndexService())


@lru_cache(maxsize=1)
def get_realtime_service() -> RealtimeService:
    return RealtimeService()


@lru_cache(maxsize=1)
def get_indicator_service() -> IndicatorService:
    return IndicatorService()


@lru_cache(maxsize=1)
def get_history_service() -> HistoryService:
    return HistoryService()


@lru_cache(maxsize=1)
def get_funding_rate_service() -> FundingRateService:
    return FundingRateService()


@lru_cache(maxsize=1)
def get_market_app_service() -> MarketAppService:
    return MarketAppService(
        crypto_index_service=get_crypto_index_service(),
        realtime_service=get_realtime_service(),
        indicator_service=get_indicator_service(),
        history_service=get_history_service(),
        funding_rate_service=get_funding_rate_service(),
    )


@lru_cache(maxsize=1)
def get_backtest_run_repository() -> BacktestRunRepository:
    return BacktestRunRepository()


@lru_cache(maxsize=1)
def get_freqtrade_backtest_service() -> FreqtradeBacktestService:
    return FreqtradeBacktestService(market_data_service=get_market_data_service())


@lru_cache(maxsize=1)
def get_backtest_run_service() -> BacktestRunService:
    return BacktestRunService(engine=get_freqtrade_backtest_service())


@lru_cache(maxsize=1)
def get_strategy_query_service() -> StrategyQueryService:
    return StrategyQueryService()


@lru_cache(maxsize=1)
def get_strategy_write_service() -> StrategyWriteService:
    return StrategyWriteService()


@lru_cache(maxsize=1)
def get_backtest_command_service() -> BacktestCommandService:
    return BacktestCommandService(
        run_service=get_backtest_run_service(),
        paper_manager=get_paper_run_manager(),
        run_repository=get_backtest_run_repository(),
        strategy_query_service=get_strategy_query_service(),
        strategy_write_service=get_strategy_write_service(),
    )


@lru_cache(maxsize=1)
def get_backtest_query_service() -> BacktestQueryService:
    return BacktestQueryService(
        run_repository=get_backtest_run_repository(),
        strategy_query_service=get_strategy_query_service(),
    )


@lru_cache(maxsize=1)
def get_paper_run_manager() -> PaperRunManager:
    return PaperRunManager(
        market_data_service=get_market_data_service(),
        run_repository=get_backtest_run_repository(),
        strategy_query_service=get_strategy_query_service(),
    )


@lru_cache(maxsize=1)
def get_sentiment_service() -> SentimentService:
    return SentimentService()


@lru_cache(maxsize=1)
def get_dca_service() -> DCAService:
    return DCAService(
        market_data_service=get_market_data_service(),
        sentiment_service=get_sentiment_service(),
    )


@lru_cache(maxsize=1)
def get_pair_compare_service() -> PairCompareService:
    return PairCompareService(market_data_service=get_market_data_service())


@lru_cache(maxsize=1)
def get_tools_app_service() -> ToolsAppService:
    return ToolsAppService(
        dca_service=get_dca_service(),
        pair_compare_service=get_pair_compare_service(),
    )


@lru_cache(maxsize=1)
def get_factor_research_service() -> FactorResearchService:
    return FactorResearchService(market_data_service=get_market_data_service())


@lru_cache(maxsize=1)
def get_factor_execution_service() -> FactorExecutionService:
    return FactorExecutionService(factor_service=get_factor_research_service())


@lru_cache(maxsize=1)
def get_factor_paper_run_manager() -> FactorPaperRunManager:
    return FactorPaperRunManager(
        factor_service=get_factor_research_service(),
        run_repository=get_backtest_run_repository(),
    )


def get_settings():
    """
    Return the global settings object.
    Useful for overriding settings in tests.
    """
    return settings
