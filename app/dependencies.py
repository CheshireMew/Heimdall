from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from starlette.requests import HTTPConnection

from app.runtime import AppRuntimeServices
from config import settings

if TYPE_CHECKING:
    from app.services.backtest.command_service import BacktestCommandService
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


def _get_runtime_services(connection: HTTPConnection) -> AppRuntimeServices:
    runtime_services = getattr(connection.app.state, "runtime_services", None)
    if runtime_services is None:
        raise RuntimeError("App runtime services are not initialized")
    return cast(AppRuntimeServices, runtime_services)


def _require_runtime_service(connection: HTTPConnection, name: str) -> Any:
    runtime_services = _get_runtime_services(connection)
    service = getattr(runtime_services, name, None)
    if service is None:
        raise RuntimeError(f"Runtime service is not initialized: {name}")
    return service


def get_exchange_gateway(connection: HTTPConnection) -> ExchangeGateway:
    return _require_runtime_service(connection, "exchange_gateway")


def get_kline_store(connection: HTTPConnection) -> KlineStore:
    return _require_runtime_service(connection, "kline_store")


def get_market_data_service(connection: HTTPConnection) -> MarketDataService:
    return _require_runtime_service(connection, "market_data_service")


def get_realtime_service(connection: HTTPConnection) -> RealtimeService:
    return _require_runtime_service(connection, "realtime_service")


def get_market_indicator_repository(connection: HTTPConnection) -> MarketIndicatorRepository:
    return _require_runtime_service(connection, "market_indicator_repository")


def get_indicator_service(connection: HTTPConnection) -> IndicatorService:
    return _require_runtime_service(connection, "indicator_service")


def get_history_service(connection: HTTPConnection) -> HistoryService:
    return _require_runtime_service(connection, "history_service")


def get_funding_rate_store(connection: HTTPConnection) -> FundingRateStore:
    return _require_runtime_service(connection, "funding_rate_store")


def get_funding_rate_service(connection: HTTPConnection) -> FundingRateService:
    return _require_runtime_service(connection, "funding_rate_service")


def get_funding_rate_app_service(connection: HTTPConnection) -> FundingRateAppService:
    return _require_runtime_service(connection, "funding_rate_app_service")


def get_crypto_index_service(connection: HTTPConnection) -> CryptoIndexService:
    return _require_runtime_service(connection, "crypto_index_service")


def get_market_query_app_service(connection: HTTPConnection) -> MarketQueryAppService:
    return _require_runtime_service(connection, "market_query_app_service")


def get_market_insight_app_service(connection: HTTPConnection) -> MarketInsightAppService:
    return _require_runtime_service(connection, "market_insight_app_service")


def get_index_data_service(connection: HTTPConnection) -> IndexDataService:
    return _require_runtime_service(connection, "index_data_service")


def get_binance_market_snapshot_service(connection: HTTPConnection) -> BinanceMarketSnapshotService:
    return _require_runtime_service(connection, "binance_market_snapshot")


def get_binance_market_intel_service(connection: HTTPConnection) -> BinanceMarketIntelService:
    return _require_runtime_service(connection, "binance_market_intel")


def get_binance_web3_service(connection: HTTPConnection) -> BinanceWeb3Service:
    return _require_runtime_service(connection, "binance_web3_service")


def get_sentiment_api_client(connection: HTTPConnection) -> SentimentApiClient:
    return _require_runtime_service(connection, "sentiment_api_client")


def get_sentiment_repository(connection: HTTPConnection) -> SentimentRepository:
    return _require_runtime_service(connection, "sentiment_repository")


def get_sentiment_service(connection: HTTPConnection) -> SentimentService:
    return _require_runtime_service(connection, "sentiment_service")


def get_dca_service(connection: HTTPConnection) -> DCAService:
    return _require_runtime_service(connection, "dca_service")


def get_pair_compare_service(connection: HTTPConnection) -> PairCompareService:
    return _require_runtime_service(connection, "pair_compare_service")


def get_tools_app_service(connection: HTTPConnection) -> ToolsAppService:
    return _require_runtime_service(connection, "tools_app_service")


def get_backtest_run_repository(connection: HTTPConnection) -> BacktestRunRepository:
    return _require_runtime_service(connection, "backtest_run_repository")


def get_freqtrade_backtest_service(connection: HTTPConnection) -> FreqtradeBacktestService:
    return _require_runtime_service(connection, "freqtrade_backtest_service")


def get_backtest_run_service(connection: HTTPConnection) -> BacktestRunService:
    return _require_runtime_service(connection, "backtest_run_service")


def get_strategy_query_service(connection: HTTPConnection) -> StrategyQueryService:
    return _require_runtime_service(connection, "strategy_query_service")


def get_strategy_write_service(connection: HTTPConnection) -> StrategyWriteService:
    return _require_runtime_service(connection, "strategy_write_service")


def get_freqtrade_report_builder(connection: HTTPConnection):
    return _require_runtime_service(connection, "freqtrade_report_builder")


def get_paper_run_manager(connection: HTTPConnection) -> PaperRunManager:
    return _require_runtime_service(connection, "paper_run_manager")


def get_backtest_command_service(connection: HTTPConnection) -> BacktestCommandService:
    return _require_runtime_service(connection, "backtest_command_service")


def get_backtest_query_service(connection: HTTPConnection) -> BacktestQueryService:
    return _require_runtime_service(connection, "backtest_query_service")


def get_factor_research_repository(connection: HTTPConnection) -> FactorResearchRepository:
    return _require_runtime_service(connection, "factor_research_repository")


def get_factor_research_service(connection: HTTPConnection) -> FactorResearchService:
    return _require_runtime_service(connection, "factor_research_service")


def get_factor_execution_service(connection: HTTPConnection) -> FactorExecutionService:
    return _require_runtime_service(connection, "factor_execution_service")


def get_factor_signal_execution_core(connection: HTTPConnection) -> FactorSignalExecutionCore:
    return _require_runtime_service(connection, "factor_signal_execution_core")


def get_factor_paper_persistence_service(connection: HTTPConnection) -> FactorPaperPersistenceService:
    return _require_runtime_service(connection, "factor_paper_persistence_service")


def get_factor_paper_run_manager(connection: HTTPConnection) -> FactorPaperRunManager:
    return _require_runtime_service(connection, "factor_paper_run_manager")


def get_currency_rate_service(connection: HTTPConnection) -> CurrencyRateService:
    return _require_runtime_service(connection, "currency_rate_service")


def get_settings():
    return settings
