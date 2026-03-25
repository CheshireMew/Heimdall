"""
市场数据相关 API 路由
"""
from __future__ import annotations

import asyncio
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, WebSocket, WebSocketDisconnect

from app.dependencies import get_market_app_service, get_market_data_service
from app.rate_limit import limiter
from app.schemas.market import ApiStatusResponse, CryptoIndexResponse, MarketIndicatorResponse, RealtimeResponse
from app.services.market.app_service import MarketAppService
from app.services.market.market_data_service import MarketDataService
from app.services.market.websocket_service import MarketWebSocketService
from config import settings
from utils.logger import logger


router = APIRouter(tags=["Market Data"])
websocket_service = MarketWebSocketService()


@router.get("/realtime", response_model=RealtimeResponse)
async def get_realtime_analysis(
    symbol: str = Query(..., description="交易对，如 BTC/USDT"),
    timeframe: str | None = Query(default=None),
    limit: int | None = Query(default=None, ge=1, le=settings.API_MAX_LIMIT),
    market_data_service: MarketDataService = Depends(get_market_data_service),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_realtime(
            market_data_service=market_data_service,
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"API /realtime 错误: {exc}")
        err_str = str(exc).lower()
        if "network" in err_str or "connection" in err_str or "timeout" in err_str:
            raise HTTPException(status_code=503, detail="无法连接到交易所 (Network Error)")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.websocket("/ws/realtime")
async def websocket_realtime(
    websocket: WebSocket,
    market_data_service: MarketDataService = Depends(get_market_data_service),
    service: MarketAppService = Depends(get_market_app_service),
):
    await websocket.accept()
    try:
        try:
            params = websocket_service.parse_params(websocket, service.valid_symbols, service.valid_timeframes)
        except ValueError as exc:
            await websocket_service.reject(websocket, str(exc))
            return

        while True:
            payload = await service.get_realtime_ws_payload(
                market_data_service=market_data_service,
                symbol=params["symbol"],
                timeframe=params["timeframe"],
                limit=params["limit"],
                use_ai=params["use_ai"],
            )
            if not payload:
                await websocket.send_json({"type": "error", "message": "no data"})
                await asyncio.sleep(settings.WS_UPDATE_INTERVAL)
                continue
            await websocket.send_json(payload)
            await asyncio.sleep(settings.WS_UPDATE_INTERVAL)
    except WebSocketDisconnect:
        logger.info("客户端断开实时推送")
    except Exception as exc:
        logger.error(f"WS /ws/realtime 错误: {exc}")
        try:
            await websocket.send_json({"type": "error", "message": str(exc)})
        except Exception:
            pass


@router.get("/history", response_model=list[list[float]])
async def get_market_history(
    symbol: str = Query(..., description="Symbol eg BTC/USDT"),
    timeframe: str = Query(..., description="Timeframe eg 5m"),
    end_ts: int = Query(..., description="End Timestamp (ms)", gt=0),
    limit: int = Query(settings.HISTORY_DEFAULT_LIMIT, description="Limit", ge=1, le=settings.API_MAX_LIMIT),
    market_data_service: MarketDataService = Depends(get_market_data_service),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return service.get_history(
            market_data_service=market_data_service,
            symbol=symbol,
            timeframe=timeframe,
            end_ts=end_ts,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"History API Error: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/full_history", response_model=list[list[float]])
@limiter.limit(settings.RATE_LIMIT_HEAVY)
async def get_market_full_history(
    request: Request,
    background_tasks: BackgroundTasks,
    symbol: str = Query(..., description="Symbol eg BTC/USDT"),
    timeframe: str = Query("1d", description="Timeframe eg 1d"),
    start_date: str = Query("2010-01-01", description="Start Date YYYY-MM-DD"),
    market_data_service: MarketDataService = Depends(get_market_data_service),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        persist_klines = lambda save_symbol, save_timeframe, klines: background_tasks.add_task(
            market_data_service.save_klines_background,
            save_symbol,
            save_timeframe,
            klines,
        )
        return await service.get_full_history(
            market_data_service=market_data_service,
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            persist_klines=persist_klines,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"Full History API Error: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/indicators", response_model=list[MarketIndicatorResponse])
async def get_market_indicators(
    category: str | None = Query(None, description="过滤分类, 如 Macro, Onchain, Sentiment, General"),
    days: int = Query(settings.INDICATORS_DEFAULT_DAYS, description="历史数据天数"),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return service.get_indicators(category=category, days=days)
    except Exception as exc:
        logger.error(f"API /indicators 错误: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/status", response_model=ApiStatusResponse)
async def get_api_status():
    return {
        "status": "running",
        "version": "2.0.0",
        "framework": "FastAPI",
        "dependencies": "ready",
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/crypto_index", response_model=CryptoIndexResponse)
@limiter.limit(settings.RATE_LIMIT_HEAVY)
async def get_crypto_index(
    request: Request,
    top_n: int = Query(20, ge=5, le=100, description="Current top N market cap assets"),
    days: int = Query(90, ge=30, le=365, description="Historical days"),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_crypto_index(top_n=top_n, days=days)
    except Exception as exc:
        logger.error(f"Crypto index API error: {exc}")
        raise HTTPException(status_code=500, detail="Failed to build crypto index")
