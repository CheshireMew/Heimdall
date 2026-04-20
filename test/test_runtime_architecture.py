from __future__ import annotations

import pytest

from app.runtime import (
    AppRuntimeServices,
    BacktestRuntime,
    FactorRuntime,
    InfraRuntime,
    MarketRuntime,
    SystemRuntime,
    ToolsRuntime,
)


def make_background_runtime_services() -> AppRuntimeServices:
    return AppRuntimeServices(
        infra=InfraRuntime(
            exchange_gateway=object(),
            database_runtime=object(),
            kline_store=object(),
            cache_service=object(),
        ),
        market=MarketRuntime(
            market_data_service=object(),
            market_indicator_repository=object(),
            binance_market_snapshot=object(),
            binance_market_intel=object(),
        ),
        tools=ToolsRuntime(),
        backtest=BacktestRuntime(
            backtest_run_repository=object(),
            freqtrade_backtest_service=object(),
            strategy_query_service=object(),
            freqtrade_report_builder=object(),
            paper_run_manager=object(),
        ),
        factors=FactorRuntime(
            factor_research_repository=object(),
            factor_research_service=object(),
            factor_signal_execution_core=object(),
            factor_paper_persistence_service=object(),
            factor_paper_run_manager=object(),
        ),
        system=SystemRuntime(market_scheduler_runtime=object()),
    )


def make_api_runtime_services() -> AppRuntimeServices:
    return AppRuntimeServices(
        infra=InfraRuntime(
            exchange_gateway=object(),
            database_runtime=object(),
            kline_store=object(),
            cache_service=object(),
        ),
        market=MarketRuntime(
            market_data_service=object(),
            realtime_service=object(),
            market_indicator_repository=object(),
            indicator_service=object(),
            history_service=object(),
            funding_rate_store=object(),
            funding_rate_service=object(),
            funding_rate_app_service=object(),
            crypto_index_service=object(),
            market_query_app_service=object(),
            market_insight_app_service=object(),
            market_websocket_service=object(),
            index_data_service=object(),
            binance_market_intel=object(),
            binance_web3_service=object(),
        ),
        tools=ToolsRuntime(
            sentiment_api_client=object(),
            sentiment_repository=object(),
            sentiment_service=object(),
            dca_service=object(),
            pair_compare_service=object(),
            tools_app_service=object(),
        ),
        backtest=BacktestRuntime(
            backtest_run_repository=object(),
            freqtrade_backtest_service=object(),
            backtest_run_service=object(),
            strategy_query_service=object(),
            strategy_write_service=object(),
            freqtrade_report_builder=object(),
            paper_run_manager=object(),
            backtest_command_service=object(),
            backtest_query_service=object(),
        ),
        factors=FactorRuntime(
            factor_research_repository=object(),
            factor_research_service=object(),
            factor_execution_service=object(),
            factor_signal_execution_core=object(),
            factor_paper_persistence_service=object(),
            factor_paper_run_manager=object(),
        ),
        system=SystemRuntime(currency_rate_service=object()),
    )


def test_background_role_validation_ignores_api_only_graph():
    services = make_background_runtime_services()

    services.validate_required_services("background")
    with pytest.raises(RuntimeError, match="market.realtime_service"):
        services.validate_required_services("api")


def test_api_role_validation_ignores_background_only_graph():
    services = make_api_runtime_services()

    services.validate_required_services("api")
    with pytest.raises(RuntimeError, match="market.binance_market_snapshot"):
        services.validate_required_services("background")
