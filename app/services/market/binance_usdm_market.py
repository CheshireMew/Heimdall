from __future__ import annotations

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


class BinanceUsdmMarketService:
    def __init__(self, client: BinanceApiSupport) -> None:
        self.client = client

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
        payload = await self.client.get_json(
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
        return BinanceKlineResponse.model_validate(normalize_kline_response("usdm", symbol.upper(), interval, payload))

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
        payload = await self.client.get_json(
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
        return BinanceFundingHistoryListResponse.model_validate({
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
        payload = await self.client.get_json(
            "/futures/data/openInterestHist",
            params={"symbol": symbol.upper(), "period": period, "limit": limit},
            ttl=30,
        )
        return BinanceOpenInterestStatsResponse.model_validate(normalize_open_interest_stats("usdm", payload))

    async def get_long_short_ratio(self, *, symbol: str, period: str, limit: int = 30) -> BinanceRatioSeriesResponse:
        payload = await self.client.get_json(
            "/futures/data/globalLongShortAccountRatio",
            params={"symbol": symbol.upper(), "period": period, "limit": limit},
            ttl=30,
        )
        return BinanceRatioSeriesResponse.model_validate(normalize_ratio_series("usdm", payload))

    async def get_top_trader_accounts(self, *, symbol: str, period: str, limit: int = 30) -> BinanceRatioSeriesResponse:
        payload = await self.client.get_json(
            "/futures/data/topLongShortAccountRatio",
            params={"symbol": symbol.upper(), "period": period, "limit": limit},
            ttl=30,
        )
        return BinanceRatioSeriesResponse.model_validate(normalize_ratio_series("usdm", payload))

    async def get_top_trader_positions(self, *, symbol: str, period: str, limit: int = 30) -> BinanceRatioSeriesResponse:
        payload = await self.client.get_json(
            "/futures/data/topLongShortPositionRatio",
            params={"symbol": symbol.upper(), "period": period, "limit": limit},
            ttl=30,
        )
        return BinanceRatioSeriesResponse.model_validate(normalize_ratio_series("usdm", payload))

    async def get_taker_volume(self, *, symbol: str, period: str, limit: int = 30) -> BinanceTakerVolumeResponse:
        payload = await self.client.get_json(
            "/futures/data/takerlongshortRatio",
            params={"symbol": symbol.upper(), "period": period, "limit": limit},
            ttl=30,
        )
        return BinanceTakerVolumeResponse.model_validate(normalize_taker_volume("usdm", payload))

    async def get_basis(
        self,
        *,
        pair: str,
        contract_type: str,
        period: str,
        limit: int = 30,
    ) -> BinanceBasisResponse:
        payload = await self.client.get_json(
            "/futures/data/basis",
            params={"pair": pair.upper(), "contractType": contract_type, "period": period, "limit": limit},
            ttl=30,
        )
        return BinanceBasisResponse.model_validate(normalize_basis("usdm", payload))
