from __future__ import annotations

from app.schemas.binance_market import (
    BinanceBookTickerResponse,
    BinanceExchangeInfoResponse,
    BinanceKlineResponse,
    BinanceOrderBookResponse,
    BinancePriceTickerResponse,
    BinanceTickerStatsResponse,
    BinanceTradeListResponse,
)

from .binance_api_support import BinanceApiSupport, compact_query, encode_symbol_list
from .binance_market_normalizers import normalize_kline_response, normalize_levels, normalize_ticker_item, normalize_trade
from .binance_numbers import to_float


class BinanceSpotMarketService:
    def __init__(self, client: BinanceApiSupport) -> None:
        self.client = client

    async def get_exchange_info(
        self,
        *,
        symbols: list[str] | None = None,
        permissions: list[str] | None = None,
        symbol_status: str | None = None,
    ) -> BinanceExchangeInfoResponse:
        params = compact_query(
            {
                "symbols": encode_symbol_list(symbols),
                "permissions": encode_symbol_list(permissions),
                "symbolStatus": symbol_status,
            }
        )
        payload = await self.client.get_json("/api/v3/exchangeInfo", params=params, ttl=300)
        return BinanceExchangeInfoResponse.model_validate({
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
        })

    async def get_ticker_24hr(self, *, symbols: list[str] | None = None) -> BinanceTickerStatsResponse:
        payload = await self.client.get_json(
            "/api/v3/ticker/24hr",
            params=compact_query({"symbols": encode_symbol_list(symbols)}),
            ttl=30,
        )
        items = payload if isinstance(payload, list) else [payload]
        return BinanceTickerStatsResponse.model_validate({
            "exchange": "binance",
            "market": "spot",
            "items": [normalize_ticker_item(item) for item in items],
        })

    async def get_ticker_window(
        self,
        *,
        symbols: list[str] | None = None,
        window_size: str | None = None,
    ) -> BinanceTickerStatsResponse:
        payload = await self.client.get_json(
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
        return BinanceTickerStatsResponse.model_validate({
            "exchange": "binance",
            "market": "spot",
            "items": [normalize_ticker_item(item) for item in items],
        })

    async def get_price(self, *, symbols: list[str] | None = None) -> BinancePriceTickerResponse:
        payload = await self.client.get_json(
            "/api/v3/ticker/price",
            params=compact_query({"symbols": encode_symbol_list(symbols)}),
            ttl=10,
        )
        items = payload if isinstance(payload, list) else [payload]
        return BinancePriceTickerResponse.model_validate({
            "exchange": "binance",
            "market": "spot",
            "items": [
                {
                    "symbol": item.get("symbol"),
                    "price": to_float(item.get("price")),
                }
                for item in items
            ],
        })

    async def get_book_ticker(self, *, symbols: list[str] | None = None) -> BinanceBookTickerResponse:
        payload = await self.client.get_json(
            "/api/v3/ticker/bookTicker",
            params=compact_query({"symbols": encode_symbol_list(symbols)}),
            ttl=10,
        )
        items = payload if isinstance(payload, list) else [payload]
        return BinanceBookTickerResponse.model_validate({
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
        })

    async def get_depth(self, *, symbol: str, limit: int = 20) -> BinanceOrderBookResponse:
        payload = await self.client.get_json(
            "/api/v3/depth",
            params={"symbol": symbol.upper(), "limit": limit},
            ttl=5,
        )
        return BinanceOrderBookResponse.model_validate({
            "exchange": "binance",
            "market": "spot",
            "symbol": symbol.upper(),
            "last_update_id": payload.get("lastUpdateId"),
            "bids": normalize_levels(payload.get("bids") or []),
            "asks": normalize_levels(payload.get("asks") or []),
        })

    async def get_trades(self, *, symbol: str, limit: int = 50) -> BinanceTradeListResponse:
        payload = await self.client.get_json(
            "/api/v3/trades",
            params={"symbol": symbol.upper(), "limit": limit},
            ttl=5,
        )
        return BinanceTradeListResponse.model_validate({
            "exchange": "binance",
            "market": "spot",
            "symbol": symbol.upper(),
            "items": [normalize_trade(item) for item in payload],
        })

    async def get_agg_trades(
        self,
        *,
        symbol: str,
        limit: int = 50,
        start_time: int | None = None,
        end_time: int | None = None,
    ) -> BinanceTradeListResponse:
        payload = await self.client.get_json(
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
        return BinanceTradeListResponse.model_validate({
            "exchange": "binance",
            "market": "spot",
            "symbol": symbol.upper(),
            "items": [normalize_trade(item, aggregate=True) for item in payload],
        })

    async def get_klines(
        self,
        *,
        symbol: str,
        interval: str,
        limit: int = 200,
        start_time: int | None = None,
        end_time: int | None = None,
        ui_mode: bool = False,
    ) -> BinanceKlineResponse:
        path = "/api/v3/uiKlines" if ui_mode else "/api/v3/klines"
        payload = await self.client.get_json(
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
        return BinanceKlineResponse.model_validate(normalize_kline_response("spot", symbol.upper(), interval, payload))
