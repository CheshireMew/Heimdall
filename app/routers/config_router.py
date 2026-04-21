"""配置相关API路由"""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi import Depends

from app.dependencies import runtime_dependency
from app.exceptions import AppError
from app.infra.db import DatabaseRuntime
from app.runtime_graph import INFRA_DATABASE_RUNTIME, SYSTEM_CURRENCY_RATE_SERVICE
from app.domain.market.symbol_catalog import get_supported_market_symbols
from app.schemas.config import (
    LlmProviderConfigResponse,
    LlmProviderConfigUpdateRequest,
    SystemConfigResponse,
)
from app.schemas.market import CurrencyRatesResponse
from app.services.llm_config_service import read_llm_config, save_llm_config
from app.services.currency_service import CurrencyRateService
from config import settings

router = APIRouter()
database_runtime_dependency = runtime_dependency(INFRA_DATABASE_RUNTIME)
currency_rate_dependency = runtime_dependency(SYSTEM_CURRENCY_RATE_SERVICE)


def _require_local_settings_request(request: Request) -> None:
    host = request.client.host if request.client else ""
    if not host or host == "testclient":
        return
    if host == "localhost" or host == "::1" or host.startswith("127."):
        return
    raise AppError("配置接口仅允许本机访问", status_code=403)


@router.get("/config", response_model=SystemConfigResponse)
async def get_config(
    database_runtime: DatabaseRuntime = Depends(database_runtime_dependency),
):
    """获取系统配置"""
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
            'cache_backend': 'local-memory',
        },
    })


@router.get("/currencies", response_model=CurrencyRatesResponse)
async def get_currencies(
    currency_service: CurrencyRateService = Depends(currency_rate_dependency),
):
    return await currency_service.get_rates()


@router.get("/llm-config", response_model=LlmProviderConfigResponse)
async def get_llm_config(request: Request):
    _require_local_settings_request(request)
    return read_llm_config()


@router.put("/llm-config", response_model=LlmProviderConfigResponse)
async def update_llm_config(request: Request, payload: LlmProviderConfigUpdateRequest):
    _require_local_settings_request(request)
    return save_llm_config(payload.model_dump())
