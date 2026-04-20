from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from app.schemas.binance_market import BinanceBreakoutMonitorResponse, BinanceMarketPageResponse
from utils.logger import logger

from .binance_breakout_monitor import BinanceBreakoutMonitor
from .binance_spot_market import BinanceSpotMarketService
from .binance_usdm_market import BinanceUsdmMarketService

if TYPE_CHECKING:
    from .binance_market_snapshot_service import BinanceMarketSnapshotService


class BinanceMarketPageService:
    def __init__(
        self,
        *,
        spot: BinanceSpotMarketService,
        usdm: BinanceUsdmMarketService,
        snapshot_service: BinanceMarketSnapshotService | None,
    ) -> None:
        self.spot = spot
        self.usdm = usdm
        self.snapshot_service = snapshot_service
        self.breakout_monitor = BinanceBreakoutMonitor(self._get_market_klines)

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
        market_snapshot = await self._load_market_page_snapshot()
        monitor = await self.breakout_monitor.build(
            market_snapshot=market_snapshot,
            min_rise_pct=min_rise_pct,
            limit=limit,
            quote_asset=normalized_quote_asset,
        )
        return BinanceMarketPageResponse.model_validate({
            "exchange": "binance",
            "quote_asset": normalized_quote_asset,
            "updated_at": monitor["updated_at"],
            "monitor": monitor,
            "spot_ticker": market_snapshot["spot_ticker"],
            "usdm_ticker": market_snapshot["usdm_ticker"],
            "usdm_mark": market_snapshot["usdm_mark"],
            "load_errors": market_snapshot["load_errors"],
        })

    async def _load_market_page_snapshot(self) -> dict[str, Any]:
        if self.snapshot_service is not None:
            return (await self.snapshot_service.get_market_page_snapshot()).model_dump()

        source_plan = (
            ("spot_ticker", "现货榜单", self.spot.get_ticker_24hr, self.breakout_monitor.empty_ticker_response, "spot"),
            ("usdm_ticker", "U本位24H", self.usdm.get_ticker_24hr, self.breakout_monitor.empty_ticker_response, "usdm"),
            ("usdm_mark", "U本位Funding", self.usdm.get_mark_price, self.breakout_monitor.empty_mark_price_response, "usdm"),
        )
        raw_results = await asyncio.gather(*(loader() for _, _, loader, _, _ in source_plan), return_exceptions=True)
        snapshot: dict[str, Any] = {"load_errors": []}
        for (key, label, _, empty_factory, market), result in zip(source_plan, raw_results, strict=False):
            if isinstance(result, Exception):
                logger.warning("Binance market page source failed: %s (%s)", key, result)
                snapshot[key] = empty_factory(market)
                snapshot["load_errors"].append(label)
                continue
            snapshot[key] = result.model_dump() if hasattr(result, "model_dump") else result
        return snapshot

    async def _get_market_klines(self, market: str, symbol: str, interval: str, limit: int) -> dict[str, Any]:
        if market == "spot":
            return (await self.spot.get_klines(symbol=symbol, interval=interval, limit=limit)).model_dump()
        return (await self.usdm.get_klines(symbol=symbol, interval=interval, limit=limit)).model_dump()
