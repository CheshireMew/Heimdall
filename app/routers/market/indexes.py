from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.dependencies import runtime_dependency
from app.rate_limit import limiter
from app.routers.errors import service_http_error
from app.schemas.market import MarketIndexHistoryResponse, MarketIndexResponse
from config import settings

if TYPE_CHECKING:
    from app.services.market.index_data_service import IndexDataService


router = APIRouter(tags=["Market Data"])
index_data_dependency = runtime_dependency("market.index_data_service")


@router.get("/indexes", response_model=list[MarketIndexResponse])
async def list_market_indexes(
    service: IndexDataService = Depends(index_data_dependency),
):
    return await service.list_indexes_async()


@router.get("/indexes/history", response_model=MarketIndexHistoryResponse)
@limiter.limit(settings.RATE_LIMIT_HISTORY)
async def get_index_history(
    request: Request,
    symbol: str = Query(..., description="指数 symbol, 如 US_SP500 或 CN_CSI300"),
    timeframe: str = Query("1d", description="第一版仅支持 1d"),
    start_date: str = Query("2010-01-01", description="Start Date YYYY-MM-DD"),
    end_date: str | None = Query(None, description="End Date YYYY-MM-DD"),
    service: IndexDataService = Depends(index_data_dependency),
):
    try:
        return await service.get_history_async(
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise service_http_error("Index History API Error", exc)


@router.get("/indexes/latest", response_model=MarketIndexHistoryResponse)
@limiter.limit(settings.RATE_LIMIT_HISTORY)
async def get_latest_index(
    request: Request,
    symbol: str = Query(..., description="指数 symbol, 如 US_SP500 或 CN_CSI300"),
    service: IndexDataService = Depends(index_data_dependency),
):
    try:
        return await service.get_latest_async(symbol=symbol)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise service_http_error("Latest Index API Error", exc)


@router.get("/indexes/pricing/history", response_model=MarketIndexHistoryResponse)
@limiter.limit(settings.RATE_LIMIT_HISTORY)
async def get_index_pricing_history(
    request: Request,
    symbol: str = Query(..., description="指数 symbol, 如 US_SP500 或 CN_CSI300"),
    timeframe: str = Query("1d", description="第一版仅支持 1d"),
    start_date: str = Query("2010-01-01", description="Start Date YYYY-MM-DD"),
    end_date: str | None = Query(None, description="End Date YYYY-MM-DD"),
    service: IndexDataService = Depends(index_data_dependency),
):
    try:
        return await service.get_pricing_history_async(
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise service_http_error("Index Pricing History API Error", exc)


@router.get("/indexes/pricing/latest", response_model=MarketIndexHistoryResponse)
@limiter.limit(settings.RATE_LIMIT_HISTORY)
async def get_latest_index_pricing(
    request: Request,
    symbol: str = Query(..., description="指数 symbol, 如 US_SP500 或 CN_CSI300"),
    service: IndexDataService = Depends(index_data_dependency),
):
    try:
        return await service.get_latest_pricing_async(symbol=symbol)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise service_http_error("Latest Index Pricing API Error", exc)
