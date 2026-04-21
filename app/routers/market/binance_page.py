from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Query

from app.dependencies import runtime_dependency
from app.runtime_graph import MARKET_BINANCE_MARKET_INTEL
from app.schemas.binance_market import BinanceBreakoutMonitorResponse, BinanceMarketPageResponse

if TYPE_CHECKING:
    from app.services.market.binance_market_intel_service import BinanceMarketIntelService


router = APIRouter(tags=["Market Data"])
binance_market_dependency = runtime_dependency(MARKET_BINANCE_MARKET_INTEL)


@router.get("/binance/market/page", response_model=BinanceMarketPageResponse)
async def get_binance_market_page(
    min_rise_pct: float = Query(5.0, ge=0.5, le=50.0),
    limit: int = Query(24, ge=1, le=30),
    quote_asset: str = Query("USDT", min_length=2, max_length=10),
    service: BinanceMarketIntelService = Depends(binance_market_dependency),
):
    return await service.page.get_page_payload(
        min_rise_pct=min_rise_pct,
        limit=limit,
        quote_asset=quote_asset,
    )


@router.get("/binance/market/breakout_monitor", response_model=BinanceBreakoutMonitorResponse)
async def get_binance_market_breakout_monitor(
    min_rise_pct: float = Query(5.0, ge=0.5, le=50.0),
    limit: int = Query(18, ge=1, le=30),
    quote_asset: str = Query("USDT", min_length=2, max_length=10),
    service: BinanceMarketIntelService = Depends(binance_market_dependency),
):
    return await service.page.get_breakout_monitor(
        min_rise_pct=min_rise_pct,
        limit=limit,
        quote_asset=quote_asset,
    )
