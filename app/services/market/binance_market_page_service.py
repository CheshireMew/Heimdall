from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Any

from app.contracts.dto.binance.page import (
    BinanceBreakoutMonitorResponse,
    BinanceMarketPageRefreshStatusResponse,
    BinanceMarketPageResponse,
)
from app.infra.executor import run_compute
from config import settings
from utils.logger import logger

from .binance_breakout_monitor import BinanceBreakoutMonitor
from .binance_contract_oi_enricher import BinanceContractOpenInterestEnricher
from .binance_market_board_builder import BinanceMarketBoardBuilder
from .binance_spot_market import BinanceSpotMarketService
from .binance_usdm_market import BinanceUsdmMarketService

if TYPE_CHECKING:
    from .binance_market_snapshot_service import BinanceMarketSnapshotService


DEFAULT_PAGE_CONFIGS = ((5.0, 24, "USDT"),)
PageKey = tuple[float, int, str]


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
        self.board_builder = BinanceMarketBoardBuilder()
        self.oi_enricher = BinanceContractOpenInterestEnricher(usdm)
        self._page_responses: dict[PageKey, BinanceMarketPageResponse] = {}
        self._requested_page_configs: set[PageKey] = {
            self._page_key(min_rise_pct=min_rise_pct, limit=limit, quote_asset=quote_asset)
            for min_rise_pct, limit, quote_asset in DEFAULT_PAGE_CONFIGS
        }
        self._lock = asyncio.Lock()
        self._refresh_event: asyncio.Event | None = None
        self._refresh_task: asyncio.Task[None] | None = None
        self._running = False
        self._refreshing = 0
        self._last_refresh_started_at: int | None = None
        self._last_refresh_completed_at: int | None = None
        self._last_refresh_error: str | None = None

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._refresh_event = asyncio.Event()
        self._refresh_task = asyncio.create_task(self._run_refresh_loop(), name="binance-market-page-refresh")

    async def shutdown(self) -> None:
        self._running = False
        if self._refresh_event is not None:
            self._refresh_event.set()
        task = self._refresh_task
        self._refresh_task = None
        if task is not None and not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)

    async def get_page(
        self,
        *,
        min_rise_pct: float = 5.0,
        limit: int = 24,
        quote_asset: str = "USDT",
    ) -> BinanceMarketPageResponse:
        key = self._page_key(min_rise_pct=min_rise_pct, limit=limit, quote_asset=quote_asset)
        should_notify_refresh = False
        async with self._lock:
            if key not in self._requested_page_configs:
                self._requested_page_configs.add(key)
                should_notify_refresh = True
            cached_response = self._page_responses.get(key)
            if cached_response is not None:
                return self._with_live_refresh_status(cached_response)

        if should_notify_refresh:
            self._request_refresh()
        return await self._build_pending_page(key)

    async def refresh_requested_payloads(self) -> None:
        async with self._lock:
            keys = sorted(self._requested_page_configs)
        for key in keys:
            try:
                await self.refresh_page(key)
            except Exception as exc:
                async with self._lock:
                    self._last_refresh_error = str(exc)
                logger.warning("Binance market page refresh failed: %s", exc)

    async def refresh_page(self, key: PageKey) -> BinanceMarketPageResponse:
        min_rise_pct, limit, quote_asset = key
        await self._mark_refresh_started()
        try:
            market_snapshot = await self._load_market_page_snapshot_for_refresh()
            ticker_rows = [item for item in market_snapshot["usdm_ticker"].get("items", [])]
            oi_changes = await self.oi_enricher.load_changes(ticker_rows)
            board_fields = await run_compute(
                lambda: self.board_builder.build_response_fields(
                    market_snapshot,
                    quote_asset=quote_asset,
                    oi_changes=oi_changes,
                )
            )
            monitor = await self.breakout_monitor.build(
                market_snapshot=market_snapshot,
                min_rise_pct=min_rise_pct,
                limit=limit,
                quote_asset=quote_asset,
            )
            response = BinanceMarketPageResponse.model_validate({
                "exchange": "binance",
                "quote_asset": quote_asset,
                "updated_at": max(int(monitor.get("updated_at") or 0), int(market_snapshot["updated_at"] or 0)),
                "monitor": monitor,
                **board_fields,
                "refresh_status": self._build_refresh_status(
                    snapshot_ready=not board_fields["load_errors"],
                    boards_ready=True,
                    monitor_ready=True,
                    oi_ready_count=sum(1 for summary in oi_changes.values() if summary),
                    oi_requested_count=len(self.oi_enricher.candidate_symbols(ticker_rows)),
                ),
            })
            async with self._lock:
                self._page_responses[key] = response
            return response
        finally:
            await self._mark_refresh_completed()

    async def _run_refresh_loop(self) -> None:
        while self._running:
            await self.refresh_requested_payloads()
            event = self._refresh_event
            if event is None:
                return
            try:
                await asyncio.wait_for(event.wait(), timeout=max(float(settings.BINANCE_MARKET_PAGE_REFRESH_INTERVAL), 1.0))
            except asyncio.TimeoutError:
                pass
            event.clear()

    async def _load_market_page_snapshot_for_refresh(self) -> dict[str, Any]:
        if not await self.snapshot_service.has_market_page_snapshot():
            await self.snapshot_service.seed(
                spot_ticker_loader=self.spot.get_ticker_24hr,
                usdm_ticker_loader=self.usdm.get_ticker_24hr,
                usdm_mark_loader=self.usdm.get_mark_price,
            )
        return await self.snapshot_service.get_market_page_snapshot_data()

    async def _get_market_klines(self, market: str, symbol: str, interval: str, limit: int) -> dict[str, Any]:
        if market == "spot":
            response = await self.spot.get_klines(symbol=symbol, interval=interval, limit=limit)
        else:
            response = await self.usdm.get_klines(symbol=symbol, interval=interval, limit=limit)
        return response.model_dump() if hasattr(response, "model_dump") else response

    async def _build_pending_page(self, key: PageKey) -> BinanceMarketPageResponse:
        min_rise_pct, limit, quote_asset = key
        market_snapshot = await self.snapshot_service.get_market_page_snapshot_data()
        board_fields = await run_compute(
            lambda: self.board_builder.build_response_fields(
                market_snapshot,
                quote_asset=quote_asset,
                oi_changes={},
            )
        )
        return BinanceMarketPageResponse.model_validate({
            "exchange": "binance",
            "quote_asset": quote_asset,
            "updated_at": int(market_snapshot["updated_at"] or 0),
            "monitor": self._empty_monitor(
                min_rise_pct=min_rise_pct,
                limit=limit,
                quote_asset=quote_asset,
                updated_at=int(market_snapshot["updated_at"] or 0),
            ),
            **board_fields,
            "refresh_status": self._build_refresh_status(
                snapshot_ready=not board_fields["load_errors"],
                boards_ready=True,
                monitor_ready=False,
                oi_ready_count=0,
                oi_requested_count=len(self.oi_enricher.candidate_symbols(market_snapshot["usdm_ticker"].get("items", []))),
            ),
        })

    def _empty_monitor(self, *, min_rise_pct: float, limit: int, quote_asset: str, updated_at: int) -> BinanceBreakoutMonitorResponse:
        return BinanceBreakoutMonitorResponse(
            exchange="binance",
            min_rise_pct=min_rise_pct,
            quote_asset=quote_asset,
            updated_at=updated_at,
            items=[],
        )

    def _page_key(self, *, min_rise_pct: float, limit: int, quote_asset: str) -> PageKey:
        return (float(min_rise_pct), int(limit), self.breakout_monitor.normalize_quote_asset(quote_asset))

    def _request_refresh(self) -> None:
        if self._refresh_event is not None:
            self._refresh_event.set()

    async def _mark_refresh_started(self) -> None:
        async with self._lock:
            self._refreshing += 1
            self._last_refresh_started_at = int(time.time() * 1000)
            self._last_refresh_error = None

    async def _mark_refresh_completed(self) -> None:
        async with self._lock:
            self._refreshing = max(0, self._refreshing - 1)
            self._last_refresh_completed_at = int(time.time() * 1000)

    def _build_refresh_status(
        self,
        *,
        snapshot_ready: bool,
        boards_ready: bool,
        monitor_ready: bool,
        oi_ready_count: int,
        oi_requested_count: int,
    ) -> BinanceMarketPageRefreshStatusResponse:
        return BinanceMarketPageRefreshStatusResponse(
            snapshot_ready=snapshot_ready,
            boards_ready=boards_ready,
            monitor_ready=monitor_ready,
            refreshing=self._refreshing > 0,
            oi_ready_count=oi_ready_count,
            oi_requested_count=oi_requested_count,
            last_refresh_started_at=self._last_refresh_started_at,
            last_refresh_completed_at=self._last_refresh_completed_at,
            last_refresh_error=self._last_refresh_error,
        )

    def _with_live_refresh_status(self, response: BinanceMarketPageResponse) -> BinanceMarketPageResponse:
        status = response.refresh_status.model_copy(update={
            "refreshing": self._refreshing > 0,
            "last_refresh_started_at": self._last_refresh_started_at,
            "last_refresh_completed_at": self._last_refresh_completed_at,
            "last_refresh_error": self._last_refresh_error,
        })
        return response.model_copy(update={"refresh_status": status})
