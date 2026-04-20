from __future__ import annotations

import asyncio
import json
import time
from collections.abc import Awaitable, Callable
from typing import Any

import websockets

from app.schemas.binance_market import (
    BinanceMarkPriceResponse,
    BinanceMarketSourceSnapshotResponse,
    BinanceTickerStatsResponse,
)
from config import settings
from utils.logger import logger


TickerLoader = Callable[[], Awaitable[Any]]
MarkPriceLoader = Callable[[], Awaitable[Any]]


class BinanceMarketSnapshotService:
    def __init__(self) -> None:
        self._spot_ticker: dict[str, dict[str, Any]] = {}
        self._usdm_ticker: dict[str, dict[str, Any]] = {}
        self._usdm_mark: dict[str, dict[str, Any]] = {}
        self._updated_at: dict[str, int] = {}
        self._lock = asyncio.Lock()
        self._tasks: list[asyncio.Task] = []
        self._running = False
        self._reconnect_delay = settings.BINANCE_MARKET_SNAPSHOT_RECONNECT_DELAY

    async def start(
        self,
        *,
        spot_ticker_loader: TickerLoader | None = None,
        usdm_ticker_loader: TickerLoader | None = None,
        usdm_mark_loader: MarkPriceLoader | None = None,
    ) -> None:
        if self._running:
            return
        self._running = True
        await self.seed(
            spot_ticker_loader=spot_ticker_loader,
            usdm_ticker_loader=usdm_ticker_loader,
            usdm_mark_loader=usdm_mark_loader,
        )
        self._tasks = [
            asyncio.create_task(self._run_spot_ticker_loop(), name="binance-spot-ticker-snapshot"),
            asyncio.create_task(self._run_usdm_ticker_loop(), name="binance-usdm-ticker-snapshot"),
            asyncio.create_task(self._run_usdm_mark_loop(), name="binance-usdm-mark-snapshot"),
        ]

    async def shutdown(self) -> None:
        self._running = False
        tasks = [task for task in self._tasks if not task.done()]
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self._tasks = []

    async def seed(
        self,
        *,
        spot_ticker_loader: TickerLoader | None = None,
        usdm_ticker_loader: TickerLoader | None = None,
        usdm_mark_loader: MarkPriceLoader | None = None,
    ) -> None:
        loaders = (
            ("spot_ticker", spot_ticker_loader, self._apply_spot_ticker_response),
            ("usdm_ticker", usdm_ticker_loader, self._apply_usdm_ticker_response),
            ("usdm_mark", usdm_mark_loader, self._apply_usdm_mark_response),
        )
        results = await asyncio.gather(
            *(loader() for _, loader, _ in loaders if loader is not None),
            return_exceptions=True,
        )
        result_index = 0
        for key, loader, applier in loaders:
            if loader is None:
                continue
            result = results[result_index]
            result_index += 1
            if isinstance(result, Exception):
                logger.warning("Binance snapshot seed failed: %s (%s)", key, result)
                continue
            await applier(result)

    async def get_market_page_snapshot(self) -> BinanceMarketSourceSnapshotResponse:
        async with self._lock:
            load_errors: list[str] = []
            if not self._spot_ticker:
                load_errors.append("现货榜单")
            if not self._usdm_ticker:
                load_errors.append("U本位24H")
            if not self._usdm_mark:
                load_errors.append("U本位Funding")
            return BinanceMarketSourceSnapshotResponse(
                spot_ticker=self._ticker_response("spot", self._spot_ticker.values()),
                usdm_ticker=self._ticker_response("usdm", self._usdm_ticker.values()),
                usdm_mark=self._mark_response("usdm", self._usdm_mark.values()),
                load_errors=load_errors,
                updated_at=max(self._updated_at.values(), default=0),
            )

    async def has_snapshot(self) -> bool:
        async with self._lock:
            return bool(self._spot_ticker or self._usdm_ticker or self._usdm_mark)

    async def get_current_price(self, symbol: str) -> float | None:
        ticker_symbol = self._to_ticker_symbol(symbol)
        if not ticker_symbol:
            return None
        async with self._lock:
            spot = self._spot_ticker.get(ticker_symbol)
            if spot is not None:
                return self._to_float(spot.get("last_price"))
            mark = self._usdm_mark.get(ticker_symbol)
            if mark is not None:
                return self._to_float(mark.get("mark_price"))
            usdm = self._usdm_ticker.get(ticker_symbol)
            if usdm is not None:
                return self._to_float(usdm.get("last_price"))
        return None

    async def _apply_spot_ticker_response(self, response: Any) -> None:
        payload = response.model_dump() if hasattr(response, "model_dump") else response
        await self._merge_tickers("spot", payload.get("items", []))

    async def _apply_usdm_ticker_response(self, response: Any) -> None:
        payload = response.model_dump() if hasattr(response, "model_dump") else response
        await self._merge_tickers("usdm_ticker", payload.get("items", []))

    async def _apply_usdm_mark_response(self, response: Any) -> None:
        payload = response.model_dump() if hasattr(response, "model_dump") else response
        await self._merge_marks(payload.get("items", []))

    async def _run_spot_ticker_loop(self) -> None:
        await self._consume_json_array_stream(
            settings.BINANCE_SPOT_WS_URL,
            self._apply_spot_ticker_events,
            "spot ticker",
        )

    async def _run_usdm_ticker_loop(self) -> None:
        await self._consume_json_array_stream(
            settings.BINANCE_FUTURES_USDM_TICKER_WS_URL,
            self._apply_usdm_ticker_events,
            "usdm ticker",
        )

    async def _run_usdm_mark_loop(self) -> None:
        await self._consume_json_array_stream(
            settings.BINANCE_FUTURES_USDM_MARK_WS_URL,
            self._apply_usdm_mark_events,
            "usdm mark",
        )

    async def _consume_json_array_stream(
        self,
        url: str,
        handler: Callable[[list[dict[str, Any]]], Awaitable[None]],
        label: str,
    ) -> None:
        while self._running:
            try:
                async with websockets.connect(url, ping_interval=20, ping_timeout=20) as websocket:
                    logger.info("Binance snapshot WebSocket connected: %s", label)
                    async for message in websocket:
                        payload = json.loads(message)
                        events = payload if isinstance(payload, list) else [payload]
                        await handler([event for event in events if isinstance(event, dict)])
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                if self._running:
                    logger.warning("Binance snapshot WebSocket disconnected: %s (%s)", label, exc)
                    await asyncio.sleep(self._reconnect_delay)

    async def _apply_spot_ticker_events(self, events: list[dict[str, Any]]) -> None:
        await self._merge_tickers("spot", [self._ticker_from_event(event) for event in events])

    async def _apply_usdm_ticker_events(self, events: list[dict[str, Any]]) -> None:
        await self._merge_tickers("usdm_ticker", [self._ticker_from_event(event) for event in events])

    async def _apply_usdm_mark_events(self, events: list[dict[str, Any]]) -> None:
        await self._merge_marks([self._mark_from_event(event) for event in events])

    async def _merge_tickers(self, scope: str, rows: list[dict[str, Any]]) -> None:
        now = int(time.time() * 1000)
        target = self._spot_ticker if scope == "spot" else self._usdm_ticker
        async with self._lock:
            for row in rows:
                symbol = str(row.get("symbol") or "").upper()
                if symbol:
                    target[symbol] = row
            self._updated_at[scope] = now

    async def _merge_marks(self, rows: list[dict[str, Any]]) -> None:
        now = int(time.time() * 1000)
        async with self._lock:
            for row in rows:
                symbol = str(row.get("symbol") or "").upper()
                if symbol:
                    self._usdm_mark[symbol] = row
            self._updated_at["usdm_mark"] = now

    def _ticker_from_event(self, event: dict[str, Any]) -> dict[str, Any]:
        return {
            "symbol": event.get("s"),
            "price_change": self._to_float(event.get("p")),
            "price_change_pct": self._to_float(event.get("P")),
            "weighted_avg_price": self._to_float(event.get("w")),
            "last_price": self._to_float(event.get("c")),
            "last_qty": self._to_float(event.get("Q")),
            "open_price": self._to_float(event.get("o")),
            "high_price": self._to_float(event.get("h")),
            "low_price": self._to_float(event.get("l")),
            "volume": self._to_float(event.get("v")),
            "quote_volume": self._to_float(event.get("q")),
            "open_time": self._to_int(event.get("O")),
            "close_time": self._to_int(event.get("C")),
            "count": self._to_int(event.get("n")),
        }

    def _mark_from_event(self, event: dict[str, Any]) -> dict[str, Any]:
        return {
            "symbol": event.get("s"),
            "pair": None,
            "mark_price": self._to_float(event.get("p")),
            "index_price": self._to_float(event.get("i")),
            "estimated_settle_price": self._to_float(event.get("P")),
            "last_funding_rate": self._to_float(event.get("r")),
            "next_funding_time": self._to_int(event.get("T")),
            "interest_rate": None,
            "time": self._to_int(event.get("E")),
        }

    def _ticker_response(self, market: str, rows: Any) -> BinanceTickerStatsResponse:
        return BinanceTickerStatsResponse.model_validate({
            "exchange": "binance",
            "market": market,
            "items": sorted(list(rows), key=lambda item: item.get("quote_volume") or 0, reverse=True),
        })

    def _mark_response(self, market: str, rows: Any) -> BinanceMarkPriceResponse:
        return BinanceMarkPriceResponse.model_validate({
            "exchange": "binance",
            "market": market,
            "items": sorted(list(rows), key=lambda item: item.get("symbol") or ""),
        })

    def _to_float(self, value: Any) -> float | None:
        try:
            if value in (None, ""):
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    def _to_int(self, value: Any) -> int | None:
        try:
            if value in (None, ""):
                return None
            return int(value)
        except (TypeError, ValueError):
            return None

    def _to_ticker_symbol(self, symbol: str) -> str:
        normalized = str(symbol or "").strip().upper()
        if not normalized:
            return ""
        return normalized.replace("/", "")
