"""配置相关API路由"""
from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi import Depends

from app.contracts.frontend import FrontendContractRouter
from app.dependencies import (
    get_currency_rate_service,
    get_database_runtime,
    get_fred_api_config_service,
    get_llm_config_service,
)
from app.exceptions import AppError
from app.domain.market.symbol_catalog import get_supported_market_symbols
from app.contracts.dto.config import (
    FredApiConfigResponse,
    FredApiConfigUpdateRequest,
    LlmProviderConfigResponse,
    LlmProviderConfigUpdateRequest,
    SystemConfigResponse,
)
from app.contracts.dto.market import CurrencyRatesResponse
from config import settings

router = FrontendContractRouter(frontend_contract_target="config")


def _require_local_settings_request(request: Request) -> None:
    host = request.client.host if request.client else ""
    if not host or host == "testclient":
        return
    if host == "localhost" or host == "::1" or host.startswith("127."):
        return
    raise AppError("配置接口仅允许本机访问", status_code=403)


def _optional_runtime_service(request: Request, name: str) -> Any | None:
    runtime_services = getattr(request.app.state, "runtime_services", None)
    if runtime_services is None:
        return None
    return getattr(runtime_services, name, None)


@router.get("/config", response_model=SystemConfigResponse)
async def get_config(
    request: Request,
    database_runtime = Depends(get_database_runtime),
):
    """获取系统配置"""
    cache_service = _optional_runtime_service(request, "cache_service")
    return SystemConfigResponse.model_validate({
        'exchange': settings.EXCHANGE_ID,
        'symbols': get_supported_market_symbols(),
        'timeframe': settings.TIMEFRAME,
        'indicators': {
            'ema_period': settings.EMA_PERIOD,
            'rsi_period': settings.RSI_PERIOD,
            'macd_fast': settings.MACD_FAST,
            'macd_slow': settings.MACD_SLOW,
            'macd_signal': settings.MACD_SIGNAL
        },
        'runtime': {
            'app_role': settings.APP_RUNTIME_ROLE,
            'database_engine': database_runtime.engine.dialect.name,
            'database_source': database_runtime.source,
            'cache_backend': type(cache_service).__name__ if cache_service is not None else 'unavailable',
        },
    })


@router.get("/currencies", response_model=CurrencyRatesResponse)
async def get_currencies(
    currency_service = Depends(get_currency_rate_service),
):
    return await currency_service.get_rates()


@router.get("/llm-config", response_model=LlmProviderConfigResponse)
async def get_llm_config(
    request: Request,
    service = Depends(get_llm_config_service),
):
    _require_local_settings_request(request)
    return service.read_config()


@router.put("/llm-config", response_model=LlmProviderConfigResponse)
async def update_llm_config(
    request: Request,
    payload: LlmProviderConfigUpdateRequest,
    service = Depends(get_llm_config_service),
):
    _require_local_settings_request(request)
    return service.save_config(payload.model_dump())


@router.get("/fred-api-config", response_model=FredApiConfigResponse)
async def get_fred_api_config(
    request: Request,
    service = Depends(get_fred_api_config_service),
):
    _require_local_settings_request(request)
    return service.read_config()


@router.put("/fred-api-config", response_model=FredApiConfigResponse)
async def update_fred_api_config(
    request: Request,
    payload: FredApiConfigUpdateRequest,
    service = Depends(get_fred_api_config_service),
):
    _require_local_settings_request(request)
    return service.save_config(payload.model_dump())
