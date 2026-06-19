from app.runtime_builder import active_service_definitions
from app.runtime_refs import (
    INFRA_EXCHANGE_GATEWAY,
    INFRA_KLINE_STORE,
    MARKET_BINANCE_MARKET_INTEL,
    MARKET_BINANCE_MARKET_SNAPSHOT,
    MARKET_MARKET_DATA_SERVICE,
    SYSTEM_MARKET_SCHEDULER_RUNTIME,
)
from config import settings


def test_default_runtime_role_is_api():
    assert settings.APP_RUNTIME_ROLE == "api"


def test_background_runtime_role_excludes_api_market_io_services():
    background_refs = {definition.ref for definition in active_service_definitions("background")}

    assert SYSTEM_MARKET_SCHEDULER_RUNTIME in background_refs
    assert INFRA_EXCHANGE_GATEWAY not in background_refs
    assert INFRA_KLINE_STORE not in background_refs
    assert MARKET_MARKET_DATA_SERVICE not in background_refs
    assert MARKET_BINANCE_MARKET_INTEL not in background_refs
    assert MARKET_BINANCE_MARKET_SNAPSHOT not in background_refs
