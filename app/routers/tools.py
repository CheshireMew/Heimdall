"""
工具类API路由
"""
import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import sys
from pathlib import Path

# 添加项目根目录到Python路径
root_path = Path(__file__).parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

try:
    from utils.logger import logger
    DEPS_AVAILABLE = True
except ImportError:
    DEPS_AVAILABLE = False

router = APIRouter()

# Pydantic模型
class DCARequest(BaseModel):
    symbol: str = 'BTC/USDT'
    amount: float = 100.0
    start_date: Optional[str] = None
    investment_time: str = '23:00'
    days: Optional[int] = None
    strategy: str = 'standard' # standard, ema_deviation
    strategy_params: Optional[dict] = {}

class PairCompareRequest(BaseModel):
    symbol_a: str = 'BTC'
    symbol_b: str = 'ETH'
    days: int = 7
    timeframe: str = '1h'

@router.post("/dca_simulate")
async def dca_simulate(request: DCARequest):
    """定投回测模拟"""
    if not DEPS_AVAILABLE:
        raise HTTPException(status_code=503, detail="服务依赖未就绪")
    
    try:
        # 处理日期
        if request.start_date:
            start_date_str = request.start_date
        else:
            days = request.days or 365
            start_date_str = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        from core.dca_calculator import DCACalculator
        calculator = DCACalculator()
        loop = asyncio.get_running_loop()
        
        result = await loop.run_in_executor(
            None,
            lambda: calculator.calculate_dca(
                symbol=request.symbol,
                start_date_str=start_date_str,
                end_date_str=None,
                daily_investment=request.amount,
                target_time_str=request.investment_time,
                strategy=request.strategy,
                strategy_params=request.strategy_params
            )
        )
        
        if 'error' in result:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return result
        
    except Exception as e:
        logger.error(f"API Error (DCA): {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/compare_pairs")
async def compare_pairs(request: PairCompareRequest):
    """币种对比分析"""
    if not DEPS_AVAILABLE:
        raise HTTPException(status_code=503, detail="服务依赖未就绪")
    
    try:
        symbol_a = request.symbol_a.upper()
        symbol_b = request.symbol_b.upper()
        
        logger.info(f"币种对比请求: {symbol_a} vs {symbol_b}, {request.days}天, {request.timeframe}")
        
        from core.pair_comparator import PairComparator
        comparator = PairComparator()
        loop = asyncio.get_running_loop()
        
        result = await loop.run_in_executor(
            None,
            lambda: comparator.compare_pairs(symbol_a, symbol_b, request.days, request.timeframe)
        )
        
        if 'error' in result:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return result
        
    except Exception as e:
        logger.error(f"API Error (Pair Comparison): {e}")
        raise HTTPException(status_code=500, detail=str(e))
