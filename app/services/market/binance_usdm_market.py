from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from app.schemas.binance_market import (
    BinanceBasisResponse,
    BinanceExchangeInfoResponse,
    BinanceFundingHistoryListResponse,
    BinanceFundingInfoResponse,
    BinanceKlineResponse,
    BinanceMarkPriceResponse,
    BinanceOpenInterestSnapshotResponse,
    BinanceOpenInterestStatsResponse,
    BinanceRatioSeriesResponse,
    BinanceTakerVolumeResponse,
    BinanceTickerStatsResponse,
)

from .binance_api_support import BinanceApiSupport, compact_query
from .binance_market_normalizers import (
    normalize_basis,
    normalize_derivatives_exchange_info,
    normalize_derivatives_ticker_list,
    normalize_kline_response,
    normalize_mark_price_list,
    normalize_open_interest_snapshot,
    normalize_open_interest_stats,
    normalize_ratio_series,
    normalize_taker_volume,
)
from .binance_numbers import to_float, to_int
from .binance_market_research_store import BinanceMarketResearchStore
from .funding_rate_store import FundingRateStore


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

    async def get_exchange_info(self) -> BinanceExchangeInfoResponse:
        payload = await self.client.get_json("/fapi/v1/exchangeInfo", ttl=300)
        return BinanceExchangeInfoResponse.model_validate(normalize_derivatives_exchange_info("usdm", payload))

    async def get_ticker_24hr(self, *, symbol: str | None = None) -> BinanceTickerStatsResponse:
        payload = await self.client.get_json(
            "/fapi/v1/ticker/24hr",
            params=compact_query({"symbol": symbol.upper() if symbol else None}),
            ttl=10,
        )
        return BinanceTickerStatsResponse.model_validate(normalize_derivatives_ticker_list("usdm", payload))

    async def get_mark_price(self, *, symbol: str | None = None) -> BinanceMarkPriceResponse:
        payload = await self.client.get_json(
            "/fapi/v1/premiumIndex",
            params=compact_query({"symbol": symbol.upper() if symbol else None}),
            ttl=10,
        )
        return BinanceMarkPriceResponse.model_validate(normalize_mark_price_list("usdm", payload))

    async def get_klines(
        self,
        *,
        symbol: str,
        interval: str,
        limit: int = 200,
        start_time: int | None = None,
        end_time: int | None = None,
    ) -> BinanceKlineResponse:
        symbol_key = symbol.upper()
        return await self._load_research_series(
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
            response_model=BinanceKlineResponse,
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

    async def get_funding_info(self) -> BinanceFundingInfoResponse:
        payload = await self.client.get_json("/fapi/v1/fundingInfo", ttl=300)
        return BinanceFundingInfoResponse.model_validate({
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
        })

    async def get_funding_history(
        self,
        *,
        symbol: str | None = None,
        limit: int = 100,
        start_time: int | None = None,
        end_time: int | None = None,
    ) -> BinanceFundingHistoryListResponse:
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
            if stored_response.items:
                return stored_response
            raise

        response = BinanceFundingHistoryListResponse.model_validate({
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
        })
        self._save_funding_history_items(response.model_dump()["items"])
        return self._funding_history_from_store(
            symbol=symbol_key,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )

    async def get_open_interest(self, *, symbol: str) -> BinanceOpenInterestSnapshotResponse:
        payload = await self.client.get_json("/fapi/v1/openInterest", params={"symbol": symbol.upper()}, ttl=10)
        return BinanceOpenInterestSnapshotResponse.model_validate(normalize_open_interest_snapshot("usdm", payload))

    async def get_open_interest_stats(
        self,
        *,
        symbol: str,
        period: str,
        limit: int = 30,
    ) -> BinanceOpenInterestStatsResponse:
        return await self._load_research_series(
            endpoint="/futures/data/openInterestHist",
            params={"symbol": symbol.upper(), "period": period, "limit": limit},
            response_model=BinanceOpenInterestStatsResponse,
            normalizer=normalize_open_interest_stats,
            series="open_interest_stats",
            symbol=symbol,
            period=period,
            limit=limit,
        )

    async def get_long_short_ratio(self, *, symbol: str, period: str, limit: int = 30) -> BinanceRatioSeriesResponse:
        return await self._load_research_series(
            endpoint="/futures/data/globalLongShortAccountRatio",
            params={"symbol": symbol.upper(), "period": period, "limit": limit},
            response_model=BinanceRatioSeriesResponse,
            normalizer=normalize_ratio_series,
            series="global_long_short_account_ratio",
            symbol=symbol,
            period=period,
            limit=limit,
        )

    async def get_top_trader_accounts(self, *, symbol: str, period: str, limit: int = 30) -> BinanceRatioSeriesResponse:
        return await self._load_research_series(
            endpoint="/futures/data/topLongShortAccountRatio",
            params={"symbol": symbol.upper(), "period": period, "limit": limit},
            response_model=BinanceRatioSeriesResponse,
            normalizer=normalize_ratio_series,
            series="top_trader_account_ratio",
            symbol=symbol,
            period=period,
            limit=limit,
        )

    async def get_top_trader_positions(self, *, symbol: str, period: str, limit: int = 30) -> BinanceRatioSeriesResponse:
        return await self._load_research_series(
            endpoint="/futures/data/topLongShortPositionRatio",
            params={"symbol": symbol.upper(), "period": period, "limit": limit},
            response_model=BinanceRatioSeriesResponse,
            normalizer=normalize_ratio_series,
            series="top_trader_position_ratio",
            symbol=symbol,
            period=period,
            limit=limit,
        )

    async def get_taker_volume(self, *, symbol: str, period: str, limit: int = 30) -> BinanceTakerVolumeResponse:
        return await self._load_research_series(
            endpoint="/futures/data/takerlongshortRatio",
            params={"symbol": symbol.upper(), "period": period, "limit": limit},
            response_model=BinanceTakerVolumeResponse,
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
    ) -> BinanceBasisResponse:
        return await self._load_research_series(
            endpoint="/futures/data/basis",
            params={"pair": pair.upper(), "contractType": contract_type, "period": period, "limit": limit},
            response_model=BinanceBasisResponse,
            normalizer=normalize_basis,
            series="basis",
            symbol=pair,
            period=period,
            contract_type=contract_type,
            limit=limit,
        )

    async def _load_research_series(
        self,
        *,
        endpoint: str,
        params: dict[str, Any],
        response_model,
        normalizer: Callable[[str, list[dict[str, Any]]], dict[str, Any]],
        series: str,
        symbol: str,
        period: str,
        contract_type: str = "",
        limit: int,
        start_time: int | None = None,
        end_time: int | None = None,
        timestamp_key: str = "timestamp",
        response_fields: dict[str, Any] | None = None,
    ):
        response_fields = response_fields or {}
        try:
            payload = await self.client.get_json(endpoint, params=params, ttl=30)
        except Exception:
            stored_items = self.research_store.list_items(
                market="usdm",
                series=series,
                symbol=symbol,
                period=period,
                contract_type=contract_type,
                start_time=start_time,
                end_time=end_time,
                limit=limit,
            )
            if stored_items:
                return response_model.model_validate({
                    "exchange": "binance",
                    "market": "usdm",
                    **response_fields,
                    "items": stored_items,
                })
            raise

        response = response_model.model_validate(normalizer("usdm", payload))
        items = response.model_dump()["items"]
        self.research_store.save_items(
            market="usdm",
            series=series,
            symbol=symbol,
            items=items,
            period=period,
            contract_type=contract_type,
            timestamp_key=timestamp_key,
        )
        stored_items = self.research_store.list_items(
            market="usdm",
            series=series,
            symbol=symbol,
            period=period,
            contract_type=contract_type,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )
        return response_model.model_validate({
            "exchange": "binance",
            "market": "usdm",
            **response_fields,
            "items": stored_items or items,
        })

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
    ) -> BinanceFundingHistoryListResponse:
        rows = self.funding_rate_store.list_history(
            exchange="binance",
            market_type="usdm",
            symbol=symbol,
            start_date=self._datetime_from_millis(start_time) if start_time is not None else None,
            end_date=self._datetime_from_millis(end_time) if end_time is not None else None,
            limit=limit,
        )
        return BinanceFundingHistoryListResponse.model_validate({
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
        })

    @staticmethod
    def _datetime_from_millis(value: int) -> datetime:
        return datetime.fromtimestamp(value / 1000, tz=timezone.utc).replace(tzinfo=None)

    @staticmethod
    def _millis_from_datetime(value: datetime) -> int:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return int(value.timestamp() * 1000)
