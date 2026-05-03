from __future__ import annotations

from typing import TYPE_CHECKING

from config import settings

from .binance_api_support import BinanceApiSupport
from .binance_market_page_service import BinanceMarketPageService
from .binance_market_snapshot_service import BinanceMarketSnapshotService
from .binance_spot_market import BinanceSpotMarketService
from .binance_usdm_market import BinanceUsdmMarketService

if TYPE_CHECKING:
    from app.infra.cache import RedisService


class BinanceMarketIntelService:
    def __init__(
        self,
        snapshot_service: BinanceMarketSnapshotService | None = None,
        cache_service: RedisService | None = None,
    ) -> None:
        spot_client = BinanceApiSupport(
            base_url=settings.BINANCE_PUBLIC_BASE_URL,
            cache_namespace="binance:spot",
            user_agent="heimdall/market-intel",
            cache_service=cache_service,
        )
        usdm_client = BinanceApiSupport(
            base_url=settings.BINANCE_FUTURES_USDM_BASE_URL,
            cache_namespace="binance:usdm",
            user_agent="heimdall/market-intel",
            cache_service=cache_service,
        )
        self.spot = BinanceSpotMarketService(spot_client)
        self.usdm = BinanceUsdmMarketService(usdm_client)
        self.snapshot_service = snapshot_service or BinanceMarketSnapshotService()
        self.page = BinanceMarketPageService(
            spot=self.spot,
            usdm=self.usdm,
            snapshot_service=self.snapshot_service,
        )
