"""
回测相关API路由
"""
import asyncio
from functools import lru_cache
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
import sys
from pathlib import Path

# 添加项目根目录到Python路径
root_path = Path(__file__).parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

try:
    from core.backtester import Backtester
    from models.schema import BacktestRun
    from models.database import get_session
    from api.serializers import serialize_backtest_run
    from config import settings
    from utils.logger import logger
    DEPS_AVAILABLE = True
except ImportError as e:
    print(f"回测模块导入失败: {e}")
    DEPS_AVAILABLE = False

router = APIRouter()

@lru_cache(maxsize=1)
def get_backtester_factory():
    """返回 Backtester 构造函数，避免在导入时阻塞事件循环"""
    return Backtester

class BacktestRequest(BaseModel):
    symbol: str = 'BTC/USDT'
    days: int = 7
    use_ai: bool = False

@router.post("/backtest/start")
async def start_backtest(request: BacktestRequest):
    """启动回测"""
    if not DEPS_AVAILABLE:
        raise HTTPException(status_code=503, detail="服务依赖未就绪")
    
    try:
        logger.info(f"启动回测: {request.symbol}, {request.days}天, AI={request.use_ai}")
        
        end = datetime.now()
        start = end - timedelta(days=request.days)
        
        loop = asyncio.get_running_loop()
        backtester_cls = get_backtester_factory()
        backtest_id = await loop.run_in_executor(
            None,
            lambda: backtester_cls(use_ai=request.use_ai).run_backtest(
                request.symbol, start, end, settings.TIMEFRAME
            )
        )
        
        if backtest_id:
            return {'success': True, 'backtest_id': backtest_id, 'message': '回测已完成'}
        else:
            raise HTTPException(status_code=500, detail='回测执行失败')
            
    except Exception as e:
        logger.error(f"API /backtest/start 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/backtest/list")
async def list_backtests():
    """回测列表"""
    if not DEPS_AVAILABLE:
        raise HTTPException(status_code=503, detail="服务依赖未就绪")
    
    try:
        loop = asyncio.get_running_loop()
        def _fetch():
            session = get_session()
            try:
                backtest_runs = session.query(BacktestRun).order_by(BacktestRun.created_at.desc()).all()
                return [serialize_backtest_run(run, include_signals=False) for run in backtest_runs]
            finally:
                session.close()
        return await loop.run_in_executor(None, _fetch)
    except Exception as e:
        logger.error(f"API /backtest/list 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/backtest/{backtest_id}")
async def get_backtest(backtest_id: int):
    """获取回测结果"""
    if not DEPS_AVAILABLE:
        raise HTTPException(status_code=503, detail="服务依赖未就绪")
    
    try:
        loop = asyncio.get_running_loop()
        def _fetch():
            session = get_session()
            try:
                backtest_run = session.query(BacktestRun).filter(BacktestRun.id == backtest_id).first()
                if not backtest_run:
                    return None
                return serialize_backtest_run(backtest_run, include_signals=True)
            finally:
                session.close()

        result = await loop.run_in_executor(None, _fetch)
        if not result:
            raise HTTPException(status_code=404, detail='回测记录不存在')
        return result
    except Exception as e:
        logger.error(f"API /backtest/{backtest_id} 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))
