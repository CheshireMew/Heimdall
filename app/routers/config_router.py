"""配置相关API路由"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi import Depends

from app.dependencies import runtime_dependency
from app.exceptions import AppError
from app.router_service_ports import CurrencyRatePort, DatabaseRuntimePort, FredApiConfigPort, LlmConfigPort
from app.runtime_refs import (
    INFRA_CACHE_SERVICE,
    INFRA_DATABASE_RUNTIME,
    SYSTEM_CURRENCY_RATE_SERVICE,
    SYSTEM_FRED_API_CONFIG_SERVICE,
    SYSTEM_LLM_CONFIG_SERVICE,
)
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

router = APIRouter()
database_runtime_dependency = runtime_dependency(INFRA_DATABASE_RUNTIME)
currency_rate_dependency = runtime_dependency(SYSTEM_CURRENCY_RATE_SERVICE)
llm_config_dependency = runtime_dependency(SYSTEM_LLM_CONFIG_SERVICE)
fred_api_config_dependency = runtime_dependency(SYSTEM_FRED_API_CONFIG_SERVICE)


def _require_local_settings_request(request: Request) -> None:
    host = request.client.host if request.client else ""
    if not host or host == "testclient":
        return
    if host == "localhost" or host == "::1" or host.startswith("127."):
        return
    raise AppError("配置接口仅允许本机访问", status_code=403)


def _optional_runtime_service(request: Request, ref: Any) -> Any | None:
    runtime_services = getattr(request.app.state, "runtime_services", None)
    if runtime_services is None:
        return None
    return runtime_services.get_service(ref)


@router.get("/config", response_model=SystemConfigResponse)
async def get_config(
    request: Request,
    database_runtime: DatabaseRuntimePort = Depends(database_runtime_dependency),
):
    """获取系统配置"""
    cache_service = _optional_runtime_service(request, INFRA_CACHE_SERVICE)
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
    currency_service: CurrencyRatePort = Depends(currency_rate_dependency),
):
    return await currency_service.get_rates()


@router.get("/llm-config", response_model=LlmProviderConfigResponse)
async def get_llm_config(
    request: Request,
    service: LlmConfigPort = Depends(llm_config_dependency),
):
    _require_local_settings_request(request)
    return service.read_config()


@router.put("/llm-config", response_model=LlmProviderConfigResponse)
async def update_llm_config(
    request: Request,
    payload: LlmProviderConfigUpdateRequest,
    service: LlmConfigPort = Depends(llm_config_dependency),
):
    _require_local_settings_request(request)
    return service.save_config(payload.model_dump())


@router.get("/fred-api-config", response_model=FredApiConfigResponse)
async def get_fred_api_config(
    request: Request,
    service: FredApiConfigPort = Depends(fred_api_config_dependency),
):
    _require_local_settings_request(request)
    return service.read_config()


@router.put("/fred-api-config", response_model=FredApiConfigResponse)
async def update_fred_api_config(
    request: Request,
    payload: FredApiConfigUpdateRequest,
    service: FredApiConfigPort = Depends(fred_api_config_dependency),
):
    _require_local_settings_request(request)
    return service.save_config(payload.model_dump())
