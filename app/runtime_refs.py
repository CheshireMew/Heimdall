from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RuntimeServiceRef:
    section: str
    name: str

    @property
    def key(self) -> str:
        return f"{self.section}.{self.name}"


INFRA_EXCHANGE_GATEWAY = RuntimeServiceRef("infra", "exchange_gateway")
INFRA_DATABASE_RUNTIME = RuntimeServiceRef("infra", "database_runtime")
INFRA_KLINE_STORE = RuntimeServiceRef("infra", "kline_store")
INFRA_CACHE_SERVICE = RuntimeServiceRef("infra", "cache_service")

MARKET_MARKET_DATA_SERVICE = RuntimeServiceRef("market", "market_data_service")
MARKET_REALTIME_SERVICE = RuntimeServiceRef("market", "realtime_service")
MARKET_INDICATOR_REPOSITORY = RuntimeServiceRef("market", "market_indicator_repository")
MARKET_INDICATOR_SERVICE = RuntimeServiceRef("market", "indicator_service")
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
