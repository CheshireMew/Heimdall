from __future__ import annotations

from fastapi import APIRouter

from app.routers.market.binance_page import router as binance_page_router
from app.routers.market.binance_rwa import router as binance_rwa_router
from app.routers.market.binance_spot import router as binance_spot_router
from app.routers.market.binance_usdm import router as binance_usdm_router
from app.routers.market.binance_web3_ranks import router as binance_web3_ranks_router
from app.routers.market.binance_web3_tokens import router as binance_web3_tokens_router
from app.routers.market.catalog import list_market_symbols, router as catalog_router
from app.routers.market.funding import router as funding_router
from app.routers.market.history import router as history_router
from app.routers.market.indexes import router as indexes_router
from app.routers.market.insight import router as insight_router
from app.routers.market.realtime import router as realtime_router

router = APIRouter()
router.include_router(catalog_router)
router.include_router(realtime_router)
router.include_router(history_router)
router.include_router(indexes_router)
router.include_router(funding_router)
router.include_router(insight_router)
router.include_router(binance_page_router)
router.include_router(binance_spot_router)
router.include_router(binance_usdm_router)
router.include_router(binance_web3_ranks_router)
router.include_router(binance_rwa_router)
router.include_router(binance_web3_tokens_router)

__all__ = ["router", "list_market_symbols"]
