from __future__ import annotations

import asyncio
import time
from functools import cmp_to_key
from typing import TYPE_CHECKING, Any

from app.schemas.binance_market import (
    BinanceBreakoutMonitorResponse,
    BinanceContractBoardResponse,
    BinanceMarketPageResponse,
    BinanceMarketPageRefreshStatusResponse,
    BinanceTickerStatsResponse,
)
from config import settings
from utils.logger import logger

from .binance_breakout_monitor import BinanceBreakoutMonitor
from .binance_spot_market import BinanceSpotMarketService
from .binance_usdm_market import BinanceUsdmMarketService

if TYPE_CHECKING:
    from .binance_market_snapshot_service import BinanceMarketSnapshotService


CONTRACT_OI_CACHE_TTL_SECONDS = 300.0
CONTRACT_OI_ENRICHMENT_TIMEOUT_SECONDS = 8.0
CONTRACT_OI_REQUEST_TIMEOUT_SECONDS = 2.5
MARKET_BOARD_LIMIT = 15
CONTRACT_OI_CANDIDATE_LIMIT = 80
SPOT_BOARD_FIELDS = ("price_change_pct", "quote_volume")
CONTRACT_BOARD_FIELDS = ("price_change_pct", "funding_rate_pct", "quote_volume", "oi_change_24h_pct")
BOARD_DIRECTIONS = ("desc", "asc")
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
        self._page_payloads: dict[PageKey, BinanceMarketPageResponse] = {}
        self._requested_page_configs: set[PageKey] = {
            self._page_key(min_rise_pct=min_rise_pct, limit=limit, quote_asset=quote_asset)
            for min_rise_pct, limit, quote_asset in DEFAULT_PAGE_CONFIGS
        }
        self._contract_oi_cache: dict[str, tuple[float, dict[str, float | None]]] = {}
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

    async def get_page_payload(
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
            cached_payload = self._page_payloads.get(key)
            if cached_payload is not None:
                return self._with_live_refresh_status(cached_payload)

        if should_notify_refresh:
            self._request_refresh()
        return await self._build_pending_page_payload(key)

    async def refresh_requested_payloads(self) -> None:
        async with self._lock:
            keys = sorted(self._requested_page_configs)
        for key in keys:
            try:
                await self.refresh_page_payload(key)
            except Exception as exc:
                async with self._lock:
                    self._last_refresh_error = str(exc)
                logger.warning("Binance market page refresh failed: %s", exc)

    async def refresh_page_payload(self, key: PageKey) -> BinanceMarketPageResponse:
        min_rise_pct, limit, quote_asset = key
        await self._mark_refresh_started()
        try:
            market_snapshot = await self._load_market_page_snapshot_for_refresh()
            ticker_rows = [item for item in market_snapshot["usdm_ticker"].get("items", [])]
            oi_changes = await self._load_contract_oi_changes(ticker_rows)
            board_fields = self._build_boards_response_fields(
                market_snapshot,
                quote_asset=quote_asset,
                oi_changes=oi_changes,
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
                    oi_requested_count=len(self._contract_oi_candidate_symbols(ticker_rows)),
                ),
            })
            async with self._lock:
                self._page_payloads[key] = response.model_copy(deep=True)
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
        return (await self.snapshot_service.get_market_page_snapshot()).model_dump()

    async def _get_market_klines(self, market: str, symbol: str, interval: str, limit: int) -> dict[str, Any]:
        if market == "spot":
            return (await self.spot.get_klines(symbol=symbol, interval=interval, limit=limit)).model_dump()
        return (await self.usdm.get_klines(symbol=symbol, interval=interval, limit=limit)).model_dump()

    def _build_boards_response_fields(
        self,
        market_snapshot: dict[str, Any],
        *,
        quote_asset: str,
        oi_changes: dict[str, dict[str, float | None]],
    ) -> dict[str, Any]:
        return {
            "spot_boards": self._build_spot_boards(market_snapshot, quote_asset=quote_asset),
            "contract_boards": self._build_contract_boards(market_snapshot, oi_changes=oi_changes),
            "load_errors": market_snapshot["load_errors"],
        }

    def _build_spot_boards(self, market_snapshot: dict[str, Any], *, quote_asset: str) -> dict[str, BinanceTickerStatsResponse]:
        rows = [
            item
            for item in market_snapshot["spot_ticker"].get("items", [])
            if str(item.get("symbol") or "").upper().endswith(quote_asset)
        ]
        return {
            self._board_key(field, direction): BinanceTickerStatsResponse.model_validate({
                "exchange": "binance",
                "market": "spot",
                "items": self._sort_rows(rows, field, direction)[:MARKET_BOARD_LIMIT],
            })
            for field in SPOT_BOARD_FIELDS
            for direction in BOARD_DIRECTIONS
        }

    def _build_contract_boards(
        self,
        market_snapshot: dict[str, Any],
        *,
        oi_changes: dict[str, dict[str, float | None]],
    ) -> dict[str, BinanceContractBoardResponse]:
        mark_map = {
            str(item.get("symbol") or "").upper(): item
            for item in market_snapshot["usdm_mark"].get("items", [])
        }
        ticker_rows = [item for item in market_snapshot["usdm_ticker"].get("items", [])]
        rows = []
        for item in ticker_rows:
            symbol = str(item.get("symbol") or "").upper()
            mark = mark_map.get(symbol, {})
            oi = oi_changes.get(symbol, {})
            rows.append({
                **item,
                "market": "usdm",
                "market_label": "U 鏈綅",
                "mark_price": mark.get("mark_price"),
                "index_price": mark.get("index_price"),
                "funding_rate_pct": self._funding_rate_pct(mark.get("last_funding_rate")),
                "open_interest": oi.get("open_interest"),
                "open_interest_value": oi.get("open_interest_value"),
                "oi_change_1h_pct": oi.get("oi_change_1h_pct"),
                "oi_change_4h_pct": oi.get("oi_change_4h_pct"),
                "oi_change_24h_pct": oi.get("oi_change_24h_pct"),
            })
        return {
            self._board_key(field, direction): BinanceContractBoardResponse.model_validate({
                "exchange": "binance",
                "market": "usdm",
                "items": self._sort_rows(rows, field, direction)[:MARKET_BOARD_LIMIT],
            })
            for field in CONTRACT_BOARD_FIELDS
            for direction in BOARD_DIRECTIONS
        }

    async def _load_contract_oi_changes(self, rows: list[dict[str, Any]]) -> dict[str, dict[str, float | None]]:
        symbols = self._contract_oi_candidate_symbols(rows)
        if not symbols:
            return {}

        async def load(symbol: str) -> tuple[str, dict[str, float | None]]:
            cached = self._read_contract_oi_cache(symbol)
            if cached is not None:
                return symbol, cached

            stored_response = self.usdm.get_cached_open_interest_stats(symbol=symbol, period="1h", limit=25)
            summary = self._summarize_open_interest_change(stored_response.model_dump().get("items", []))
            if summary:
                self._write_contract_oi_cache(symbol, summary)
                return symbol, summary

            try:
                response = await asyncio.wait_for(
                    self.usdm.get_open_interest_stats(symbol=symbol, period="1h", limit=25),
                    timeout=CONTRACT_OI_REQUEST_TIMEOUT_SECONDS,
                )
                summary = self._summarize_open_interest_change(response.model_dump().get("items", []))
            except Exception:
                summary = {}
            self._write_contract_oi_cache(symbol, summary)
            return symbol, summary

        semaphore = asyncio.Semaphore(8)

        async def guarded(symbol: str) -> tuple[str, dict[str, float | None]]:
            async with semaphore:
                return await load(symbol)

        tasks = [asyncio.create_task(guarded(symbol)) for symbol in symbols]
        done, pending = await asyncio.wait(tasks, timeout=CONTRACT_OI_ENRICHMENT_TIMEOUT_SECONDS)
        for task in pending:
            task.cancel()
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)

        pairs: list[tuple[str, dict[str, float | None]]] = []
        for task in done:
            if task.cancelled():
                continue
            try:
                pairs.append(task.result())
            except Exception:
                continue
        return {symbol: summary for symbol, summary in pairs}

    def _contract_oi_candidate_symbols(self, rows: list[dict[str, Any]]) -> list[str]:
        sorted_rows = sorted(
            rows,
            key=lambda item: self._to_float(item.get("quote_volume")) or 0.0,
            reverse=True,
        )
        return [
            str(item.get("symbol") or "").upper()
            for item in sorted_rows[:CONTRACT_OI_CANDIDATE_LIMIT]
            if str(item.get("symbol") or "").upper().endswith("USDT")
        ]

    def _summarize_open_interest_change(self, items: list[dict[str, Any]]) -> dict[str, float | None]:
        ordered = [item for item in items if self._to_float(item.get("sum_open_interest")) is not None]
        if not ordered:
            return {}
        latest = ordered[-1]
        return {
            "open_interest": self._to_float(latest.get("sum_open_interest")),
            "open_interest_value": self._to_float(latest.get("sum_open_interest_value")),
            "oi_change_1h_pct": self._change_pct(ordered, 1),
            "oi_change_4h_pct": self._change_pct(ordered, 4),
            "oi_change_24h_pct": self._change_pct(ordered, 24),
        }

    def _change_pct(self, items: list[dict[str, Any]], lookback: int) -> float | None:
        if len(items) <= lookback:
            return None
        current = self._to_float(items[-1].get("sum_open_interest"))
        previous = self._to_float(items[-1 - lookback].get("sum_open_interest"))
        if current is None or previous in (None, 0):
            return None
        return (current - previous) / previous * 100

    def _read_contract_oi_cache(self, symbol: str) -> dict[str, float | None] | None:
        cached = self._contract_oi_cache.get(symbol)
        if cached is None:
            return None
        expires_at, summary = cached
        if expires_at <= time.monotonic():
            self._contract_oi_cache.pop(symbol, None)
            return None
        return dict(summary)

    def _write_contract_oi_cache(self, symbol: str, summary: dict[str, float | None]) -> None:
        self._contract_oi_cache[symbol] = (time.monotonic() + CONTRACT_OI_CACHE_TTL_SECONDS, dict(summary))

    async def _build_pending_page_payload(self, key: PageKey) -> BinanceMarketPageResponse:
        min_rise_pct, limit, quote_asset = key
        market_snapshot = (await self.snapshot_service.get_market_page_snapshot()).model_dump()
        board_fields = self._build_boards_response_fields(
            market_snapshot,
            quote_asset=quote_asset,
            oi_changes={},
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
                oi_requested_count=len(self._contract_oi_candidate_symbols(market_snapshot["usdm_ticker"].get("items", []))),
            ),
        })

    def _empty_monitor(self, *, min_rise_pct: float, limit: int, quote_asset: str, updated_at: int) -> BinanceBreakoutMonitorResponse:
        return BinanceBreakoutMonitorResponse.model_validate({
            "exchange": "binance",
            "min_rise_pct": min_rise_pct,
            "quote_asset": quote_asset,
            "updated_at": updated_at,
            "items": [],
        })

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
        return response.model_copy(update={"refresh_status": status}, deep=True)

    def _sort_rows(self, rows: list[dict[str, Any]], field: str, direction: str) -> list[dict[str, Any]]:
        return sorted(
            rows,
            key=cmp_to_key(lambda left, right: self._compare_rows(left, right, field, direction)),
        )

    def _compare_rows(self, left: dict[str, Any], right: dict[str, Any], field: str, direction: str) -> int:
        primary = self._compare_nullable_number(left.get(field), right.get(field), direction)
        if primary != 0:
            return primary
        by_volume = self._compare_nullable_number(left.get("quote_volume"), right.get("quote_volume"), "desc")
        if by_volume != 0:
            return by_volume
        left_symbol = str(left.get("symbol") or "")
        right_symbol = str(right.get("symbol") or "")
        return (left_symbol > right_symbol) - (left_symbol < right_symbol)

    def _compare_nullable_number(self, left: Any, right: Any, direction: str) -> int:
        left_value = self._to_float(left)
        right_value = self._to_float(right)
        if left_value is None and right_value is None:
            return 0
        if left_value is None:
            return 1
        if right_value is None:
            return -1
        if left_value == right_value:
            return 0
        if direction == "desc":
            return -1 if left_value > right_value else 1
        return -1 if left_value < right_value else 1

    def _funding_rate_pct(self, value: Any) -> float | None:
        numeric = self._to_float(value)
        return None if numeric is None else numeric * 100

    def _to_float(self, value: Any) -> float | None:
        try:
            if value in (None, ""):
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    def _board_key(self, field: str, direction: str) -> str:
        return f"{field}_{direction}"
