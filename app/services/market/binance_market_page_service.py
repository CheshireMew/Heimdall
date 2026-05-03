from __future__ import annotations

import time
from functools import cmp_to_key
from typing import TYPE_CHECKING, Any

from app.schemas.binance_market import (
    BinanceBreakoutMonitorResponse,
    BinanceContractBoardResponse,
    BinanceMarketBoardsResponse,
    BinanceMarketPageResponse,
    BinanceTickerStatsResponse,
)

from .binance_breakout_monitor import BinanceBreakoutMonitor
from .binance_spot_market import BinanceSpotMarketService
from .binance_usdm_market import BinanceUsdmMarketService

if TYPE_CHECKING:
    from .binance_market_snapshot_service import BinanceMarketSnapshotService


PAGE_PAYLOAD_CACHE_TTL_SECONDS = 20.0
MARKET_BOARD_LIMIT = 15
SPOT_BOARD_FIELDS = ("price_change_pct", "quote_volume")
CONTRACT_BOARD_FIELDS = ("price_change_pct", "funding_rate_pct", "quote_volume")
BOARD_DIRECTIONS = ("desc", "asc")


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
        boards = self._build_boards_response(
            market_snapshot,
            quote_asset=normalized_quote_asset,
            updated_at=market_snapshot["updated_at"],
        )
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
            "spot_boards": boards.spot_boards,
            "contract_boards": boards.contract_boards,
            "load_errors": boards.load_errors,
        })
        if not response.load_errors:
            self._write_page_payload_cache(cache_key, response)
        return response

    async def get_market_boards(self, *, quote_asset: str = "USDT") -> BinanceMarketBoardsResponse:
        normalized_quote_asset = self.breakout_monitor.normalize_quote_asset(quote_asset)
        market_snapshot = await self._load_market_page_snapshot()
        return self._build_boards_response(
            market_snapshot,
            quote_asset=normalized_quote_asset,
            updated_at=market_snapshot["updated_at"],
        )

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

    def _build_boards_response(
        self,
        market_snapshot: dict[str, Any],
        *,
        quote_asset: str,
        updated_at: int,
    ) -> BinanceMarketBoardsResponse:
        return BinanceMarketBoardsResponse.model_validate({
            "exchange": "binance",
            "quote_asset": quote_asset,
            "updated_at": updated_at,
            "spot_boards": self._build_spot_boards(market_snapshot, quote_asset=quote_asset),
            "contract_boards": self._build_contract_boards(market_snapshot),
            "load_errors": market_snapshot["load_errors"],
        })

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

    def _build_contract_boards(self, market_snapshot: dict[str, Any]) -> dict[str, BinanceContractBoardResponse]:
        mark_map = {
            str(item.get("symbol") or "").upper(): item
            for item in market_snapshot["usdm_mark"].get("items", [])
        }
        rows = []
        for item in market_snapshot["usdm_ticker"].get("items", []):
            symbol = str(item.get("symbol") or "").upper()
            mark = mark_map.get(symbol, {})
            rows.append({
                **item,
                "market": "usdm",
                "market_label": "U 鏈綅",
                "mark_price": mark.get("mark_price"),
                "index_price": mark.get("index_price"),
                "funding_rate_pct": self._funding_rate_pct(mark.get("last_funding_rate")),
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
