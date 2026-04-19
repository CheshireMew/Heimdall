"""配置相关API路由"""
from __future__ import annotations

import ipaddress

from fastapi import APIRouter, HTTPException, Request
from fastapi import Depends

from app.dependencies import get_currency_rate_service
from app.infra.db import get_database_runtime
from app.domain.market.symbol_catalog import get_supported_market_symbols
from app.routers.errors import service_http_error
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


def _require_local_settings_request(request: Request) -> None:
    host = request.client.host if request.client else ""
    if not host or host == "testclient":
        return
    try:
        if ipaddress.ip_address(host).is_loopback:
            return
    except ValueError:
        pass
    raise HTTPException(status_code=403, detail="配置接口仅允许本机访问")


@router.get("/config", response_model=SystemConfigResponse)
async def get_config():
    """获取系统配置"""
    try:
        database_runtime = get_database_runtime()
        return {
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
                'cache_backend': 'local-memory',
            },
        }
    except Exception as exc:
        raise service_http_error("API /config 错误", exc)


@router.get("/currencies", response_model=CurrencyRatesResponse)
async def get_currencies(
    currency_service: CurrencyRateService = Depends(get_currency_rate_service),
):
    try:
        return await currency_service.get_rates()
    except Exception as exc:
        raise service_http_error("API /currencies 错误", exc)


@router.get("/llm-config", response_model=LlmProviderConfigResponse)
async def get_llm_config(request: Request):
    _require_local_settings_request(request)
    try:
        return read_llm_config()
    except Exception as exc:
        raise service_http_error("API /llm-config 错误", exc)


@router.put("/llm-config", response_model=LlmProviderConfigResponse)
async def update_llm_config(request: Request, payload: LlmProviderConfigUpdateRequest):
    _require_local_settings_request(request)
    try:
        return save_llm_config(payload.model_dump())
    except Exception as exc:
        raise service_http_error("API PUT /llm-config 错误", exc)
