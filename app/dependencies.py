from functools import lru_cache
from config import settings
from app.services.backtest.command_service import BacktestCommandService
from app.services.backtest.paper_manager import PaperRunManager
from app.services.backtest.query_service import BacktestQueryService
from app.services.market.exchange_gateway import ExchangeGateway
from app.services.market.kline_store import KlineStore
from app.services.market.app_service import MarketAppService
from app.services.market.market_data_service import MarketDataService
from app.services.market.crypto_index_service import CryptoIndexService
from app.services.market.crypto_index_app_service import CryptoIndexAppService
from app.services.tools.app_service import ToolsAppService

@lru_cache(maxsize=1)
def get_market_data_service() -> MarketDataService:
    """Get or create the unified market data service."""
    return MarketDataService(
        exchange_gateway=ExchangeGateway(exchange_id=settings.EXCHANGE_ID),
        kline_store=KlineStore(),
    )

@lru_cache(maxsize=1)
def get_crypto_index_service() -> CryptoIndexAppService:
    """
    Get or create a singleton crypto index application service.
    """
    return CryptoIndexAppService(CryptoIndexService())


@lru_cache(maxsize=1)
def get_market_app_service() -> MarketAppService:
    return MarketAppService(crypto_index_service=get_crypto_index_service())


@lru_cache(maxsize=1)
def get_backtest_command_service() -> BacktestCommandService:
    return BacktestCommandService(
        market_data_service=get_market_data_service(),
        paper_manager=get_paper_run_manager(),
    )


@lru_cache(maxsize=1)
def get_backtest_query_service() -> BacktestQueryService:
    return BacktestQueryService()


@lru_cache(maxsize=1)
def get_paper_run_manager() -> PaperRunManager:
    return PaperRunManager(market_data_service=get_market_data_service())


@lru_cache(maxsize=1)
def get_tools_app_service() -> ToolsAppService:
    return ToolsAppService(market_data_service=get_market_data_service())

def get_settings():
    """
    Return the global settings object.
    Useful for overriding settings in tests.
    """
    return settings
