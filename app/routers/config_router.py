"""
配置相关API路由
"""
from fastapi import APIRouter, HTTPException
import sys
from pathlib import Path

# 添加项目根目录到Python路径
root_path = Path(__file__).parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

try:
    from config import settings
    DEPS_AVAILABLE = True
except ImportError:
    DEPS_AVAILABLE = False

router = APIRouter()

@router.get("/config")
async def get_config():
    """获取系统配置"""
    if not DEPS_AVAILABLE:
        raise HTTPException(status_code=503, detail="服务依赖未就绪")
    
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
        raise HTTPException(status_code=500, detail=str(e))
