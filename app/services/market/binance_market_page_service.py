from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from app.schemas.binance_market import BinanceBreakoutMonitorResponse, BinanceMarketPageResponse

from .binance_breakout_monitor import BinanceBreakoutMonitor
from .binance_spot_market import BinanceSpotMarketService
from .binance_usdm_market import BinanceUsdmMarketService

if TYPE_CHECKING:
    from .binance_market_snapshot_service import BinanceMarketSnapshotService


PAGE_PAYLOAD_CACHE_TTL_SECONDS = 20.0


class BinanceMarketPageService:
    def __init__(
        self,
        *,
        spot: BinanceSpotMarketService,
        usdm: BinanceUsdmMarketService,
        snapshot_service: BinanceMarketSnapshotService,
    ) -> None:
        self.spot = spot
        self.usdm = usdm
        self.snapshot_service = snapshot_service
        self.breakout_monitor = BinanceBreakoutMonitor(self._get_market_klines)
        self._page_payload_cache: dict[tuple[float, int, str], tuple[float, BinanceMarketPageResponse]] = {}

    async def get_breakout_monitor(
        self,
        *,
        min_rise_pct: float = 5.0,
        limit: int = 18,
        quote_asset: str = "USDT",
    ) -> BinanceBreakoutMonitorResponse:
        normalized_quote_asset = self.breakout_monitor.normalize_quote_asset(quote_asset)
        market_snapshot = await self._load_market_page_snapshot()
        return BinanceBreakoutMonitorResponse.model_validate(await self.breakout_monitor.build(
            market_snapshot=market_snapshot,
            min_rise_pct=min_rise_pct,
            limit=limit,
            quote_asset=normalized_quote_asset,
        ))

    async def get_page_payload(
        self,
        *,
        min_rise_pct: float = 5.0,
        limit: int = 24,
        quote_asset: str = "USDT",
    ) -> BinanceMarketPageResponse:
        normalized_quote_asset = self.breakout_monitor.normalize_quote_asset(quote_asset)
        cache_key = (float(min_rise_pct), int(limit), normalized_quote_asset)
        cached_payload = self._read_page_payload_cache(cache_key)
        if cached_payload is not None:
            return cached_payload

        market_snapshot = await self._load_market_page_snapshot()
        monitor = await self.breakout_monitor.build(
            market_snapshot=market_snapshot,
            min_rise_pct=min_rise_pct,
            limit=limit,
            quote_asset=normalized_quote_asset,
        )
        response = BinanceMarketPageResponse.model_validate({
            "exchange": "binance",
            "quote_asset": normalized_quote_asset,
            "updated_at": monitor["updated_at"],
            "monitor": monitor,
            "spot_ticker": market_snapshot["spot_ticker"],
            "usdm_ticker": market_snapshot["usdm_ticker"],
            "usdm_mark": market_snapshot["usdm_mark"],
            "load_errors": market_snapshot["load_errors"],
        })
        if not response.load_errors:
            self._write_page_payload_cache(cache_key, response)
        return response

    def _read_page_payload_cache(self, key: tuple[float, int, str]) -> BinanceMarketPageResponse | None:
        cached = self._page_payload_cache.get(key)
        if cached is None:
            return None
        expires_at, response = cached
        if expires_at <= time.monotonic():
            self._page_payload_cache.pop(key, None)
            return None
        return response.model_copy(deep=True)

    def _write_page_payload_cache(self, key: tuple[float, int, str], response: BinanceMarketPageResponse) -> None:
        self._page_payload_cache[key] = (
            time.monotonic() + PAGE_PAYLOAD_CACHE_TTL_SECONDS,
            response.model_copy(deep=True),
        )

    async def _load_market_page_snapshot(self) -> dict[str, Any]:
        if not await self.snapshot_service.has_market_page_snapshot():
            await self.snapshot_service.seed(
                spot_ticker_loader=self.spot.get_ticker_24hr,
                usdm_ticker_loader=self.usdm.get_ticker_24hr,
                usdm_mark_loader=self.usdm.get_mark_price,
        )
        return (await self.snapshot_service.get_market_page_snapshot()).model_dump()

    async def _get_market_klines(self, market: str, symbol: str, interval: str, limit: int) -> dict[str, Any]:
        if market == "spot":
            return (await self.spot.get_klines(symbol=symbol, interval=interval, limit=limit)).model_dump()
        return (await self.usdm.get_klines(symbol=symbol, interval=interval, limit=limit)).model_dump()
