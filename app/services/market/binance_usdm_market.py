from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from .binance_api_support import BinanceApiSupport, compact_query
from .binance_market_normalizers import (
    normalize_basis,
    normalize_derivatives_exchange_info,
    normalize_derivatives_ticker_list,
    normalize_force_orders,
    normalize_kline_response,
    normalize_mark_price_list,
    normalize_open_interest_snapshot,
    normalize_open_interest_stats,
    normalize_ratio_series,
    normalize_taker_volume,
)
from .binance_numbers import to_float, to_int
from .binance_research_series import BinanceResearchSeriesLoader
from app.infra.persistence.market.binance_market_research_store import BinanceMarketResearchStore
from app.infra.persistence.market.funding_rate_store import FundingRateStore


class BinanceUsdmMarketService:
    def __init__(
        self,
        client: BinanceApiSupport,
        *,
        research_store: BinanceMarketResearchStore,
        funding_rate_store: FundingRateStore,
    ) -> None:
        self.client = client
        self.research_store = research_store
        self.funding_rate_store = funding_rate_store
        self.research_series = BinanceResearchSeriesLoader(
            market="usdm",
            store=research_store,
            get_json=client.get_json,
        )

    async def get_exchange_info(self) -> dict[str, object]:
        payload = await self.client.get_json("/fapi/v1/exchangeInfo", ttl=300)
        return normalize_derivatives_exchange_info("usdm", payload)

    async def get_ticker_24hr(self, *, symbol: str | None = None) -> dict[str, object]:
        payload = await self.client.get_json(
            "/fapi/v1/ticker/24hr",
            params=compact_query({"symbol": symbol.upper() if symbol else None}),
            ttl=10,
        )
        return normalize_derivatives_ticker_list("usdm", payload)

    async def get_mark_price(self, *, symbol: str | None = None) -> dict[str, object]:
        payload = await self.client.get_json(
            "/fapi/v1/premiumIndex",
            params=compact_query({"symbol": symbol.upper() if symbol else None}),
            ttl=10,
        )
        return normalize_mark_price_list("usdm", payload)

    async def get_klines(
        self,
        *,
        symbol: str,
        interval: str,
        limit: int = 200,
        start_time: int | None = None,
        end_time: int | None = None,
    ) -> dict[str, object]:
        symbol_key = symbol.upper()
        return await self.research_series.load(
            endpoint="/fapi/v1/klines",
            params=compact_query(
                {
                    "symbol": symbol_key,
                    "interval": interval,
                    "limit": limit,
                    "startTime": start_time,
                    "endTime": end_time,
                }
            ),
            normalizer=lambda market, payload: normalize_kline_response(market, symbol_key, interval, payload),
            series="klines",
            symbol=symbol_key,
            period=interval,
            limit=limit,
            start_time=start_time,
            end_time=end_time,
            timestamp_key="open_time",
            response_fields={"symbol": symbol_key, "interval": interval},
        )

    async def get_funding_info(self) -> dict[str, object]:
        payload = await self.client.get_json("/fapi/v1/fundingInfo", ttl=300)
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

    async def get_funding_history(
        self,
        *,
        symbol: str | None = None,
        limit: int = 100,
        start_time: int | None = None,
        end_time: int | None = None,
    ) -> dict[str, object]:
        symbol_key = symbol.upper() if symbol else None
        try:
            payload = await self.client.get_json(
                "/fapi/v1/fundingRate",
                params=compact_query(
                    {
                        "symbol": symbol_key,
                        "limit": limit,
                        "startTime": start_time,
                        "endTime": end_time,
                    }
                ),
                ttl=30,
            )
        except Exception:
            stored_response = self._funding_history_from_store(
                symbol=symbol_key,
                start_time=start_time,
                end_time=end_time,
                limit=limit,
            )
            if stored_response["items"]:
                return stored_response
            raise

        response = {
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
        self._save_funding_history_items(response["items"])
        return self._funding_history_from_store(
            symbol=symbol_key,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )

    async def get_open_interest(self, *, symbol: str) -> dict[str, object]:
        payload = await self.client.get_json("/fapi/v1/openInterest", params={"symbol": symbol.upper()}, ttl=10)
        return normalize_open_interest_snapshot("usdm", payload)

    async def get_open_interest_stats(
        self,
        *,
        symbol: str,
        period: str,
        limit: int = 30,
    ) -> dict[str, object]:
        return await self.research_series.load(
            endpoint="/futures/data/openInterestHist",
            params={"symbol": symbol.upper(), "period": period, "limit": limit},
            normalizer=normalize_open_interest_stats,
            series="open_interest_stats",
            symbol=symbol,
            period=period,
            limit=limit,
        )

    def get_cached_open_interest_stats(
        self,
        *,
        symbol: str,
        period: str,
        limit: int = 30,
    ) -> dict[str, object]:
        return {
            "exchange": "binance",
            "market": "usdm",
            "items": self.research_store.list_items(
                market="usdm",
                series="open_interest_stats",
                symbol=symbol,
                period=period,
                limit=limit,
            ),
        }

    async def get_long_short_ratio(self, *, symbol: str, period: str, limit: int = 30) -> dict[str, object]:
        return await self.research_series.load(
            endpoint="/futures/data/globalLongShortAccountRatio",
            params={"symbol": symbol.upper(), "period": period, "limit": limit},
            normalizer=normalize_ratio_series,
            series="global_long_short_account_ratio",
            symbol=symbol,
            period=period,
            limit=limit,
        )

    async def get_top_trader_accounts(self, *, symbol: str, period: str, limit: int = 30) -> dict[str, object]:
        return await self.research_series.load(
            endpoint="/futures/data/topLongShortAccountRatio",
            params={"symbol": symbol.upper(), "period": period, "limit": limit},
            normalizer=normalize_ratio_series,
            series="top_trader_account_ratio",
            symbol=symbol,
            period=period,
            limit=limit,
        )

    async def get_top_trader_positions(self, *, symbol: str, period: str, limit: int = 30) -> dict[str, object]:
        return await self.research_series.load(
            endpoint="/futures/data/topLongShortPositionRatio",
            params={"symbol": symbol.upper(), "period": period, "limit": limit},
            normalizer=normalize_ratio_series,
            series="top_trader_position_ratio",
            symbol=symbol,
            period=period,
            limit=limit,
        )

    async def get_taker_volume(self, *, symbol: str, period: str, limit: int = 30) -> dict[str, object]:
        return await self.research_series.load(
            endpoint="/futures/data/takerlongshortRatio",
            params={"symbol": symbol.upper(), "period": period, "limit": limit},
            normalizer=normalize_taker_volume,
            series="taker_long_short_ratio",
            symbol=symbol,
            period=period,
            limit=limit,
        )

    async def get_basis(
        self,
        *,
        pair: str,
        contract_type: str,
        period: str,
        limit: int = 30,
    ) -> dict[str, object]:
        return await self.research_series.load(
            endpoint="/futures/data/basis",
            params={"pair": pair.upper(), "contractType": contract_type, "period": period, "limit": limit},
            normalizer=normalize_basis,
            series="basis",
            symbol=pair,
            period=period,
            contract_type=contract_type,
            limit=limit,
        )

    async def get_force_orders(
        self,
        *,
        symbol: str,
        limit: int = 50,
        start_time: int | None = None,
        end_time: int | None = None,
    ) -> dict[str, object]:
        payload = await self.client.get_json(
            "/fapi/v1/allForceOrders",
            params=compact_query(
                {
                    "symbol": symbol.upper(),
                    "limit": limit,
                    "startTime": start_time,
                    "endTime": end_time,
                }
            ),
            ttl=30,
        )
        return normalize_force_orders("usdm", payload)

    async def get_contract_research_detail(
        self,
        *,
        symbol: str,
        period: str = "1h",
        limit: int = 72,
    ) -> dict[str, object]:
        symbol_key = symbol.upper()
        return {
            "exchange": "binance",
            "market": "usdm",
            "symbol": symbol_key,
            "period": period,
            "open_interest": (await self._safe_series(self.get_open_interest_stats, symbol=symbol_key, period=period, limit=limit)),
            "basis": (await self._safe_series(self.get_basis, pair=symbol_key, contract_type="PERPETUAL", period=period, limit=limit)),
            "taker_volume": (await self._safe_series(self.get_taker_volume, symbol=symbol_key, period=period, limit=limit)),
            "force_orders": (await self._safe_series(self.get_force_orders, symbol=symbol_key, limit=min(limit, 100))),
            "long_short_ratio": (await self._safe_series(self.get_long_short_ratio, symbol=symbol_key, period=period, limit=limit)),
            "top_trader_accounts": (await self._safe_series(self.get_top_trader_accounts, symbol=symbol_key, period=period, limit=limit)),
            "top_trader_positions": (await self._safe_series(self.get_top_trader_positions, symbol=symbol_key, period=period, limit=limit)),
        }

    async def _safe_series(self, loader: Callable[..., Any], **kwargs):
        try:
            return await loader(**kwargs)
        except Exception:
            name = getattr(loader, "__name__", "")
            if name not in {
                "get_open_interest_stats",
                "get_basis",
                "get_taker_volume",
                "get_force_orders",
                "get_long_short_ratio",
                "get_top_trader_accounts",
                "get_top_trader_positions",
            }:
                raise
            return {"exchange": "binance", "market": "usdm", "items": []}

    def _save_funding_history_items(self, items: list[dict[str, Any]]) -> None:
        rows = []
        for item in items:
            symbol = item.get("symbol")
            funding_time = item.get("funding_time")
            funding_rate = item.get("funding_rate")
            if symbol is None or funding_time is None or funding_rate is None:
                continue
            rows.append({
                "exchange": "binance",
                "market_type": "usdm",
                "symbol": str(symbol).upper(),
                "funding_time": self._datetime_from_millis(int(funding_time)),
                "funding_rate": funding_rate,
                "mark_price": item.get("mark_price"),
            })
        self.funding_rate_store.save_many(rows)

    def _funding_history_from_store(
        self,
        *,
        symbol: str | None,
        start_time: int | None,
        end_time: int | None,
        limit: int,
    ) -> dict[str, object]:
        rows = self.funding_rate_store.list_history(
            exchange="binance",
            market_type="usdm",
            symbol=symbol,
            start_date=self._datetime_from_millis(start_time) if start_time is not None else None,
            end_date=self._datetime_from_millis(end_time) if end_time is not None else None,
            limit=limit,
        )
        return {
            "exchange": "binance",
            "market": "usdm",
            "items": [
                {
                    "symbol": row["symbol"],
                    "funding_rate": row["funding_rate"],
                    "mark_price": row["mark_price"],
                    "funding_time": self._millis_from_datetime(row["funding_time"]),
                }
                for row in rows
            ],
        }

    @staticmethod
    def _datetime_from_millis(value: int) -> datetime:
        return datetime.fromtimestamp(value / 1000, tz=timezone.utc).replace(tzinfo=None)

    @staticmethod
    def _millis_from_datetime(value: datetime) -> int:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return int(value.timestamp() * 1000)
