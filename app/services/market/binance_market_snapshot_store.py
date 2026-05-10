from __future__ import annotations

import asyncio
import time
from typing import Any

from .binance_numbers import safe_float


class BinanceMarketSnapshotStore:
    def __init__(self) -> None:
        self._spot_ticker: dict[str, dict[str, Any]] = {}
        self._usdm_ticker: dict[str, dict[str, Any]] = {}
        self._usdm_mark: dict[str, dict[str, Any]] = {}
        self._loaded_sources: set[str] = set()
        self._updated_at: dict[str, int] = {}
        self._lock = asyncio.Lock()

    async def market_page_snapshot(self) -> dict[str, Any]:
        return await self.market_page_snapshot_data()

    async def market_page_snapshot_data(self) -> dict[str, Any]:
        async with self._lock:
            load_errors: list[str] = []
            if "spot_ticker" not in self._loaded_sources:
                load_errors.append("现货榜单")
            if "usdm_ticker" not in self._loaded_sources:
                load_errors.append("U本位24H")
            if "usdm_mark" not in self._loaded_sources:
                load_errors.append("U本位Funding")
            return {
                "spot_ticker": self._ticker_payload("spot", self._spot_ticker.values()),
                "usdm_ticker": self._ticker_payload("usdm", self._usdm_ticker.values()),
                "usdm_mark": self._mark_payload("usdm", self._usdm_mark.values()),
                "load_errors": load_errors,
                "updated_at": max(self._updated_at.values(), default=0),
            }

    async def has_snapshot(self) -> bool:
        async with self._lock:
            return bool(self._loaded_sources)

    async def has_market_page_snapshot(self) -> bool:
        async with self._lock:
            return {"spot_ticker", "usdm_ticker", "usdm_mark"}.issubset(self._loaded_sources)

    async def current_price(self, symbol: str) -> float | None:
        ticker_symbol = self._to_ticker_symbol(symbol)
        if not ticker_symbol:
            return None
        async with self._lock:
            spot = self._spot_ticker.get(ticker_symbol)
            if spot is not None:
                return safe_float(spot.get("last_price"))
            mark = self._usdm_mark.get(ticker_symbol)
            if mark is not None:
                return safe_float(mark.get("mark_price"))
            usdm = self._usdm_ticker.get(ticker_symbol)
            if usdm is not None:
                return safe_float(usdm.get("last_price"))
        return None

    async def merge_tickers(self, source: str, rows: list[dict[str, Any]]) -> None:
        now = int(time.time() * 1000)
        target = self._spot_ticker if source == "spot_ticker" else self._usdm_ticker
        async with self._lock:
            for row in rows:
                symbol = str(row.get("symbol") or "").upper()
                if symbol:
                    target[symbol] = row
            self._updated_at[source] = now
            self._loaded_sources.add(source)

    async def merge_marks(self, rows: list[dict[str, Any]]) -> None:
        now = int(time.time() * 1000)
        async with self._lock:
            for row in rows:
                symbol = str(row.get("symbol") or "").upper()
                if symbol:
                    self._usdm_mark[symbol] = row
            self._updated_at["usdm_mark"] = now
            self._loaded_sources.add("usdm_mark")

    def ticker_response(self, market: str, rows: Any) -> dict[str, Any]:
        return self._ticker_payload(market, rows)

    def mark_response(self, market: str, rows: Any) -> dict[str, Any]:
        return self._mark_payload(market, rows)

    def _ticker_payload(self, market: str, rows: Any) -> dict[str, Any]:
        return {
            "exchange": "binance",
            "market": market,
            "items": sorted(list(rows), key=lambda item: item.get("quote_volume") or 0, reverse=True),
        }

    def _mark_payload(self, market: str, rows: Any) -> dict[str, Any]:
        return {
            "exchange": "binance",
            "market": market,
            "items": sorted(list(rows), key=lambda item: item.get("symbol") or ""),
        }

    def _to_ticker_symbol(self, symbol: str) -> str:
        normalized = str(symbol or "").strip().upper()
        if not normalized:
            return ""
        return normalized.replace("/", "")
