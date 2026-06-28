from __future__ import annotations

from fastapi import Depends, Query

from app.contracts.frontend import FrontendContractRouter
from app.dependencies import get_binance_market_intel_service
from app.contracts.dto.binance.page import BinanceMarketPageResponse
from app.contracts.dto.binance.usdm import BinanceContractResearchDetailResponse


router = FrontendContractRouter(frontend_contract_target="market", tags=["Market Data"])


@router.get("/binance/market/page", response_model=BinanceMarketPageResponse)
async def get_binance_market_page(
    min_rise_pct: float = Query(5.0, ge=0.5, le=50.0),
    limit: int = Query(24, ge=1, le=30),
    quote_asset: str = Query("USDT", min_length=2, max_length=10),
    service = Depends(get_binance_market_intel_service),
):
    return await service.page.get_page(
        min_rise_pct=min_rise_pct,
        limit=limit,
        quote_asset=quote_asset,
    )


@router.get("/binance/market/contract_detail", response_model=BinanceContractResearchDetailResponse)
async def get_binance_market_contract_detail(
    symbol: str = Query(..., min_length=3, max_length=32),
    period: str = Query("1h"),
    limit: int = Query(72, ge=1, le=500),
    service = Depends(get_binance_market_intel_service),
):
    return await service.usdm.get_contract_research_detail(symbol=symbol, period=period, limit=limit)
