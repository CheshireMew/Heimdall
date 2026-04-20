"""
Shared pytest fixtures for Heimdall tests.
"""
from contextlib import asynccontextmanager
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import app.main as main_module
from app.runtime import (
    AppRuntimeServices,
    BacktestRuntime,
    FactorRuntime,
    InfraRuntime,
    MarketRuntime,
    SystemRuntime,
    ToolsRuntime,
)
from app.infra.db import build_database_runtime
from app.infra.db.schema import Base
from config.settings import AppSettings
from test.regression_support import (
    StubBacktestCommandService,
    StubBacktestQueryService,
    StubBinanceMarketService,
    StubBinanceWeb3Service,
    StubFactorExecutionService,
    StubFactorPaperRunManager,
    StubFactorResearchService,
    StubFundingRateAppService,
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


@pytest.fixture(autouse=True)
def installed_database_runtime(tmp_path):
    database_url = f"sqlite:///{(tmp_path / 'test.db').as_posix()}"
    runtime = build_database_runtime(AppSettings(DATABASE_URL=database_url))
    Base.metadata.create_all(runtime.engine)
    try:
        yield runtime
    finally:
        runtime.dispose()


@pytest.fixture
def db_engine(installed_database_runtime):
    """Expose the installed runtime engine to tests that need direct SQLAlchemy access."""
    return installed_database_runtime.engine


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
def api_harness(installed_database_runtime):
    @asynccontextmanager
    async def noop_lifespan(_app):
        yield

    services = {
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
    app.state.runtime_services = AppRuntimeServices(
        infra=InfraRuntime(database_runtime=installed_database_runtime),
        market=MarketRuntime(
            market_query_app_service=services["market_query_app"],
            market_insight_app_service=services["market_insight_app"],
            funding_rate_app_service=services["funding_rate_app"],
            binance_market_intel=services["binance_market_service"],
            binance_web3_service=services["binance_web3_service"],
        ),
        tools=ToolsRuntime(tools_app_service=services["tools_app"]),
        backtest=BacktestRuntime(
            backtest_command_service=services["backtest_command"],
            backtest_query_service=services["backtest_query"],
        ),
        factors=FactorRuntime(
            factor_research_service=services["factor_research"],
            factor_execution_service=services["factor_execution"],
            factor_paper_run_manager=services["factor_paper"],
        ),
        system=SystemRuntime(currency_rate_service=services["currency_rate"]),
    )
    app.state.database_error = None
    original_lifespan = app.router.lifespan_context
    app.router.lifespan_context = noop_lifespan
    app.dependency_overrides = {}

    with TestClient(app) as client:
        yield {"client": client, **services}

    app.dependency_overrides.clear()
    app.router.lifespan_context = original_lifespan
