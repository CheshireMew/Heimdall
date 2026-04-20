from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect

from app.dependencies import runtime_dependency
from app.routers.errors import service_http_error
from app.schemas.market import RealtimeResponse
from config import settings
from utils.logger import logger

if TYPE_CHECKING:
    from app.services.market.query_app_service import MarketQueryAppService
    from app.services.market.websocket_service import MarketWebSocketService


router = APIRouter(tags=["Market Data"])
market_query_dependency = runtime_dependency("market.market_query_app_service")
market_websocket_dependency = runtime_dependency("market.market_websocket_service")


@router.get("/realtime", response_model=RealtimeResponse)
async def get_realtime_analysis(
    symbol: str = Query(..., description="交易对，如 BTC/USDT"),
    timeframe: str | None = Query(default=None),
    limit: int | None = Query(default=None, ge=1, le=settings.API_MAX_LIMIT),
    service: MarketQueryAppService = Depends(market_query_dependency),
):
    try:
        return await service.get_realtime(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        err_str = str(exc).lower()
        if "network" in err_str or "connection" in err_str or "timeout" in err_str:
            logger.error(f"API /realtime 错误: {exc}")
            raise HTTPException(status_code=503, detail="无法连接到交易所 (Network Error)")
        raise service_http_error("API /realtime 错误", exc)


@router.websocket("/ws/realtime")
async def websocket_realtime(
    websocket: WebSocket,
    service: MarketQueryAppService = Depends(market_query_dependency),
    websocket_service: MarketWebSocketService = Depends(market_websocket_dependency),
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
                symbol=params["symbol"],
                timeframe=params["timeframe"],
                limit=params["limit"],
                use_ai=params["use_ai"],
            )
            if not payload:
                await websocket.send_json({"type": "error", "message": "no data"})
                await asyncio.sleep(settings.WS_UPDATE_INTERVAL)
                continue
            await websocket.send_json(payload.model_dump())
            await asyncio.sleep(settings.WS_UPDATE_INTERVAL)
    except WebSocketDisconnect:
        logger.info("客户端断开实时推送")
    except Exception as exc:
        logger.error(f"WS /ws/realtime 错误: {exc}")
        try:
            await websocket.send_json({"type": "error", "message": str(exc)})
        except Exception:
            pass
