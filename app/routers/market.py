"""
市场数据相关API路由
"""
import asyncio
from functools import lru_cache
from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from typing import Optional
from datetime import datetime
import sys
from pathlib import Path

# 添加项目根目录到Python路径
root_path = Path(__file__).parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

# 导入核心模块
try:
    from core.market_provider import MarketProvider
    from core.technical_analysis import TechnicalAnalysis
    from core.prompt_engine import PromptEngine
    from services.llm_client import LLMClient
    from config import settings
    from utils.logger import logger
    DEPS_AVAILABLE = True
except ImportError as e:
    logger_msg = f"依赖导入失败: {e}"
    print(logger_msg)
    DEPS_AVAILABLE = False

router = APIRouter()

# 延迟创建重资源实例，避免在模块导入时阻塞事件循环
@lru_cache(maxsize=1)
def get_market_provider():
    return MarketProvider()

@lru_cache(maxsize=1)
def get_llm_client():
    if not settings.DEEPSEEK_API_KEY or len(settings.DEEPSEEK_API_KEY) < 10:
        return None
    return LLMClient()

@router.get("/realtime")
async def get_realtime_analysis(
    symbol: str = Query(..., description="交易对，如 BTC/USDT"),
    timeframe: Optional[str] = Query(default=None),
    limit: Optional[int] = Query(default=None)
):
    """
    获取实时市场分析
    """
    if not DEPS_AVAILABLE:
        raise HTTPException(status_code=503, detail="服务依赖未就绪")
    
    try:
        logger.info(f"实时分析请求: {symbol}")
        
        # 使用默认值
        timeframe = timeframe or settings.TIMEFRAME
        limit = limit or settings.LIMIT
        
        # 获取 K 线数据
        market_provider = get_market_provider()
        loop = asyncio.get_running_loop()
        kline_data = await loop.run_in_executor(
            None, lambda: market_provider.get_kline_data(symbol, timeframe, limit)
        )
        
        if not kline_data:
            raise HTTPException(status_code=500, detail='获取数据失败')
        
        # 计算技术指标
        closes = [x[4] for x in kline_data]
        highs = [x[2] for x in kline_data]
        lows = [x[3] for x in kline_data]
        
        indicators = {
            'ema': TechnicalAnalysis.calculate_ema(closes, settings.EMA_PERIOD),
            'rsi': TechnicalAnalysis.calculate_rsi(closes, settings.RSI_PERIOD),
            'macd': TechnicalAnalysis.calculate_macd(
                closes, settings.MACD_FAST, settings.MACD_SLOW, settings.MACD_SIGNAL
            ),
            'atr': TechnicalAnalysis.calculate_atr(highs, lows, closes, 14)
        }
        
        # AI分析（可选）
        ai_analysis = None
        llm_client = get_llm_client()
        if llm_client:
            try:
                prompt = PromptEngine.build_analysis_prompt(symbol, kline_data, indicators)
                ai_analysis = await loop.run_in_executor(None, lambda: llm_client.analyze(prompt))
            except Exception as e:
                logger.warning(f"AI 分析失败: {e}")
        
        # 返回结果
        return {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'current_price': closes[-1],
            'indicators': {
                'ema': indicators['ema'],
                'rsi': indicators['rsi'],
                'macd': {
                    'dif': indicators['macd'][0] if indicators['macd'][0] else None,
                    'dea': indicators['macd'][1] if indicators['macd'][1] else None,
                    'histogram': indicators['macd'][2] if indicators['macd'][2] else None
                } if indicators['macd'] else None,
                'atr': indicators['atr']
            },
            'ai_analysis': ai_analysis,
            'kline_data': kline_data
        }
        
    except Exception as e:
        logger.error(f"API /realtime 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/realtime")
async def websocket_realtime(websocket: WebSocket):
    """
    WebSocket 实时推送：每隔 5s 发送最新 K 线、指标，可选 AI 文本
    参数（query）:
      - symbol: 交易对，例如 BTC/USDT
      - timeframe: 可选，默认 settings.TIMEFRAME
      - limit: 可选，默认 settings.LIMIT
      - ai: 可选，true/1 时启用 AI 分析（需要配置 DEEPSEEK_API_KEY）
    """
    await websocket.accept()
    try:
        symbol = websocket.query_params.get("symbol")
        if not symbol:
            await websocket.close(code=1008, reason="symbol is required")
            return
        timeframe = websocket.query_params.get("timeframe") or settings.TIMEFRAME
        limit = int(websocket.query_params.get("limit") or settings.LIMIT)
        use_ai = websocket.query_params.get("ai", "").lower() in ("1", "true", "yes")

        market_provider = get_market_provider()
        llm_client = get_llm_client() if use_ai else None
        loop = asyncio.get_running_loop()

        while True:
            # 获取行情与指标（线程池避免阻塞事件循环）
            kline_data = await loop.run_in_executor(
                None, lambda: market_provider.get_kline_data(symbol, timeframe, limit)
            )
            if not kline_data:
                await websocket.send_json({"type": "error", "message": "no data"})
                await asyncio.sleep(5)
                continue

            closes = [x[4] for x in kline_data]
            highs = [x[2] for x in kline_data]
            lows = [x[3] for x in kline_data]
            indicators = {
                'ema': TechnicalAnalysis.calculate_ema(closes, settings.EMA_PERIOD),
                'rsi': TechnicalAnalysis.calculate_rsi(closes, settings.RSI_PERIOD),
                'macd': TechnicalAnalysis.calculate_macd(
                    closes, settings.MACD_FAST, settings.MACD_SLOW, settings.MACD_SIGNAL
                ),
                'atr': TechnicalAnalysis.calculate_atr(highs, lows, closes, 14)
            }

            ai_analysis = None
            if llm_client:
                try:
                    prompt = PromptEngine.build_analysis_prompt(symbol, kline_data, indicators)
                    ai_analysis = await loop.run_in_executor(None, lambda: llm_client.analyze(prompt))
                except Exception as e:
                    logger.warning(f"WS AI 分析失败: {e}")

            payload = {
                'type': 'realtime',
                'symbol': symbol,
                'timeframe': timeframe,
                'timestamp': datetime.now().isoformat(),
                'current_price': closes[-1],
                'indicators': {
                    'ema': indicators['ema'],
                    'rsi': indicators['rsi'],
                    'macd': {
                        'dif': indicators['macd'][0] if indicators['macd'] and indicators['macd'][0] else None,
                        'dea': indicators['macd'][1] if indicators['macd'] and indicators['macd'][1] else None,
                        'histogram': indicators['macd'][2] if indicators['macd'] and indicators['macd'][2] else None
                    } if indicators['macd'] else None,
                    'atr': indicators['atr']
                },
                'ai_analysis': ai_analysis,
                'kline_data': kline_data
            }

            await websocket.send_json(payload)
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        logger.info("客户端断开实时推送")
    except Exception as e:
        logger.error(f"WS /ws/realtime 错误: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
        await websocket.close()

@router.get("/history")
async def get_market_history(
    symbol: str = Query(..., description="Symbol eg BTC/USDT"),
    timeframe: str = Query(..., description="Timeframe eg 5m"),
    end_ts: int = Query(..., description="End Timestamp (ms)"),
    limit: int = Query(500, description="Limit")
):
    """获取历史K线数据 (用于无限滚动)"""
    if not DEPS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Deps not ready")
        
    try:
        mp = get_market_provider()
        data = mp.get_history_data(symbol, timeframe, end_ts, limit)
        return data
    except Exception as e:
        logger.error(f"History API Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/market/sentiment")
async def get_market_sentiment():
    """获取市场情绪指标"""
    if not DEPS_AVAILABLE:
        raise HTTPException(status_code=503, detail="服务依赖未就绪")
    
    try:
        from services.sentiment_service import sentiment_service
        data = sentiment_service.get_fear_greed_index()
        
        if not data:
            raise HTTPException(status_code=500, detail='Failed to fetch sentiment')
        
        return data
        
    except Exception as e:
        from utils.logger import logger
        logger.error(f"API Error (getSentiment): {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_api_status():
    """获取API系统状态"""
    return {
        "status": "running",
        "version": "2.0.0",
        "framework": "FastAPI",
        "dependencies": "ready" if DEPS_AVAILABLE else "error",
        "timestamp": datetime.now().isoformat()
    }
