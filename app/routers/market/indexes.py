from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Query, Request

from app.dependencies import runtime_dependency
from app.runtime_graph import MARKET_INDEX_DATA_SERVICE
from app.rate_limit import limiter
from app.schemas.market import MarketIndexHistoryResponse, MarketIndexResponse, build_ohlcv_points
from config import settings

if TYPE_CHECKING:
    from app.services.market.index_data_service import IndexDataService, MarketIndexHistoryRecord, MarketIndexRecord


router = APIRouter(tags=["Market Data"])
index_data_dependency = runtime_dependency(MARKET_INDEX_DATA_SERVICE)


def _index_response(record: MarketIndexRecord) -> MarketIndexResponse:
    return MarketIndexResponse(
        symbol=record.symbol,
        name=record.name,
        market=record.market,
        currency=record.currency,
        pricing_symbol=record.pricing_symbol,
        pricing_name=record.pricing_name,
        pricing_currency=record.pricing_currency,
    )


def _index_history_response(record: MarketIndexHistoryRecord) -> MarketIndexHistoryResponse:
    return MarketIndexHistoryResponse(
        symbol=record.symbol,
        name=record.name,
        market=record.market,
        currency=record.currency,
        native_currency=record.native_currency,
        timeframe=record.timeframe,
        source=record.source,
        price_basis=record.price_basis,
        pricing_symbol=record.pricing_symbol,
        pricing_name=record.pricing_name,
        pricing_currency=record.pricing_currency,
        is_close_only=record.is_close_only,
        count=record.count,
        data=build_ohlcv_points([item.as_row() for item in record.data]),
    )


@router.get("/indexes", response_model=list[MarketIndexResponse])
async def list_market_indexes(
    service: IndexDataService = Depends(index_data_dependency),
):
    return [_index_response(record) for record in await service.list_indexes_async()]


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
    return _index_history_response(
        await service.get_history_async(
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
        )
    )


@router.get("/indexes/latest", response_model=MarketIndexHistoryResponse)
@limiter.limit(settings.RATE_LIMIT_HISTORY)
async def get_latest_index(
    request: Request,
    symbol: str = Query(..., description="指数 symbol, 如 US_SP500 或 CN_CSI300"),
    service: IndexDataService = Depends(index_data_dependency),
):
    return _index_history_response(await service.get_latest_async(symbol=symbol))


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
    return _index_history_response(
        await service.get_pricing_history_async(
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
        )
    )


@router.get("/indexes/pricing/latest", response_model=MarketIndexHistoryResponse)
@limiter.limit(settings.RATE_LIMIT_HISTORY)
async def get_latest_index_pricing(
    request: Request,
    symbol: str = Query(..., description="指数 symbol, 如 US_SP500 或 CN_CSI300"),
    service: IndexDataService = Depends(index_data_dependency),
):
    return _index_history_response(await service.get_latest_pricing_async(symbol=symbol))
