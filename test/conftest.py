"""
Shared pytest fixtures for Heimdall tests.
"""
from contextlib import asynccontextmanager
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import app.main as main_module
from app.dependencies import (
    get_backtest_command_service,
    get_backtest_query_service,
    get_binance_market_intel_service,
    get_binance_web3_service,
    get_currency_rate_service,
    get_factor_execution_service,
    get_factor_paper_run_manager,
    get_funding_rate_app_service,
    get_factor_research_service,
    get_market_data_service,
    get_market_insight_app_service,
    get_market_query_app_service,
    get_tools_app_service,
)
from app.infra.db.schema import Base
from test.regression_support import (
    StubBacktestCommandService,
    StubBacktestQueryService,
    StubBinanceMarketService,
    StubBinanceWeb3Service,
    StubFactorExecutionService,
    StubFactorPaperRunManager,
    StubFactorResearchService,
    StubFundingRateAppService,
    StubMarketDataService,
    StubMarketInsightAppService,
    StubMarketQueryAppService,
    StubToolsAppService,
)


class StubCurrencyRateService:
    async def get_rates(self):
        return {
            "base": "USD",
            "rates": {"USD": 1.0, "CNY": 7.2},
            "supported": [
                {"code": "USD", "name": "US Dollar", "symbol": "$", "locale": "en-US", "fraction_digits": 2},
                {"code": "CNY", "name": "人民币", "symbol": "¥", "locale": "zh-CN", "fraction_digits": 2},
            ],
            "updated_at": "2026-04-14T00:00:00+00:00",
            "source": "test",
            "is_fallback": False,
        }


@pytest.fixture(scope="session")
def db_engine():
    """Create an in-memory SQLite engine for testing (shared across all tests)."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        echo=False,
    )
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """Provide a transactional database session that rolls back after each test."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def mock_kline_data():
    """Sample OHLCV data for testing: [timestamp_ms, open, high, low, close, volume]."""
    base_ts = 1700000000000  # Nov 2023
    return [
        [base_ts + i * 3600000, 40000 + i * 10, 40050 + i * 10, 39950 + i * 10, 40000 + i * 15, 100 + i]
        for i in range(300)
    ]


@pytest.fixture
def api_harness():
    @asynccontextmanager
    async def noop_lifespan(_app):
        yield

    services = {
        "market_data": StubMarketDataService(),
        "market_query_app": StubMarketQueryAppService(),
        "market_insight_app": StubMarketInsightAppService(),
        "funding_rate_app": StubFundingRateAppService(),
        "binance_market_service": StubBinanceMarketService(),
        "binance_web3_service": StubBinanceWeb3Service(),
        "backtest_command": StubBacktestCommandService(),
        "backtest_query": StubBacktestQueryService(),
        "tools_app": StubToolsAppService(),
        "currency_rate": StubCurrencyRateService(),
        "factor_research": StubFactorResearchService(),
        "factor_execution": StubFactorExecutionService(),
        "factor_paper": StubFactorPaperRunManager(),
    }
    app = main_module.app
    app.state.database_error = None
    original_lifespan = app.router.lifespan_context
    app.router.lifespan_context = noop_lifespan
    app.dependency_overrides = {
        get_market_data_service: lambda: services["market_data"],
        get_market_query_app_service: lambda: services["market_query_app"],
        get_market_insight_app_service: lambda: services["market_insight_app"],
        get_funding_rate_app_service: lambda: services["funding_rate_app"],
        get_binance_market_intel_service: lambda: services["binance_market_service"],
        get_binance_web3_service: lambda: services["binance_web3_service"],
        get_backtest_command_service: lambda: services["backtest_command"],
        get_backtest_query_service: lambda: services["backtest_query"],
        get_tools_app_service: lambda: services["tools_app"],
        get_currency_rate_service: lambda: services["currency_rate"],
        get_factor_research_service: lambda: services["factor_research"],
        get_factor_execution_service: lambda: services["factor_execution"],
        get_factor_paper_run_manager: lambda: services["factor_paper"],
    }

    with TestClient(app) as client:
        yield {"client": client, **services}

    app.dependency_overrides.clear()
    app.router.lifespan_context = original_lifespan
