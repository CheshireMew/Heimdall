from __future__ import annotations

from typing import Any

from config import settings

from .binance_api_support import BinanceApiSupport, compact_query, encode_symbol_list


class BinanceMarketIntelService:
    def __init__(self) -> None:
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
        self.coinm = BinanceApiSupport(
            base_url=settings.BINANCE_FUTURES_COINM_BASE_URL,
            cache_namespace="binance:coinm",
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
            "items": [self._normalize_ticker_item(item) for item in items],
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
            "items": [self._normalize_ticker_item(item) for item in items],
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
                    "price": self._to_float(item.get("price")),
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
                    "bid_price": self._to_float(item.get("bidPrice")),
                    "bid_qty": self._to_float(item.get("bidQty")),
                    "ask_price": self._to_float(item.get("askPrice")),
                    "ask_qty": self._to_float(item.get("askQty")),
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
            "bids": self._normalize_levels(payload.get("bids") or []),
            "asks": self._normalize_levels(payload.get("asks") or []),
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
            "items": [self._normalize_trade(item) for item in payload],
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
            "items": [self._normalize_trade(item, aggregate=True) for item in payload],
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
        return self._normalize_kline_response("spot", symbol.upper(), interval, payload)

    async def get_usdm_exchange_info(self) -> dict[str, Any]:
        payload = await self.usdm.get_json("/fapi/v1/exchangeInfo", ttl=300)
        return self._normalize_derivatives_exchange_info("usdm", payload)

    async def get_coinm_exchange_info(self) -> dict[str, Any]:
        payload = await self.coinm.get_json("/dapi/v1/exchangeInfo", ttl=300)
        return self._normalize_derivatives_exchange_info("coinm", payload)

    async def get_usdm_ticker_24hr(self, *, symbol: str | None = None) -> dict[str, Any]:
        payload = await self.usdm.get_json(
            "/fapi/v1/ticker/24hr",
            params=compact_query({"symbol": symbol.upper() if symbol else None}),
            ttl=10,
        )
        return self._normalize_derivatives_ticker_list("usdm", payload)

    async def get_coinm_ticker_24hr(self, *, symbol: str | None = None, pair: str | None = None) -> dict[str, Any]:
        payload = await self.coinm.get_json(
            "/dapi/v1/ticker/24hr",
            params=compact_query({"symbol": symbol.upper() if symbol else None, "pair": pair.upper() if pair else None}),
            ttl=10,
        )
        return self._normalize_derivatives_ticker_list("coinm", payload)

    async def get_usdm_mark_price(self, *, symbol: str | None = None) -> dict[str, Any]:
        payload = await self.usdm.get_json(
            "/fapi/v1/premiumIndex",
            params=compact_query({"symbol": symbol.upper() if symbol else None}),
            ttl=10,
        )
        return self._normalize_mark_price_list("usdm", payload)

    async def get_coinm_mark_price(self, *, symbol: str | None = None, pair: str | None = None) -> dict[str, Any]:
        payload = await self.coinm.get_json(
            "/dapi/v1/premiumIndex",
            params=compact_query({"symbol": symbol.upper() if symbol else None, "pair": pair.upper() if pair else None}),
            ttl=10,
        )
        return self._normalize_mark_price_list("coinm", payload)

    async def get_usdm_funding_info(self) -> dict[str, Any]:
        payload = await self.usdm.get_json("/fapi/v1/fundingInfo", ttl=300)
        return {
            "exchange": "binance",
            "market": "usdm",
            "items": [
                {
                    "symbol": item.get("symbol"),
                    "adjusted_funding_rate_cap": self._to_float(item.get("adjustedFundingRateCap")),
                    "adjusted_funding_rate_floor": self._to_float(item.get("adjustedFundingRateFloor")),
                    "funding_interval_hours": self._to_int(item.get("fundingIntervalHours")),
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
                    "funding_rate": self._to_float(item.get("fundingRate")),
                    "mark_price": self._to_float(item.get("markPrice")),
                    "funding_time": self._to_int(item.get("fundingTime")),
                }
                for item in payload
            ],
        }

    async def get_coinm_funding_info(self) -> dict[str, Any]:
        payload = await self.coinm.get_json("/dapi/v1/fundingInfo", ttl=300)
        return {
            "exchange": "binance",
            "market": "coinm",
            "items": [
                {
                    "symbol": item.get("symbol"),
                    "adjusted_funding_rate_cap": self._to_float(item.get("adjustedFundingRateCap")),
                    "adjusted_funding_rate_floor": self._to_float(item.get("adjustedFundingRateFloor")),
                    "funding_interval_hours": self._to_int(item.get("fundingIntervalHours")),
                    "disclaimer": bool(item.get("disclaimer")),
                }
                for item in payload
            ],
        }

    async def get_coinm_funding_history(
        self,
        *,
        symbol: str | None = None,
        limit: int = 100,
        start_time: int | None = None,
        end_time: int | None = None,
    ) -> dict[str, Any]:
        payload = await self.coinm.get_json(
            "/dapi/v1/fundingRate",
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
            "market": "coinm",
            "items": [
                {
                    "symbol": item.get("symbol"),
                    "funding_rate": self._to_float(item.get("fundingRate")),
                    "mark_price": self._to_float(item.get("markPrice")),
                    "funding_time": self._to_int(item.get("fundingTime")),
                }
                for item in payload
            ],
        }

    async def get_usdm_open_interest(self, *, symbol: str) -> dict[str, Any]:
        payload = await self.usdm.get_json("/fapi/v1/openInterest", params={"symbol": symbol.upper()}, ttl=10)
        return self._normalize_open_interest_snapshot("usdm", payload)

    async def get_coinm_open_interest(self, *, symbol: str) -> dict[str, Any]:
        payload = await self.coinm.get_json("/dapi/v1/openInterest", params={"symbol": symbol.upper()}, ttl=10)
        return self._normalize_open_interest_snapshot("coinm", payload)

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
        return self._normalize_open_interest_stats("usdm", payload)

    async def get_coinm_open_interest_stats(
        self,
        *,
        pair: str,
        contract_type: str,
        period: str,
        limit: int = 30,
    ) -> dict[str, Any]:
        payload = await self.coinm.get_json(
            "/futures/data/openInterestHist",
            params={"pair": pair.upper(), "contractType": contract_type, "period": period, "limit": limit},
            ttl=30,
        )
        return self._normalize_open_interest_stats("coinm", payload)

    async def get_usdm_long_short_ratio(self, *, symbol: str, period: str, limit: int = 30) -> dict[str, Any]:
        payload = await self.usdm.get_json(
            "/futures/data/globalLongShortAccountRatio",
            params={"symbol": symbol.upper(), "period": period, "limit": limit},
            ttl=30,
        )
        return self._normalize_ratio_series("usdm", payload)

    async def get_coinm_long_short_ratio(self, *, pair: str, period: str, limit: int = 30) -> dict[str, Any]:
        payload = await self.coinm.get_json(
            "/futures/data/globalLongShortAccountRatio",
            params={"pair": pair.upper(), "period": period, "limit": limit},
            ttl=30,
        )
        return self._normalize_ratio_series("coinm", payload)

    async def get_usdm_top_trader_accounts(self, *, symbol: str, period: str, limit: int = 30) -> dict[str, Any]:
        payload = await self.usdm.get_json(
            "/futures/data/topLongShortAccountRatio",
            params={"symbol": symbol.upper(), "period": period, "limit": limit},
            ttl=30,
        )
        return self._normalize_ratio_series("usdm", payload)

    async def get_coinm_top_trader_accounts(self, *, symbol: str, period: str, limit: int = 30) -> dict[str, Any]:
        payload = await self.coinm.get_json(
            "/futures/data/topLongShortAccountRatio",
            params={"symbol": symbol.upper(), "period": period, "limit": limit},
            ttl=30,
        )
        return self._normalize_ratio_series("coinm", payload)

    async def get_usdm_top_trader_positions(self, *, symbol: str, period: str, limit: int = 30) -> dict[str, Any]:
        payload = await self.usdm.get_json(
            "/futures/data/topLongShortPositionRatio",
            params={"symbol": symbol.upper(), "period": period, "limit": limit},
            ttl=30,
        )
        return self._normalize_ratio_series("usdm", payload)

    async def get_coinm_top_trader_positions(self, *, pair: str, period: str, limit: int = 30) -> dict[str, Any]:
        payload = await self.coinm.get_json(
            "/futures/data/topLongShortPositionRatio",
            params={"pair": pair.upper(), "period": period, "limit": limit},
            ttl=30,
        )
        return self._normalize_ratio_series("coinm", payload)

    async def get_usdm_taker_volume(self, *, symbol: str, period: str, limit: int = 30) -> dict[str, Any]:
        payload = await self.usdm.get_json(
            "/futures/data/takerlongshortRatio",
            params={"symbol": symbol.upper(), "period": period, "limit": limit},
            ttl=30,
        )
        return self._normalize_taker_volume("usdm", payload)

    async def get_coinm_taker_volume(
        self,
        *,
        pair: str,
        contract_type: str,
        period: str,
        limit: int = 30,
    ) -> dict[str, Any]:
        payload = await self.coinm.get_json(
            "/futures/data/takerBuySellVol",
            params={"pair": pair.upper(), "contractType": contract_type, "period": period, "limit": limit},
            ttl=30,
        )
        return self._normalize_taker_volume("coinm", payload)

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
        return self._normalize_basis("usdm", payload)

    async def get_coinm_basis(
        self,
        *,
        pair: str,
        contract_type: str,
        period: str,
        limit: int = 30,
    ) -> dict[str, Any]:
        payload = await self.coinm.get_json(
            "/futures/data/basis",
            params={"pair": pair.upper(), "contractType": contract_type, "period": period, "limit": limit},
            ttl=30,
        )
        return self._normalize_basis("coinm", payload)

    def _normalize_ticker_item(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "symbol": item.get("symbol"),
            "price_change": self._to_float(item.get("priceChange")),
            "price_change_pct": self._to_float(item.get("priceChangePercent")),
            "weighted_avg_price": self._to_float(item.get("weightedAvgPrice")),
            "last_price": self._to_float(item.get("lastPrice")),
            "last_qty": self._to_float(item.get("lastQty")),
            "open_price": self._to_float(item.get("openPrice")),
            "high_price": self._to_float(item.get("highPrice")),
            "low_price": self._to_float(item.get("lowPrice")),
            "volume": self._to_float(item.get("volume")),
            "quote_volume": self._to_float(item.get("quoteVolume")),
            "open_time": self._to_int(item.get("openTime")),
            "close_time": self._to_int(item.get("closeTime")),
            "count": self._to_int(item.get("count")),
        }

    def _normalize_levels(self, levels: list[list[Any]]) -> list[dict[str, float | None]]:
        return [{"price": self._to_float(level[0]), "qty": self._to_float(level[1])} for level in levels]

    def _normalize_trade(self, item: dict[str, Any], *, aggregate: bool = False) -> dict[str, Any]:
        return {
            "id": self._to_int(item.get("a") if aggregate else item.get("id")),
            "price": self._to_float(item.get("p") if aggregate else item.get("price")),
            "qty": self._to_float(item.get("q") if aggregate else item.get("qty")),
            "quote_qty": self._to_float(item.get("quoteQty")),
            "time": self._to_int(item.get("T") if aggregate else item.get("time")),
            "is_buyer_maker": bool(item.get("m") if aggregate else item.get("isBuyerMaker")),
        }

    def _normalize_kline_response(self, market: str, symbol: str, interval: str, rows: list[list[Any]]) -> dict[str, Any]:
        return {
            "exchange": "binance",
            "market": market,
            "symbol": symbol,
            "interval": interval,
            "items": [
                {
                    "open_time": self._to_int(row[0]),
                    "open": self._to_float(row[1]),
                    "high": self._to_float(row[2]),
                    "low": self._to_float(row[3]),
                    "close": self._to_float(row[4]),
                    "volume": self._to_float(row[5]),
                    "close_time": self._to_int(row[6]),
                    "quote_volume": self._to_float(row[7]) if len(row) > 7 else None,
                    "trade_count": self._to_int(row[8]) if len(row) > 8 else None,
                }
                for row in rows
            ],
        }

    def _normalize_derivatives_exchange_info(self, market: str, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "exchange": "binance",
            "market": market,
            "timezone": payload.get("timezone"),
            "server_time": payload.get("serverTime"),
            "symbols": [
                {
                    "symbol": item.get("symbol"),
                    "status": item.get("status"),
                    "pair": item.get("pair"),
                    "contract_type": item.get("contractType"),
                    "base_asset": item.get("baseAsset"),
                    "quote_asset": item.get("quoteAsset"),
                }
                for item in payload.get("symbols", [])
            ],
        }

    def _normalize_derivatives_ticker_list(self, market: str, payload: Any) -> dict[str, Any]:
        items = payload if isinstance(payload, list) else [payload]
        return {
            "exchange": "binance",
            "market": market,
            "items": [self._normalize_ticker_item(item) for item in items],
        }

    def _normalize_mark_price_list(self, market: str, payload: Any) -> dict[str, Any]:
        items = payload if isinstance(payload, list) else [payload]
        return {
            "exchange": "binance",
            "market": market,
            "items": [
                {
                    "symbol": item.get("symbol"),
                    "pair": item.get("pair"),
                    "mark_price": self._to_float(item.get("markPrice")),
                    "index_price": self._to_float(item.get("indexPrice")),
                    "estimated_settle_price": self._to_float(item.get("estimatedSettlePrice")),
                    "last_funding_rate": self._to_float(item.get("lastFundingRate")),
                    "next_funding_time": self._to_int(item.get("nextFundingTime")),
                    "interest_rate": self._to_float(item.get("interestRate")),
                    "time": self._to_int(item.get("time")),
                }
                for item in items
            ],
        }

    def _normalize_open_interest_snapshot(self, market: str, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "exchange": "binance",
            "market": market,
            "symbol": payload.get("symbol"),
            "pair": payload.get("pair"),
            "open_interest": self._to_float(payload.get("openInterest")),
            "contract_type": payload.get("contractType"),
            "time": self._to_int(payload.get("time")),
        }

    def _normalize_open_interest_stats(self, market: str, payload: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "exchange": "binance",
            "market": market,
            "items": [
                {
                    "symbol": item.get("symbol"),
                    "pair": item.get("pair"),
                    "contract_type": item.get("contractType"),
                    "sum_open_interest": self._to_float(item.get("sumOpenInterest")),
                    "sum_open_interest_value": self._to_float(item.get("sumOpenInterestValue")),
                    "timestamp": self._to_int(item.get("timestamp")),
                }
                for item in payload
            ],
        }

    def _normalize_ratio_series(self, market: str, payload: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "exchange": "binance",
            "market": market,
            "items": [
                {
                    "symbol": item.get("symbol"),
                    "pair": item.get("pair"),
                    "long_short_ratio": self._to_float(item.get("longShortRatio")),
                    "long_account": self._to_float(item.get("longAccount")),
                    "short_account": self._to_float(item.get("shortAccount")),
                    "long_position": self._to_float(item.get("longPosition")),
                    "short_position": self._to_float(item.get("shortPosition")),
                    "timestamp": self._to_int(item.get("timestamp")),
                }
                for item in payload
            ],
        }

    def _normalize_taker_volume(self, market: str, payload: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "exchange": "binance",
            "market": market,
            "items": [
                {
                    "symbol": item.get("symbol"),
                    "pair": item.get("pair"),
                    "buy_sell_ratio": self._to_float(item.get("buySellRatio")),
                    "buy_vol": self._to_float(item.get("buyVol")),
                    "sell_vol": self._to_float(item.get("sellVol")),
                    "buy_vol_value": self._to_float(item.get("buyVolValue")),
                    "sell_vol_value": self._to_float(item.get("sellVolValue")),
                    "timestamp": self._to_int(item.get("timestamp")),
                }
                for item in payload
            ],
        }

    def _normalize_basis(self, market: str, payload: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "exchange": "binance",
            "market": market,
            "items": [
                {
                    "symbol": item.get("symbol"),
                    "pair": item.get("pair"),
                    "contract_type": item.get("contractType"),
                    "basis": self._to_float(item.get("basis")),
                    "basis_rate": self._to_float(item.get("basisRate")),
                    "annualized_basis_rate": self._to_float(item.get("annualizedBasisRate")),
                    "futures_price": self._to_float(item.get("futuresPrice")),
                    "index_price": self._to_float(item.get("indexPrice")),
                    "timestamp": self._to_int(item.get("timestamp")),
                }
                for item in payload
            ],
        }

    def _to_float(self, value: Any) -> float | None:
        if value in (None, ""):
            return None
        return float(value)

    def _to_int(self, value: Any) -> int | None:
        if value in (None, ""):
            return None
        return int(value)
