from app.runtime import BACKGROUND_REQUIRED_SERVICES, AppRuntimeServices, missing_required_services
from config import settings


def test_default_runtime_role_is_api():
    assert settings.APP_RUNTIME_ROLE == "api"


def test_background_runtime_role_excludes_api_market_io_services():
    services = AppRuntimeServices(
        database_runtime=object(),
        cache_service=object(),
        market_indicator_repository=object(),
        dli_cache=object(),
        market_scheduler_runtime=object(),
    )

    assert tuple(BACKGROUND_REQUIRED_SERVICES) == (
        "database_runtime",
        "cache_service",
        "market_indicator_repository",
        "dli_cache",
        "market_scheduler_runtime",
    )
    assert missing_required_services(services, "background") == []
    assert services.exchange_gateway is None
    assert services.kline_store is None
    assert services.market_data_service is None
    assert services.binance_market_intel is None
    assert services.binance_market_snapshot is None
