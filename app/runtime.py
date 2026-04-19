from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
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
    from app.services.market.binance_web3_service import BinanceWeb3Service
    from app.services.market.binance_market_intel_service import BinanceMarketIntelService
    from app.services.market.binance_market_snapshot_service import BinanceMarketSnapshotService
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


@dataclass(slots=True)
class AppRuntimeServices:
    exchange_gateway: ExchangeGateway | None = None
    kline_store: KlineStore | None = None
    market_data_service: MarketDataService | None = None
    realtime_service: RealtimeService | None = None
    market_indicator_repository: MarketIndicatorRepository | None = None
    indicator_service: IndicatorService | None = None
    history_service: HistoryService | None = None
    funding_rate_store: FundingRateStore | None = None
    funding_rate_service: FundingRateService | None = None
    funding_rate_app_service: FundingRateAppService | None = None
    crypto_index_service: CryptoIndexService | None = None
    market_query_app_service: MarketQueryAppService | None = None
    market_insight_app_service: MarketInsightAppService | None = None
    index_data_service: IndexDataService | None = None
    binance_market_snapshot: BinanceMarketSnapshotService | None = None
    binance_market_intel: BinanceMarketIntelService | None = None
    binance_web3_service: BinanceWeb3Service | None = None
    sentiment_api_client: SentimentApiClient | None = None
    sentiment_repository: SentimentRepository | None = None
    sentiment_service: SentimentService | None = None
    dca_service: DCAService | None = None
    pair_compare_service: PairCompareService | None = None
    tools_app_service: ToolsAppService | None = None
    backtest_run_repository: BacktestRunRepository | None = None
    freqtrade_backtest_service: FreqtradeBacktestService | None = None
    backtest_run_service: BacktestRunService | None = None
    strategy_query_service: StrategyQueryService | None = None
    strategy_write_service: StrategyWriteService | None = None
    freqtrade_report_builder: FreqtradeReportBuilder | None = None
    paper_run_manager: PaperRunManager | None = None
    backtest_command_service: BacktestCommandService | None = None
    backtest_query_service: BacktestQueryService | None = None
    factor_research_repository: FactorResearchRepository | None = None
    factor_research_service: FactorResearchService | None = None
    factor_execution_service: FactorExecutionService | None = None
    factor_signal_execution_core: FactorSignalExecutionCore | None = None
    factor_paper_persistence_service: FactorPaperPersistenceService | None = None
    factor_paper_run_manager: FactorPaperRunManager | None = None
    currency_rate_service: CurrencyRateService | None = None
    market_scheduler: Any | None = None
