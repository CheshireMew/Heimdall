from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter

from app.domain.market.symbol_catalog import list_market_search_items
from app.schemas.market import ApiStatusResponse, MarketSymbolSearchResponse

router = APIRouter(tags=["Market Data"])


@router.get("/symbols", response_model=list[MarketSymbolSearchResponse])
async def list_market_symbols():
    return list_market_search_items()


@router.get("/status", response_model=ApiStatusResponse)
async def get_api_status():
    return ApiStatusResponse(
        status="running",
        version="2.0.0",
        framework="FastAPI",
        dependencies="ready",
        timestamp=datetime.now().isoformat(),
    )
