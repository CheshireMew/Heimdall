from __future__ import annotations

import asyncio
from datetime import datetime
from typing import TYPE_CHECKING, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, WebSocket, WebSocketDisconnect

from app.dependencies import (
    get_base_market_app_service,
    get_index_data_service,
    get_market_data_service,
)
from app.domain.market.symbol_catalog import list_market_search_items
from app.rate_limit import limiter
from app.routers.market.common import internal_error
from app.schemas.market import (
    ApiStatusResponse,
    CryptoIndexResponse,
    CurrentPriceResponse,
    FundingRateHistoryResponse,
    FundingRateSnapshotResponse,
    FundingRateSyncResponse,
    KlineTailResponse,
    MarketIndicatorResponse,
    MarketIndexHistoryResponse,
    MarketIndexResponse,
    MarketSymbolSearchResponse,
    RealtimeResponse,
    TechnicalMetricsResponse,
    TradeSetupResponse,
)
from app.services.market.websocket_service import MarketWebSocketService
from config import settings
from utils.logger import logger

if TYPE_CHECKING:
    from app.services.market.base_app_service import BaseMarketAppService
    from app.services.market.index_data_service import IndexDataService
    from app.services.market.market_data_service import MarketDataService


router = APIRouter(tags=["Market Data"])
websocket_service = MarketWebSocketService()


@router.get("/symbols", response_model=list[MarketSymbolSearchResponse])
async def list_market_symbols():
    return list_market_search_items()


@router.get("/realtime", response_model=RealtimeResponse)
async def get_realtime_analysis(
    symbol: str = Query(..., description="交易对，如 BTC/USDT"),
    timeframe: str | None = Query(default=None),
    limit: int | None = Query(default=None, ge=1, le=settings.API_MAX_LIMIT),
    market_data_service: MarketDataService = Depends(get_market_data_service),
    service: BaseMarketAppService = Depends(get_base_market_app_service),
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
    service: BaseMarketAppService = Depends(get_base_market_app_service),
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
    service: BaseMarketAppService = Depends(get_base_market_app_service),
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
        raise internal_error("History API Error", exc)


@router.get("/klines/latest", response_model=list[list[float]])
async def get_latest_klines(
    symbol: str = Query(..., description="Symbol eg BTC/USDT"),
    timeframe: str = Query(..., description="Timeframe eg 5m"),
    limit: int = Query(settings.LIMIT, description="Limit", ge=1, le=settings.API_MAX_LIMIT),
    market_data_service: MarketDataService = Depends(get_market_data_service),
    service: BaseMarketAppService = Depends(get_base_market_app_service),
):
    try:
        return service.get_recent_klines(
            market_data_service=market_data_service,
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise internal_error("Latest klines API Error", exc)


@router.get("/klines/tail", response_model=KlineTailResponse)
async def get_kline_tail(
    symbol: str = Query(..., description="Symbol eg BTC/USDT"),
    timeframe: str = Query(..., description="Timeframe eg 5m"),
    limit: int = Query(2, description="Tail size", ge=1, le=20),
    market_data_service: MarketDataService = Depends(get_market_data_service),
    service: BaseMarketAppService = Depends(get_base_market_app_service),
):
    try:
        return await service.get_live_kline_tail(
            market_data_service=market_data_service,
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise internal_error("Kline tail API Error", exc)


@router.get("/price/current", response_model=CurrentPriceResponse)
async def get_current_price(
    symbol: str = Query(..., description="Symbol eg BTC/USDT"),
    timeframe: str = Query("1d", description="Timeframe eg 1d"),
    market_data_service: MarketDataService = Depends(get_market_data_service),
    service: BaseMarketAppService = Depends(get_base_market_app_service),
):
    try:
        return await service.get_current_price(
            market_data_service=market_data_service,
            symbol=symbol,
            timeframe=timeframe,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise internal_error("Current price API Error", exc)


@router.get("/full_history", response_model=list[list[float]])
@limiter.limit(settings.RATE_LIMIT_HISTORY)
async def get_market_full_history(
    request: Request,
    symbol: str = Query(..., description="Symbol eg BTC/USDT"),
    timeframe: str = Query("1d", description="Timeframe eg 1d"),
    start_date: str = Query("2010-01-01", description="Start Date YYYY-MM-DD"),
    fetch_policy: Literal["cache_only", "hydrate"] = Query("hydrate", description="History source policy"),
    market_data_service: MarketDataService = Depends(get_market_data_service),
    service: BaseMarketAppService = Depends(get_base_market_app_service),
):
    try:
        return await service.get_full_history(
            market_data_service=market_data_service,
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            fetch_policy=fetch_policy,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise internal_error("Full History API Error", exc)


@router.get("/full_history/batch", response_model=dict[str, list[list[float]]])
@limiter.limit(settings.RATE_LIMIT_HISTORY)
async def get_market_full_history_batch(
    request: Request,
    symbols: list[str] = Query(..., description="交易对列表，如 BTC/USDT"),
    timeframe: str = Query("1d", description="Timeframe eg 1d"),
    start_date: str = Query("2010-01-01", description="Start Date YYYY-MM-DD"),
    fetch_policy: Literal["cache_only", "hydrate"] = Query("hydrate", description="History source policy"),
    market_data_service: MarketDataService = Depends(get_market_data_service),
    service: BaseMarketAppService = Depends(get_base_market_app_service),
):
    try:
        return await service.get_full_history_batch(
            market_data_service=market_data_service,
            symbols=symbols,
            timeframe=timeframe,
            start_date=start_date,
            fetch_policy=fetch_policy,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise internal_error("Batch Full History API Error", exc)


@router.get("/indicators", response_model=list[MarketIndicatorResponse])
async def get_market_indicators(
    category: str | None = Query(None, description="过滤分类, 如 Macro, Onchain, Sentiment, General"),
    days: int = Query(settings.INDICATORS_DEFAULT_DAYS, description="历史数据天数"),
    service: BaseMarketAppService = Depends(get_base_market_app_service),
):
    try:
        return service.get_indicators(category=category, days=days)
    except Exception as exc:
        raise internal_error("API /indicators 错误", exc)


@router.get("/indexes", response_model=list[MarketIndexResponse])
async def list_market_indexes(
    service: IndexDataService = Depends(get_index_data_service),
):
    return service.list_indexes()


@router.get("/indexes/history", response_model=MarketIndexHistoryResponse)
@limiter.limit(settings.RATE_LIMIT_HISTORY)
async def get_index_history(
    request: Request,
    symbol: str = Query(..., description="指数 symbol, 如 US_SP500 或 CN_CSI300"),
    timeframe: str = Query("1d", description="第一版仅支持 1d"),
    start_date: str = Query("2010-01-01", description="Start Date YYYY-MM-DD"),
    end_date: str | None = Query(None, description="End Date YYYY-MM-DD"),
    service: IndexDataService = Depends(get_index_data_service),
):
    try:
        return service.get_history(
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise internal_error("Index History API Error", exc)


@router.get("/indexes/latest", response_model=MarketIndexHistoryResponse)
@limiter.limit(settings.RATE_LIMIT_HISTORY)
async def get_latest_index(
    request: Request,
    symbol: str = Query(..., description="指数 symbol, 如 US_SP500 或 CN_CSI300"),
    service: IndexDataService = Depends(get_index_data_service),
):
    try:
        return service.get_latest(symbol=symbol)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise internal_error("Latest Index API Error", exc)


@router.get("/indexes/pricing/history", response_model=MarketIndexHistoryResponse)
@limiter.limit(settings.RATE_LIMIT_HISTORY)
async def get_index_pricing_history(
    request: Request,
    symbol: str = Query(..., description="指数 symbol, 如 US_SP500 或 CN_CSI300"),
    timeframe: str = Query("1d", description="第一版仅支持 1d"),
    start_date: str = Query("2010-01-01", description="Start Date YYYY-MM-DD"),
    end_date: str | None = Query(None, description="End Date YYYY-MM-DD"),
    service: IndexDataService = Depends(get_index_data_service),
):
    try:
        return service.get_pricing_history(
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise internal_error("Index Pricing History API Error", exc)


@router.get("/indexes/pricing/latest", response_model=MarketIndexHistoryResponse)
@limiter.limit(settings.RATE_LIMIT_HISTORY)
async def get_latest_index_pricing(
    request: Request,
    symbol: str = Query(..., description="指数 symbol, 如 US_SP500 或 CN_CSI300"),
    service: IndexDataService = Depends(get_index_data_service),
):
    try:
        return service.get_latest_pricing(symbol=symbol)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise internal_error("Latest Index Pricing API Error", exc)


@router.get("/funding-rate/current", response_model=FundingRateSnapshotResponse)
@limiter.limit(settings.RATE_LIMIT_HEAVY)
async def get_current_funding_rate(
    request: Request,
    symbol: str = Query(..., description="合约 symbol，例如 BTCUSDT 或 BTC/USDT:USDT"),
    service: BaseMarketAppService = Depends(get_base_market_app_service),
):
    try:
        return await service.get_current_funding_rate(symbol)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise internal_error("API /funding-rate/current 错误", exc)


@router.post("/funding-rate/sync", response_model=FundingRateSyncResponse)
@limiter.limit(settings.RATE_LIMIT_HEAVY)
async def sync_funding_rate_history(
    request: Request,
    symbol: str = Query(..., description="合约 symbol，例如 BTCUSDT"),
    start_date: str = Query("2019-09-01", description="开始日期 YYYY-MM-DD"),
    end_date: str | None = Query(None, description="结束日期 YYYY-MM-DD，默认当前时间"),
    service: BaseMarketAppService = Depends(get_base_market_app_service),
):
    try:
        return await service.sync_funding_rate_history(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise internal_error("API /funding-rate/sync 错误", exc)


@router.get("/funding-rate/history", response_model=FundingRateHistoryResponse)
async def get_funding_rate_history(
    symbol: str = Query(..., description="合约 symbol，例如 BTCUSDT"),
    start_date: str | None = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: str | None = Query(None, description="结束日期 YYYY-MM-DD"),
    limit: int | None = Query(None, ge=1, le=20000),
    service: BaseMarketAppService = Depends(get_base_market_app_service),
):
    try:
        return await service.get_funding_rate_history(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise internal_error("API /funding-rate/history 错误", exc)


@router.get("/technical-metrics", response_model=TechnicalMetricsResponse)
async def get_technical_metrics(
    symbol: str = Query(..., description="交易对，如 BTC/USDT"),
    timeframe: str = Query("1d", description="时间周期，如 1d"),
    limit: int = Query(120, ge=30, le=settings.API_MAX_LIMIT),
    atr_period: int = Query(14, ge=2, le=200),
    volatility_period: int = Query(20, ge=2, le=365),
    market_data_service: MarketDataService = Depends(get_market_data_service),
    service: BaseMarketAppService = Depends(get_base_market_app_service),
):
    try:
        return await service.get_technical_metrics(
            market_data_service=market_data_service,
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            atr_period=atr_period,
            volatility_period=volatility_period,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise internal_error("API /technical-metrics 错误", exc)


@router.get("/trade-setup", response_model=TradeSetupResponse)
async def get_trade_setup(
    symbol: str = Query(..., description="交易对，如 BTC/USDT"),
    timeframe: str = Query("1h", description="时间周期，如 1h"),
    limit: int = Query(120, ge=30, le=settings.API_MAX_LIMIT),
    account_size: float = Query(1000, ge=0),
    style: str = Query("Scalping"),
    strategy: str = Query("最大收益"),
    mode: str = Query("rules", pattern="^(rules|ai)$"),
    market_data_service: MarketDataService = Depends(get_market_data_service),
    service: BaseMarketAppService = Depends(get_base_market_app_service),
):
    try:
        return await service.get_trade_setup(
            market_data_service=market_data_service,
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            account_size=account_size,
            style=style,
            strategy=strategy,
            mode=mode,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise internal_error("API /trade-setup 错误", exc)


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
    service: BaseMarketAppService = Depends(get_base_market_app_service),
):
    try:
        return await service.get_crypto_index(top_n=top_n, days=days)
    except Exception as exc:
        logger.error(f"Crypto index API error: {exc}")
        raise HTTPException(status_code=500, detail="Failed to build crypto index")
