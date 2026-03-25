"""
配置相关API路由
"""
from fastapi import APIRouter, HTTPException

from config import settings
from utils.logger import logger

router = APIRouter()

@router.get("/config")
async def get_config():
    """获取系统配置"""
    try:
        return {
            'exchange': settings.EXCHANGE_ID,
            'symbols': settings.SYMBOLS,
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
