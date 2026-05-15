from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.dependencies import runtime_dependency
from app.router_service_ports import BinanceMarketPort
from app.runtime_refs import MARKET_BINANCE_MARKET_INTEL
from app.contracts.dto.binance.page import BinanceMarketPageResponse
from app.contracts.dto.binance.usdm import BinanceContractResearchDetailResponse


router = APIRouter(tags=["Market Data"])
binance_market_dependency = runtime_dependency(MARKET_BINANCE_MARKET_INTEL)


@router.get("/binance/market/page", response_model=BinanceMarketPageResponse)
async def get_binance_market_page(
    min_rise_pct: float = Query(5.0, ge=0.5, le=50.0),
    limit: int = Query(24, ge=1, le=30),
    quote_asset: str = Query("USDT", min_length=2, max_length=10),
    service: BinanceMarketPort = Depends(binance_market_dependency),
):
    return await service.page.get_page_payload(
        min_rise_pct=min_rise_pct,
        limit=limit,
        quote_asset=quote_asset,
    )


@router.get("/binance/market/contract_detail", response_model=BinanceContractResearchDetailResponse)
async def get_binance_market_contract_detail(
    symbol: str = Query(..., min_length=3, max_length=32),
    period: str = Query("1h"),
    limit: int = Query(72, ge=1, le=500),
    service: BinanceMarketPort = Depends(binance_market_dependency),
):
    return await service.usdm.get_contract_research_detail(symbol=symbol, period=period, limit=limit)
