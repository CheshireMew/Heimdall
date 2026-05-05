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
from app.runtime import AppRuntimeServices
from app.runtime_refs import (
    BACKTEST_COMMAND_SERVICE,
    BACKTEST_QUERY_SERVICE,
    FACTORS_EXECUTION_SERVICE,
    FACTORS_PAPER_RUN_MANAGER,
    FACTORS_RESEARCH_SERVICE,
    INFRA_DATABASE_RUNTIME,
    MARKET_BINANCE_MARKET_INTEL,
    MARKET_BINANCE_WEB3_SERVICE,
    MARKET_FUNDING_RATE_APP_SERVICE,
    MARKET_INSIGHT_APP_SERVICE,
    MARKET_QUERY_APP_SERVICE,
    SYSTEM_CURRENCY_RATE_SERVICE,
    SYSTEM_FRED_API_CONFIG_SERVICE,
    SYSTEM_LLM_CONFIG_SERVICE,
    TOOLS_TOOLS_APP_SERVICE,
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


class StubLlmConfigService:
    def read_config(self):
        return {
            "provider": "deepseek",
            "apiKey": "",
            "apiKeySet": False,
            "apiKeyPreview": "",
            "baseUrl": "https://api.deepseek.com/v1",
            "modelId": "deepseek-chat",
            "reasoningEnabled": False,
            "presets": [
                {
                    "id": "deepseek",
                    "label": "DeepSeek",
                    "baseUrl": "https://api.deepseek.com/v1",
                    "defaultModel": "deepseek-chat",
                    "supportsReasoning": True,
                }
            ],
        }

    def save_config(self, payload):
        return self.read_config()


class StubFredApiConfigService:
    def read_config(self):
        return {
            "apiKey": "",
            "apiKeySet": False,
            "apiKeyPreview": "",
            "source": "unset",
        }

    def save_config(self, payload):
        return self.read_config()


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
        "llm_config": StubLlmConfigService(),
        "fred_api_config": StubFredApiConfigService(),
    }
    app = main_module.app
    app.state.runtime_services = AppRuntimeServices.from_entries({
        INFRA_DATABASE_RUNTIME: installed_database_runtime,
        MARKET_QUERY_APP_SERVICE: services["market_query_app"],
        MARKET_INSIGHT_APP_SERVICE: services["market_insight_app"],
        MARKET_FUNDING_RATE_APP_SERVICE: services["funding_rate_app"],
        MARKET_BINANCE_MARKET_INTEL: services["binance_market_service"],
        MARKET_BINANCE_WEB3_SERVICE: services["binance_web3_service"],
        TOOLS_TOOLS_APP_SERVICE: services["tools_app"],
        BACKTEST_COMMAND_SERVICE: services["backtest_command"],
        BACKTEST_QUERY_SERVICE: services["backtest_query"],
        FACTORS_RESEARCH_SERVICE: services["factor_research"],
        FACTORS_EXECUTION_SERVICE: services["factor_execution"],
        FACTORS_PAPER_RUN_MANAGER: services["factor_paper"],
        SYSTEM_CURRENCY_RATE_SERVICE: services["currency_rate"],
        SYSTEM_LLM_CONFIG_SERVICE: services["llm_config"],
        SYSTEM_FRED_API_CONFIG_SERVICE: services["fred_api_config"],
    })
    app.state.database_error = None
    original_lifespan = app.router.lifespan_context
    app.router.lifespan_context = noop_lifespan
    app.dependency_overrides = {}

    with TestClient(app) as client:
        yield {"client": client, **services}

    app.dependency_overrides.clear()
    app.router.lifespan_context = original_lifespan
