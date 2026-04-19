from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from config import settings
from utils.logger import logger

from .binance_api_support import BinanceApiSupport, compact_query, encode_symbol_list
from .binance_breakout_monitor import BinanceBreakoutMonitor
from .binance_market_normalizers import (
    normalize_basis,
    normalize_derivatives_exchange_info,
    normalize_derivatives_ticker_list,
    normalize_kline_response,
    normalize_levels,
    normalize_mark_price_list,
    normalize_open_interest_snapshot,
    normalize_open_interest_stats,
    normalize_ratio_series,
    normalize_taker_volume,
    normalize_ticker_item,
    normalize_trade,
)
from .binance_numbers import to_float, to_int

if TYPE_CHECKING:
    from .binance_market_snapshot_service import BinanceMarketSnapshotService


class BinanceMarketIntelService:
    def __init__(self, snapshot_service: BinanceMarketSnapshotService | None = None) -> None:
        self.snapshot_service = snapshot_service
        self.breakout_monitor = BinanceBreakoutMonitor(self._get_market_klines)
        self.spot = BinanceApiSupport(
            base_url=settings.BINANCE_PUBLIC_BASE_URL,
            cache_namespace="binance:spot",
            user_agent="heimdall/market-intel",
        )
        self.usdm = BinanceApiSupport(
            base_url=settings.BINANCE_FUTURES_USDM_BASE_URL,
            cache_namespace="binance:usdm",
            user_agent="heimdall/market-intel",
        )

    async def get_spot_exchange_info(
        self,
        *,
        symbols: list[str] | None = None,
        permissions: list[str] | None = None,
        symbol_status: str | None = None,
    ) -> dict[str, Any]:
        params = compact_query(
            {
                "symbols": encode_symbol_list(symbols),
                "permissions": encode_symbol_list(permissions),
                "symbolStatus": symbol_status,
            }
        )
        payload = await self.spot.get_json("/api/v3/exchangeInfo", params=params, ttl=300)
        return {
            "exchange": "binance",
            "market": "spot",
            "timezone": payload.get("timezone"),
            "server_time": payload.get("serverTime"),
            "symbols": [
                {
                    "symbol": item.get("symbol"),
                    "status": item.get("status"),
                    "base_asset": item.get("baseAsset"),
                    "quote_asset": item.get("quoteAsset"),
                    "price_precision": item.get("quotePrecision"),
                    "quantity_precision": item.get("baseAssetPrecision"),
                    "permissions": list(item.get("permissions") or []),
                }
                for item in payload.get("symbols", [])
            ],
        }

    async def get_spot_ticker_24hr(self, *, symbols: list[str] | None = None) -> dict[str, Any]:
        payload = await self.spot.get_json(
            "/api/v3/ticker/24hr",
            params=compact_query({"symbols": encode_symbol_list(symbols)}),
            ttl=30,
        )
        items = payload if isinstance(payload, list) else [payload]
        return {
            "exchange": "binance",
            "market": "spot",
            "items": [normalize_ticker_item(item) for item in items],
        }

    async def get_spot_ticker_window(
        self,
        *,
        symbols: list[str] | None = None,
        window_size: str | None = None,
    ) -> dict[str, Any]:
        payload = await self.spot.get_json(
            "/api/v3/ticker",
            params=compact_query(
                {
                    "symbols": encode_symbol_list(symbols),
                    "windowSize": window_size,
                }
            ),
            ttl=30,
        )
        items = payload if isinstance(payload, list) else [payload]
        return {
            "exchange": "binance",
            "market": "spot",
            "items": [normalize_ticker_item(item) for item in items],
        }

    async def get_spot_price(self, *, symbols: list[str] | None = None) -> dict[str, Any]:
        payload = await self.spot.get_json(
            "/api/v3/ticker/price",
            params=compact_query({"symbols": encode_symbol_list(symbols)}),
            ttl=10,
        )
        items = payload if isinstance(payload, list) else [payload]
        return {
            "exchange": "binance",
            "market": "spot",
            "items": [
                {
                    "symbol": item.get("symbol"),
                    "price": to_float(item.get("price")),
                }
                for item in items
            ],
        }

    async def get_spot_book_ticker(self, *, symbols: list[str] | None = None) -> dict[str, Any]:
        payload = await self.spot.get_json(
            "/api/v3/ticker/bookTicker",
            params=compact_query({"symbols": encode_symbol_list(symbols)}),
            ttl=10,
        )
        items = payload if isinstance(payload, list) else [payload]
        return {
            "exchange": "binance",
            "market": "spot",
            "items": [
                {
                    "symbol": item.get("symbol"),
                    "bid_price": to_float(item.get("bidPrice")),
                    "bid_qty": to_float(item.get("bidQty")),
                    "ask_price": to_float(item.get("askPrice")),
                    "ask_qty": to_float(item.get("askQty")),
                }
                for item in items
            ],
        }

    async def get_spot_depth(self, *, symbol: str, limit: int = 20) -> dict[str, Any]:
        payload = await self.spot.get_json(
            "/api/v3/depth",
            params={"symbol": symbol.upper(), "limit": limit},
            ttl=5,
        )
        return {
            "exchange": "binance",
            "market": "spot",
            "symbol": symbol.upper(),
            "last_update_id": payload.get("lastUpdateId"),
            "bids": normalize_levels(payload.get("bids") or []),
            "asks": normalize_levels(payload.get("asks") or []),
        }

    async def get_spot_trades(self, *, symbol: str, limit: int = 50) -> dict[str, Any]:
        payload = await self.spot.get_json(
            "/api/v3/trades",
            params={"symbol": symbol.upper(), "limit": limit},
            ttl=5,
        )
        return {
            "exchange": "binance",
            "market": "spot",
            "symbol": symbol.upper(),
            "items": [normalize_trade(item) for item in payload],
        }

    async def get_spot_agg_trades(
        self,
        *,
        symbol: str,
        limit: int = 50,
        start_time: int | None = None,
        end_time: int | None = None,
    ) -> dict[str, Any]:
        payload = await self.spot.get_json(
            "/api/v3/aggTrades",
            params=compact_query(
                {
                    "symbol": symbol.upper(),
                    "limit": limit,
                    "startTime": start_time,
                    "endTime": end_time,
                }
            ),
            ttl=5,
        )
        return {
            "exchange": "binance",
            "market": "spot",
            "symbol": symbol.upper(),
            "items": [normalize_trade(item, aggregate=True) for item in payload],
        }

    async def get_spot_klines(
        self,
        *,
        symbol: str,
        interval: str,
        limit: int = 200,
        start_time: int | None = None,
        end_time: int | None = None,
        ui_mode: bool = False,
    ) -> dict[str, Any]:
        path = "/api/v3/uiKlines" if ui_mode else "/api/v3/klines"
        payload = await self.spot.get_json(
            path,
            params=compact_query(
                {
                    "symbol": symbol.upper(),
                    "interval": interval,
                    "limit": limit,
                    "startTime": start_time,
                    "endTime": end_time,
                }
            ),
            ttl=30,
        )
        return normalize_kline_response("spot", symbol.upper(), interval, payload)

    async def get_usdm_exchange_info(self) -> dict[str, Any]:
        payload = await self.usdm.get_json("/fapi/v1/exchangeInfo", ttl=300)
        return normalize_derivatives_exchange_info("usdm", payload)

    async def get_usdm_ticker_24hr(self, *, symbol: str | None = None) -> dict[str, Any]:
        payload = await self.usdm.get_json(
            "/fapi/v1/ticker/24hr",
            params=compact_query({"symbol": symbol.upper() if symbol else None}),
            ttl=10,
        )
        return normalize_derivatives_ticker_list("usdm", payload)

    async def get_usdm_mark_price(self, *, symbol: str | None = None) -> dict[str, Any]:
        payload = await self.usdm.get_json(
            "/fapi/v1/premiumIndex",
            params=compact_query({"symbol": symbol.upper() if symbol else None}),
            ttl=10,
        )
        return normalize_mark_price_list("usdm", payload)

    async def get_usdm_klines(
        self,
        *,
        symbol: str,
        interval: str,
        limit: int = 200,
        start_time: int | None = None,
        end_time: int | None = None,
    ) -> dict[str, Any]:
        payload = await self.usdm.get_json(
            "/fapi/v1/klines",
            params=compact_query(
                {
                    "symbol": symbol.upper(),
                    "interval": interval,
                    "limit": limit,
                    "startTime": start_time,
                    "endTime": end_time,
                }
            ),
            ttl=30,
        )
        return normalize_kline_response("usdm", symbol.upper(), interval, payload)

    async def get_usdm_funding_info(self) -> dict[str, Any]:
        payload = await self.usdm.get_json("/fapi/v1/fundingInfo", ttl=300)
        return {
            "exchange": "binance",
            "market": "usdm",
            "items": [
                {
                    "symbol": item.get("symbol"),
                    "adjusted_funding_rate_cap": to_float(item.get("adjustedFundingRateCap")),
                    "adjusted_funding_rate_floor": to_float(item.get("adjustedFundingRateFloor")),
                    "funding_interval_hours": to_int(item.get("fundingIntervalHours")),
                    "disclaimer": bool(item.get("disclaimer")),
                }
                for item in payload
            ],
        }

    async def get_usdm_funding_history(
        self,
        *,
        symbol: str | None = None,
        limit: int = 100,
        start_time: int | None = None,
        end_time: int | None = None,
    ) -> dict[str, Any]:
        payload = await self.usdm.get_json(
            "/fapi/v1/fundingRate",
            params=compact_query(
                {
                    "symbol": symbol.upper() if symbol else None,
                    "limit": limit,
                    "startTime": start_time,
                    "endTime": end_time,
                }
            ),
            ttl=30,
        )
        return {
            "exchange": "binance",
            "market": "usdm",
            "items": [
                {
                    "symbol": item.get("symbol"),
                    "funding_rate": to_float(item.get("fundingRate")),
                    "mark_price": to_float(item.get("markPrice")),
                    "funding_time": to_int(item.get("fundingTime")),
                }
                for item in payload
            ],
        }

    async def get_usdm_open_interest(self, *, symbol: str) -> dict[str, Any]:
        payload = await self.usdm.get_json("/fapi/v1/openInterest", params={"symbol": symbol.upper()}, ttl=10)
        return normalize_open_interest_snapshot("usdm", payload)

    async def get_usdm_open_interest_stats(
        self,
        *,
        symbol: str,
        period: str,
        limit: int = 30,
    ) -> dict[str, Any]:
        payload = await self.usdm.get_json(
            "/futures/data/openInterestHist",
            params={"symbol": symbol.upper(), "period": period, "limit": limit},
            ttl=30,
        )
        return normalize_open_interest_stats("usdm", payload)

    async def get_usdm_long_short_ratio(self, *, symbol: str, period: str, limit: int = 30) -> dict[str, Any]:
        payload = await self.usdm.get_json(
            "/futures/data/globalLongShortAccountRatio",
            params={"symbol": symbol.upper(), "period": period, "limit": limit},
            ttl=30,
        )
        return normalize_ratio_series("usdm", payload)

    async def get_usdm_top_trader_accounts(self, *, symbol: str, period: str, limit: int = 30) -> dict[str, Any]:
        payload = await self.usdm.get_json(
            "/futures/data/topLongShortAccountRatio",
            params={"symbol": symbol.upper(), "period": period, "limit": limit},
            ttl=30,
        )
        return normalize_ratio_series("usdm", payload)

    async def get_usdm_top_trader_positions(self, *, symbol: str, period: str, limit: int = 30) -> dict[str, Any]:
        payload = await self.usdm.get_json(
            "/futures/data/topLongShortPositionRatio",
            params={"symbol": symbol.upper(), "period": period, "limit": limit},
            ttl=30,
        )
        return normalize_ratio_series("usdm", payload)

    async def get_usdm_taker_volume(self, *, symbol: str, period: str, limit: int = 30) -> dict[str, Any]:
        payload = await self.usdm.get_json(
            "/futures/data/takerlongshortRatio",
            params={"symbol": symbol.upper(), "period": period, "limit": limit},
            ttl=30,
        )
        return normalize_taker_volume("usdm", payload)

    async def get_usdm_basis(
        self,
        *,
        pair: str,
        contract_type: str,
        period: str,
        limit: int = 30,
    ) -> dict[str, Any]:
        payload = await self.usdm.get_json(
            "/futures/data/basis",
            params={"pair": pair.upper(), "contractType": contract_type, "period": period, "limit": limit},
            ttl=30,
        )
        return normalize_basis("usdm", payload)

    async def get_market_breakout_monitor(
        self,
        *,
        min_rise_pct: float = 5.0,
        limit: int = 18,
        quote_asset: str = "USDT",
    ) -> dict[str, Any]:
        normalized_quote_asset = self.breakout_monitor.normalize_quote_asset(quote_asset)
        market_snapshot = await self._load_market_page_snapshot()
        return await self.breakout_monitor.build(
            market_snapshot=market_snapshot,
            min_rise_pct=min_rise_pct,
            limit=limit,
            quote_asset=normalized_quote_asset,
        )

    async def get_market_page_payload(
        self,
        *,
        min_rise_pct: float = 5.0,
        limit: int = 24,
        quote_asset: str = "USDT",
    ) -> dict[str, Any]:
        normalized_quote_asset = self.breakout_monitor.normalize_quote_asset(quote_asset)
        market_snapshot = await self._load_market_page_snapshot()
        monitor = await self.breakout_monitor.build(
            market_snapshot=market_snapshot,
            min_rise_pct=min_rise_pct,
            limit=limit,
            quote_asset=normalized_quote_asset,
        )
        return {
            "exchange": "binance",
            "quote_asset": normalized_quote_asset,
            "updated_at": monitor["updated_at"],
            "monitor": monitor,
            "spot_ticker": market_snapshot["spot_ticker"],
            "usdm_ticker": market_snapshot["usdm_ticker"],
            "usdm_mark": market_snapshot["usdm_mark"],
            "load_errors": market_snapshot["load_errors"],
        }

    async def _load_market_page_snapshot(self) -> dict[str, Any]:
        if self.snapshot_service is not None:
            return await self.snapshot_service.get_market_page_snapshot()

        source_plan = (
            ("spot_ticker", "现货榜单", self.get_spot_ticker_24hr, self.breakout_monitor.empty_ticker_response, "spot"),
            ("usdm_ticker", "U本位24H", self.get_usdm_ticker_24hr, self.breakout_monitor.empty_ticker_response, "usdm"),
            ("usdm_mark", "U本位Funding", self.get_usdm_mark_price, self.breakout_monitor.empty_mark_price_response, "usdm"),
        )
        raw_results = await asyncio.gather(*(loader() for _, _, loader, _, _ in source_plan), return_exceptions=True)
        snapshot: dict[str, Any] = {"load_errors": []}
        for (key, label, _, empty_factory, market), result in zip(source_plan, raw_results, strict=False):
            if isinstance(result, Exception):
                logger.warning("Binance market page source failed: %s (%s)", key, result)
                snapshot[key] = empty_factory(market)
                snapshot["load_errors"].append(label)
                continue
            snapshot[key] = result
        return snapshot

    async def _get_market_klines(self, market: str, symbol: str, interval: str, limit: int) -> dict[str, Any]:
        if market == "spot":
            return await self.get_spot_klines(symbol=symbol, interval=interval, limit=limit)
        return await self.get_usdm_klines(symbol=symbol, interval=interval, limit=limit)
