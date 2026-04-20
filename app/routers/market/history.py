from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.dependencies import runtime_dependency
from app.rate_limit import limiter
from app.routers.errors import service_http_error
from app.schemas.market import (
    CurrentPriceBatchResponse,
    CurrentPriceResponse,
    KlineTailResponse,
    MarketHistoryBatchResponse,
    MarketHistoryResponse,
)
from config import settings

if TYPE_CHECKING:
    from app.services.market.query_app_service import MarketQueryAppService


router = APIRouter(tags=["Market Data"])
market_query_dependency = runtime_dependency("market.market_query_app_service")


@router.get("/history", response_model=MarketHistoryResponse)
async def get_market_history(
    symbol: str = Query(..., description="Symbol eg BTC/USDT"),
    timeframe: str = Query(..., description="Timeframe eg 5m"),
    end_ts: int = Query(..., description="End Timestamp (ms)", gt=0),
    limit: int = Query(settings.HISTORY_DEFAULT_LIMIT, description="Limit", ge=1, le=settings.API_MAX_LIMIT),
    service: MarketQueryAppService = Depends(market_query_dependency),
):
    try:
        return await service.get_history(
            symbol=symbol,
            timeframe=timeframe,
            end_ts=end_ts,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise service_http_error("History API Error", exc)


@router.get("/klines/latest", response_model=MarketHistoryResponse)
async def get_latest_klines(
    symbol: str = Query(..., description="Symbol eg BTC/USDT"),
    timeframe: str = Query(..., description="Timeframe eg 5m"),
    limit: int = Query(settings.LIMIT, description="Limit", ge=1, le=settings.API_MAX_LIMIT),
    service: MarketQueryAppService = Depends(market_query_dependency),
):
    try:
        return await service.get_recent_klines(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise service_http_error("Latest klines API Error", exc)


@router.get("/klines/tail", response_model=KlineTailResponse)
async def get_kline_tail(
    symbol: str = Query(..., description="Symbol eg BTC/USDT"),
    timeframe: str = Query(..., description="Timeframe eg 5m"),
    limit: int = Query(2, description="Tail size", ge=1, le=20),
    service: MarketQueryAppService = Depends(market_query_dependency),
):
    try:
        return await service.get_live_kline_tail(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise service_http_error("Kline tail API Error", exc)


@router.get("/price/current", response_model=CurrentPriceResponse)
async def get_current_price(
    symbol: str = Query(..., description="Symbol eg BTC/USDT"),
    timeframe: str = Query("1d", description="Timeframe eg 1d"),
    service: MarketQueryAppService = Depends(market_query_dependency),
):
    try:
        return await service.get_current_price(
            symbol=symbol,
            timeframe=timeframe,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise service_http_error("Current price API Error", exc)


@router.get("/price/current/batch", response_model=CurrentPriceBatchResponse)
async def get_current_price_batch(
    symbols: list[str] = Query(..., description="Symbols eg BTC/USDT"),
    timeframe: str = Query("1d", description="Timeframe eg 1d"),
    service: MarketQueryAppService = Depends(market_query_dependency),
):
    try:
        return await service.get_current_price_batch(
            symbols=symbols,
            timeframe=timeframe,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise service_http_error("Current price batch API Error", exc)


@router.get("/full_history", response_model=MarketHistoryResponse)
@limiter.limit(settings.RATE_LIMIT_HISTORY)
async def get_market_full_history(
    request: Request,
    symbol: str = Query(..., description="Symbol eg BTC/USDT"),
    timeframe: str = Query("1d", description="Timeframe eg 1d"),
    start_date: str = Query("2010-01-01", description="Start Date YYYY-MM-DD"),
    fetch_policy: Literal["cache_only", "hydrate"] = Query("hydrate", description="History source policy"),
    service: MarketQueryAppService = Depends(market_query_dependency),
):
    try:
        return await service.get_full_history(
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            fetch_policy=fetch_policy,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise service_http_error("Full History API Error", exc)


@router.get("/full_history/batch", response_model=MarketHistoryBatchResponse)
@limiter.limit(settings.RATE_LIMIT_HISTORY)
async def get_market_full_history_batch(
    request: Request,
    symbols: list[str] = Query(..., description="交易对列表，如 BTC/USDT"),
    timeframe: str = Query("1d", description="Timeframe eg 1d"),
    start_date: str = Query("2010-01-01", description="Start Date YYYY-MM-DD"),
    fetch_policy: Literal["cache_only", "hydrate"] = Query("hydrate", description="History source policy"),
    service: MarketQueryAppService = Depends(market_query_dependency),
):
    try:
        return await service.get_full_history_batch(
            symbols=symbols,
            timeframe=timeframe,
            start_date=start_date,
            fetch_policy=fetch_policy,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise service_http_error("Batch Full History API Error", exc)
