from __future__ import annotations

import asyncio
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect

from app.dependencies import runtime_dependency
from app.contracts.dto.market import RealtimeResponse
from config import settings
from utils.logger import logger


router = APIRouter(tags=["Market Data"])
market_query_dependency = runtime_dependency("market_query_service")
market_websocket_dependency = runtime_dependency("market_websocket_service")


@router.get("/realtime", response_model=RealtimeResponse)
async def get_realtime_analysis(
    symbol: str = Query(..., description="交易对，如 BTC/USDT"),
    timeframe: str | None = Query(default=None),
    limit: int | None = Query(default=None, ge=1, le=settings.API_MAX_LIMIT),
    service = Depends(market_query_dependency),
):
    return await service.get_realtime(
        symbol=symbol,
        timeframe=timeframe,
        limit=limit,
    )


@router.websocket("/ws/realtime")
async def websocket_realtime(
    websocket: WebSocket,
    service = Depends(market_query_dependency),
    websocket_service = Depends(market_websocket_dependency),
):
    await websocket.accept()
    try:
        params = await websocket_service.parse_params_or_reject(websocket, service.valid_symbols, service.valid_timeframes)
        if params is None:
            return

        while True:
            payload = await service.get_realtime_ws_payload(
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
