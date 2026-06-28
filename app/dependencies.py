from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, cast

from starlette.requests import HTTPConnection

from app.runtime import AppRuntimeServices

TService = TypeVar("TService")

if TYPE_CHECKING:
    from app.infra.db.database import DatabaseRuntime
    from app.services.currency_service import CurrencyRateService
    from app.services.fred_api_config_service import FredApiConfigService
    from app.services.llm_config_service import LlmConfigService
    from app.services.market.binance_market_intel_service import BinanceMarketIntelService
    from app.services.market.binance_web3_heat_rank_service import BinanceWeb3HeatRankService
    from app.services.market.binance_web3_rank_gateway import BinanceWeb3RankGateway
    from app.services.market.binance_web3_tokens import BinanceWeb3TokenService
    from app.services.market.index_data_service import IndexDataService
    from app.services.market.insight_app_service import MarketInsightAppService
    from app.services.market.query_app_service import MarketQueryAppService
    from app.services.market.websocket_service import MarketWebSocketService
    from app.services.tools.app_service import ToolsAppService


def get_runtime_services(connection: HTTPConnection) -> AppRuntimeServices:
    runtime_services = getattr(connection.app.state, "runtime_services", None)
    if runtime_services is None:
        raise RuntimeError("App runtime services are not initialized")
    return cast(AppRuntimeServices, runtime_services)


def _required_service(connection: HTTPConnection, name: str) -> TService:
    return cast(TService, get_runtime_services(connection).require(name))


def get_database_runtime(connection: HTTPConnection) -> "DatabaseRuntime":
    return _required_service(connection, "database_runtime")


def get_currency_rate_service(connection: HTTPConnection) -> "CurrencyRateService":
    return _required_service(connection, "currency_rate_service")


def get_llm_config_service(connection: HTTPConnection) -> "LlmConfigService":
    return _required_service(connection, "llm_config_service")


def get_fred_api_config_service(connection: HTTPConnection) -> "FredApiConfigService":
    return _required_service(connection, "fred_api_config_service")


def get_tools_app_service(connection: HTTPConnection) -> "ToolsAppService":
    return _required_service(connection, "tools_app_service")


def get_market_query_service(connection: HTTPConnection) -> "MarketQueryAppService":
    return _required_service(connection, "market_query_service")


def get_market_insight_service(connection: HTTPConnection) -> "MarketInsightAppService":
    return _required_service(connection, "market_insight_service")


def get_market_websocket_service(connection: HTTPConnection) -> "MarketWebSocketService":
    return _required_service(connection, "market_websocket_service")


def get_index_data_service(connection: HTTPConnection) -> "IndexDataService":
    return _required_service(connection, "index_data_service")


def get_binance_market_intel_service(connection: HTTPConnection) -> "BinanceMarketIntelService":
    return _required_service(connection, "binance_market_intel")


def get_binance_web3_rank_gateway(connection: HTTPConnection) -> "BinanceWeb3RankGateway":
    return _required_service(connection, "binance_web3_ranks")


def get_binance_web3_heat_rank_service(connection: HTTPConnection) -> "BinanceWeb3HeatRankService":
    return _required_service(connection, "binance_web3_heat_ranks")


def get_binance_web3_token_service(connection: HTTPConnection) -> "BinanceWeb3TokenService":
    return _required_service(connection, "binance_web3_tokens")
