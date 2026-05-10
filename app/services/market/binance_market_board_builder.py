from __future__ import annotations

from typing import Any

from .binance_numbers import safe_float
from .market_board_support import board_key

MARKET_BOARD_LIMIT = 15
SPOT_BOARD_FIELDS = ("price_change_pct", "quote_volume")
CONTRACT_BOARD_FIELDS = ("price_change_pct", "funding_rate_pct", "quote_volume", "oi_change_24h_pct")
BOARD_DIRECTIONS = ("desc", "asc")


class BinanceMarketBoardBuilder:
    def build_response_fields(
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

    def _build_spot_boards(self, market_snapshot: dict[str, Any], *, quote_asset: str) -> dict[str, dict[str, Any]]:
        rows = [
            item
            for item in market_snapshot["spot_ticker"].get("items", [])
            if str(item.get("symbol") or "").upper().endswith(quote_asset)
        ]
        return {
            board_key(field, direction): {
                "exchange": "binance",
                "market": "spot",
                "items": self._sort_market_rows(rows, field, direction)[:MARKET_BOARD_LIMIT],
            }
            for field in SPOT_BOARD_FIELDS
            for direction in BOARD_DIRECTIONS
        }

    def _build_contract_boards(
        self,
        market_snapshot: dict[str, Any],
        *,
        oi_changes: dict[str, dict[str, float | None]],
    ) -> dict[str, dict[str, Any]]:
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
                "market_label": "U 本位",
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
            board_key(field, direction): {
                "exchange": "binance",
                "market": "usdm",
                "items": self._sort_market_rows(rows, field, direction)[:MARKET_BOARD_LIMIT],
            }
            for field in CONTRACT_BOARD_FIELDS
            for direction in BOARD_DIRECTIONS
        }

    def _sort_market_rows(self, rows: list[dict[str, Any]], field: str, direction: str) -> list[dict[str, Any]]:
        reverse_primary = direction == "desc"

        def sort_key(item: dict[str, Any]) -> tuple[bool, float, bool, float, str]:
            primary = safe_float(item.get(field))
            volume = safe_float(item.get("quote_volume"))
            primary_value = primary if primary is not None else 0.0
            if reverse_primary:
                primary_value = -primary_value
            return (
                primary is None,
                primary_value,
                volume is None,
                -(volume or 0.0),
                str(item.get("symbol") or ""),
            )

        return sorted(rows, key=sort_key)

    def _funding_rate_pct(self, value: Any) -> float | None:
        numeric = safe_float(value)
        return None if numeric is None else numeric * 100
