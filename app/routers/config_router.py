"""
配置相关API路由
"""
from fastapi import APIRouter, HTTPException
from fastapi import Depends

from app.dependencies import get_currency_rate_service
from app.domain.market.symbol_catalog import get_supported_market_symbols
from app.schemas.config import LlmProviderConfigResponse, LlmProviderConfigUpdateRequest
from app.schemas.market import CurrencyRatesResponse
from app.services.llm_config_service import read_llm_config, save_llm_config
from app.services.currency_service import CurrencyRateService
from config import settings
from utils.logger import logger

router = APIRouter()

@router.get("/config")
async def get_config():
    """获取系统配置"""
    try:
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
            }
        }
    except Exception as e:
        logger.error(f"API /config 错误: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/currencies", response_model=CurrencyRatesResponse)
async def get_currencies(
    currency_service: CurrencyRateService = Depends(get_currency_rate_service),
):
    try:
        return await currency_service.get_rates()
    except Exception as e:
        logger.error(f"API /currencies 错误: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/llm-config", response_model=LlmProviderConfigResponse)
async def get_llm_config():
    try:
        return read_llm_config()
    except Exception as e:
        logger.error(f"API /llm-config 错误: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/llm-config", response_model=LlmProviderConfigResponse)
async def update_llm_config(payload: LlmProviderConfigUpdateRequest):
    try:
        return save_llm_config(payload.model_dump())
    except Exception as e:
        logger.error(f"API PUT /llm-config 错误: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
