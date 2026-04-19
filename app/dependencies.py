from __future__ import annotations

from typing import TYPE_CHECKING, cast

from starlette.requests import HTTPConnection

from app.runtime import (
    AppRuntimeServices,
    BacktestRuntime,
    FactorRuntime,
    InfraRuntime,
    MarketRuntime,
    SystemRuntime,
    ToolsRuntime,
)
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
    from app.services.market.websocket_service import MarketWebSocketService
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


def _require_runtime_service(service, label: str):
    if service is None:
        raise RuntimeError(f"Runtime service is not initialized: {label}")
    return service


def _get_infra_runtime(connection: HTTPConnection) -> InfraRuntime:
    return _get_runtime_services(connection).infra


def _get_market_runtime(connection: HTTPConnection) -> MarketRuntime:
    return _get_runtime_services(connection).market


def _get_tools_runtime(connection: HTTPConnection) -> ToolsRuntime:
    return _get_runtime_services(connection).tools


def _get_backtest_runtime(connection: HTTPConnection) -> BacktestRuntime:
    return _get_runtime_services(connection).backtest


def _get_factor_runtime(connection: HTTPConnection) -> FactorRuntime:
    return _get_runtime_services(connection).factors


def _get_system_runtime(connection: HTTPConnection) -> SystemRuntime:
    return _get_runtime_services(connection).system


def get_exchange_gateway(connection: HTTPConnection) -> ExchangeGateway:
    runtime = _get_infra_runtime(connection)
    return _require_runtime_service(runtime.exchange_gateway, "infra.exchange_gateway")


def get_kline_store(connection: HTTPConnection) -> KlineStore:
    runtime = _get_infra_runtime(connection)
    return _require_runtime_service(runtime.kline_store, "infra.kline_store")


def get_market_data_service(connection: HTTPConnection) -> MarketDataService:
    runtime = _get_market_runtime(connection)
    return _require_runtime_service(runtime.market_data_service, "market.market_data_service")


def get_realtime_service(connection: HTTPConnection) -> RealtimeService:
    runtime = _get_market_runtime(connection)
    return _require_runtime_service(runtime.realtime_service, "market.realtime_service")


def get_market_indicator_repository(connection: HTTPConnection) -> MarketIndicatorRepository:
    runtime = _get_market_runtime(connection)
    return _require_runtime_service(runtime.market_indicator_repository, "market.market_indicator_repository")


def get_indicator_service(connection: HTTPConnection) -> IndicatorService:
    runtime = _get_market_runtime(connection)
    return _require_runtime_service(runtime.indicator_service, "market.indicator_service")


def get_history_service(connection: HTTPConnection) -> HistoryService:
    runtime = _get_market_runtime(connection)
    return _require_runtime_service(runtime.history_service, "market.history_service")


def get_funding_rate_store(connection: HTTPConnection) -> FundingRateStore:
    runtime = _get_market_runtime(connection)
    return _require_runtime_service(runtime.funding_rate_store, "market.funding_rate_store")


def get_funding_rate_service(connection: HTTPConnection) -> FundingRateService:
    runtime = _get_market_runtime(connection)
    return _require_runtime_service(runtime.funding_rate_service, "market.funding_rate_service")


def get_funding_rate_app_service(connection: HTTPConnection) -> FundingRateAppService:
    runtime = _get_market_runtime(connection)
    return _require_runtime_service(runtime.funding_rate_app_service, "market.funding_rate_app_service")


def get_crypto_index_service(connection: HTTPConnection) -> CryptoIndexService:
    runtime = _get_market_runtime(connection)
    return _require_runtime_service(runtime.crypto_index_service, "market.crypto_index_service")


def get_market_query_app_service(connection: HTTPConnection) -> MarketQueryAppService:
    runtime = _get_market_runtime(connection)
    return _require_runtime_service(runtime.market_query_app_service, "market.market_query_app_service")


def get_market_insight_app_service(connection: HTTPConnection) -> MarketInsightAppService:
    runtime = _get_market_runtime(connection)
    return _require_runtime_service(runtime.market_insight_app_service, "market.market_insight_app_service")


def get_market_websocket_service(connection: HTTPConnection) -> MarketWebSocketService:
    runtime = _get_market_runtime(connection)
    return _require_runtime_service(runtime.market_websocket_service, "market.market_websocket_service")


def get_index_data_service(connection: HTTPConnection) -> IndexDataService:
    runtime = _get_market_runtime(connection)
    return _require_runtime_service(runtime.index_data_service, "market.index_data_service")


def get_binance_market_snapshot_service(connection: HTTPConnection) -> BinanceMarketSnapshotService:
    runtime = _get_market_runtime(connection)
    return _require_runtime_service(runtime.binance_market_snapshot, "market.binance_market_snapshot")


def get_binance_market_intel_service(connection: HTTPConnection) -> BinanceMarketIntelService:
    runtime = _get_market_runtime(connection)
    return _require_runtime_service(runtime.binance_market_intel, "market.binance_market_intel")


def get_binance_web3_service(connection: HTTPConnection) -> BinanceWeb3Service:
    runtime = _get_market_runtime(connection)
    return _require_runtime_service(runtime.binance_web3_service, "market.binance_web3_service")


def get_sentiment_api_client(connection: HTTPConnection) -> SentimentApiClient:
    runtime = _get_tools_runtime(connection)
    return _require_runtime_service(runtime.sentiment_api_client, "tools.sentiment_api_client")


def get_sentiment_repository(connection: HTTPConnection) -> SentimentRepository:
    runtime = _get_tools_runtime(connection)
    return _require_runtime_service(runtime.sentiment_repository, "tools.sentiment_repository")


def get_sentiment_service(connection: HTTPConnection) -> SentimentService:
    runtime = _get_tools_runtime(connection)
    return _require_runtime_service(runtime.sentiment_service, "tools.sentiment_service")


def get_dca_service(connection: HTTPConnection) -> DCAService:
    runtime = _get_tools_runtime(connection)
    return _require_runtime_service(runtime.dca_service, "tools.dca_service")


def get_pair_compare_service(connection: HTTPConnection) -> PairCompareService:
    runtime = _get_tools_runtime(connection)
    return _require_runtime_service(runtime.pair_compare_service, "tools.pair_compare_service")


def get_tools_app_service(connection: HTTPConnection) -> ToolsAppService:
    runtime = _get_tools_runtime(connection)
    return _require_runtime_service(runtime.tools_app_service, "tools.tools_app_service")


def get_backtest_run_repository(connection: HTTPConnection) -> BacktestRunRepository:
    runtime = _get_backtest_runtime(connection)
    return _require_runtime_service(runtime.backtest_run_repository, "backtest.backtest_run_repository")


def get_freqtrade_backtest_service(connection: HTTPConnection) -> FreqtradeBacktestService:
    runtime = _get_backtest_runtime(connection)
    return _require_runtime_service(runtime.freqtrade_backtest_service, "backtest.freqtrade_backtest_service")


def get_backtest_run_service(connection: HTTPConnection) -> BacktestRunService:
    runtime = _get_backtest_runtime(connection)
    return _require_runtime_service(runtime.backtest_run_service, "backtest.backtest_run_service")


def get_strategy_query_service(connection: HTTPConnection) -> StrategyQueryService:
    runtime = _get_backtest_runtime(connection)
    return _require_runtime_service(runtime.strategy_query_service, "backtest.strategy_query_service")


def get_strategy_write_service(connection: HTTPConnection) -> StrategyWriteService:
    runtime = _get_backtest_runtime(connection)
    return _require_runtime_service(runtime.strategy_write_service, "backtest.strategy_write_service")


def get_freqtrade_report_builder(connection: HTTPConnection):
    runtime = _get_backtest_runtime(connection)
    return _require_runtime_service(runtime.freqtrade_report_builder, "backtest.freqtrade_report_builder")


def get_paper_run_manager(connection: HTTPConnection) -> PaperRunManager:
    runtime = _get_backtest_runtime(connection)
    return _require_runtime_service(runtime.paper_run_manager, "backtest.paper_run_manager")


def get_backtest_command_service(connection: HTTPConnection) -> BacktestCommandService:
    runtime = _get_backtest_runtime(connection)
    return _require_runtime_service(runtime.backtest_command_service, "backtest.backtest_command_service")


def get_backtest_query_service(connection: HTTPConnection) -> BacktestQueryService:
    runtime = _get_backtest_runtime(connection)
    return _require_runtime_service(runtime.backtest_query_service, "backtest.backtest_query_service")


def get_factor_research_repository(connection: HTTPConnection) -> FactorResearchRepository:
    runtime = _get_factor_runtime(connection)
    return _require_runtime_service(runtime.factor_research_repository, "factors.factor_research_repository")


def get_factor_research_service(connection: HTTPConnection) -> FactorResearchService:
    runtime = _get_factor_runtime(connection)
    return _require_runtime_service(runtime.factor_research_service, "factors.factor_research_service")


def get_factor_execution_service(connection: HTTPConnection) -> FactorExecutionService:
    runtime = _get_factor_runtime(connection)
    return _require_runtime_service(runtime.factor_execution_service, "factors.factor_execution_service")


def get_factor_signal_execution_core(connection: HTTPConnection) -> FactorSignalExecutionCore:
    runtime = _get_factor_runtime(connection)
    return _require_runtime_service(runtime.factor_signal_execution_core, "factors.factor_signal_execution_core")


def get_factor_paper_persistence_service(connection: HTTPConnection) -> FactorPaperPersistenceService:
    runtime = _get_factor_runtime(connection)
    return _require_runtime_service(runtime.factor_paper_persistence_service, "factors.factor_paper_persistence_service")


def get_factor_paper_run_manager(connection: HTTPConnection) -> FactorPaperRunManager:
    runtime = _get_factor_runtime(connection)
    return _require_runtime_service(runtime.factor_paper_run_manager, "factors.factor_paper_run_manager")


def get_currency_rate_service(connection: HTTPConnection) -> CurrencyRateService:
    runtime = _get_system_runtime(connection)
    return _require_runtime_service(runtime.currency_rate_service, "system.currency_rate_service")


def get_settings():
    return settings
