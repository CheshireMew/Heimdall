from __future__ import annotations

from fastapi import APIRouter

from app.routers.market.base import list_market_symbols, router as base_router
from app.routers.market.binance_market import router as binance_market_router
from app.routers.market.binance_web3 import router as binance_web3_router

router = APIRouter()
router.include_router(base_router)
router.include_router(binance_market_router)
router.include_router(binance_web3_router)

__all__ = ["router", "list_market_symbols"]
