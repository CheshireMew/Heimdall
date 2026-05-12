from __future__ import annotations

import asyncio
import hashlib
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List

import httpx

from app.infra.cache import RedisService, optional_cache_get, optional_cache_set
from config import settings
from utils.logger import logger


@dataclass(frozen=True, slots=True)
class ExchangeClose:
    timestamp: int
    close: float


class CryptoIndexService:
    """Build a fixed-basket crypto market index from current top-N market cap coins."""

    def __init__(self, cache_service: RedisService | None = None) -> None:
        self.cache_service = cache_service
        self.base_url = settings.COINGECKO_BASE_URL.rstrip("/")
        self.api_key = settings.COINGECKO_API_KEY
        self.timeout = settings.COINGECKO_TIMEOUT
        self.max_concurrency = settings.COINGECKO_MAX_CONCURRENCY
        self.max_retries = settings.COINGECKO_MAX_RETRIES
        self.retry_delay = settings.COINGECKO_RETRY_DELAY
        self.request_gap = settings.COINGECKO_REQUEST_GAP
        self.cache_ttl = settings.COINGECKO_CACHE_TTL
        self.binance_base_url = settings.BINANCE_PUBLIC_BASE_URL.rstrip("/")
        self.okx_base_url = settings.OKX_PUBLIC_BASE_URL.rstrip("/")

    def _headers(self) -> Dict[str, str]:
        headers = {"accept": "application/json"}
        if self.api_key:
            headers["x-cg-pro-api-key"] = self.api_key
        return headers

    def _index_cache_key(self, top_n: int, days: int, base_value: float) -> str:
        raw = f"crypto-index:v2:{top_n}:{days}:{base_value}"
        return f"crypto_index:{hashlib.md5(raw.encode()).hexdigest()}"

    def _top_market_caps_cache_key(self, top_n: int) -> str:
        return f"crypto_index:top_market_caps:{top_n}"

    def _coin_history_cache_key(self, coin_id: str, symbol: str, days: int) -> str:
        return f"crypto_index:coin_history:v2:{coin_id}:{symbol}:{days}"

    @staticmethod
    def _retry_after_seconds(response: httpx.Response, default_delay: float) -> float:
        retry_after = response.headers.get("Retry-After")
        if not retry_after:
            return default_delay
        try:
            retry_after_seconds = float(retry_after)
            if retry_after_seconds <= 0:
                return default_delay
            return min(retry_after_seconds, default_delay)
        except ValueError:
            return default_delay

    async def _get_json(
        self,
        client: httpx.AsyncClient,
        path: str,
        params: Dict[str, Any],
        max_retries: int | None = None,
    ) -> Any:
        retries = max_retries or self.max_retries
        last_error: Exception | None = None
        for attempt in range(1, retries + 1):
            try:
                response = await client.get(f"{self.base_url}{path}", params=params)
                if response.status_code == 429 and attempt < retries:
                    delay = self._retry_after_seconds(response, self.retry_delay * attempt)
                    logger.warning(f"CoinGecko rate limit hit for {path}, retrying in {delay:.1f}s (attempt {attempt}/{retries})")
                    await asyncio.sleep(delay)
                    continue
                if response.status_code >= 500 and attempt < retries:
                    delay = self.retry_delay * attempt
                    logger.warning(f"CoinGecko upstream error {response.status_code} for {path}, retrying in {delay:.1f}s")
                    await asyncio.sleep(delay)
                    continue
                response.raise_for_status()
                return response.json()
            except httpx.RequestError as e:
                last_error = e
                if attempt >= retries:
                    break
                delay = self.retry_delay * attempt
                logger.warning(f"CoinGecko request failed for {path}: {e}. Retrying in {delay:.1f}s")
                await asyncio.sleep(delay)
            except httpx.HTTPStatusError as e:
                last_error = e
                break

        if last_error is not None:
            raise last_error
        raise RuntimeError(f"CoinGecko request failed for {path}")

    async def get_top_market_caps(self, top_n: int) -> List[Dict[str, Any]]:
        cache_key = self._top_market_caps_cache_key(top_n)
        cached = optional_cache_get(self.cache_service, cache_key)
        if cached is not None:
            return cached

        async with httpx.AsyncClient(timeout=self.timeout, headers=self._headers()) as client:
            data = await self._get_json(
                client,
                "/coins/markets",
                {
                    "vs_currency": "usd",
                    "order": "market_cap_desc",
                    "per_page": top_n,
                    "page": 1,
                    "sparkline": "false",
                    "price_change_percentage": "24h",
                },
                max_retries=max(self.max_retries + 2, 4),
            )

        result = [
            {
                "id": item["id"],
                "symbol": item["symbol"].upper(),
                "name": item["name"],
                "image": item.get("image"),
                "rank": item.get("market_cap_rank"),
                "price": item.get("current_price"),
                "market_cap": item.get("market_cap"),
                "market_cap_change_24h_pct": item.get("market_cap_change_percentage_24h"),
                "price_change_24h_pct": item.get("price_change_percentage_24h_in_currency"),
                "volume_24h": item.get("total_volume"),
            }
            for item in data
            if item.get("market_cap")
        ]
        optional_cache_set(self.cache_service, cache_key, result, ttl=None, default_ttl=self.cache_ttl)
        return result

    async def _get_coin_market_caps(
        self,
        client: httpx.AsyncClient,
        coin: dict[str, Any],
        days: int,
    ) -> Dict[str, Any]:
        coin_id = str(coin["id"])
        symbol = str(coin["symbol"]).upper()
        cache_key = self._coin_history_cache_key(coin_id, symbol, days)
        cached = optional_cache_get(self.cache_service, cache_key)
        if cached is not None:
            if isinstance(cached, dict):
                return {
                    "id": coin_id,
                    "market_caps": cached.get("market_caps") or [],
                    "source": cached.get("source") or "cache",
                    "error": None,
                }
            return {
                "id": coin_id,
                "market_caps": cached,
                "source": "cache",
                "error": None,
            }

        market_cap = self._positive_float(coin.get("market_cap"))
        current_price = self._positive_float(coin.get("price"))
        if market_cap and current_price:
            exchange_closes = await self._get_exchange_daily_closes(client, symbol, days)
            if exchange_closes:
                market_caps = [
                    [row.timestamp, market_cap * row.close / current_price]
                    for row in exchange_closes
                    if row.close > 0
                ]
                if market_caps:
                    source = self._preferred_exchange(symbol)
                    optional_cache_set(
                        self.cache_service,
                        cache_key,
                        {"market_caps": market_caps, "source": source},
                        ttl=None,
                        default_ttl=self.cache_ttl,
                    )
                    return {
                        "id": coin_id,
                        "market_caps": market_caps,
                        "source": source,
                        "error": None,
                    }

        try:
            data = await self._get_json(
                client,
                f"/coins/{coin_id}/market_chart",
                {
                    "vs_currency": "usd",
                    "days": days,
                    "interval": "daily",
                },
            )
            market_caps = data.get("market_caps", [])
            if market_caps:
                optional_cache_set(
                    self.cache_service,
                    cache_key,
                    {"market_caps": market_caps, "source": "coingecko"},
                    ttl=None,
                    default_ttl=self.cache_ttl,
                )
            return {"id": coin_id, "market_caps": market_caps, "source": "coingecko", "error": None}
        except Exception as e:
            logger.warning(f"CoinGecko history fetch failed for {coin_id}: {e}")
            return {"id": coin_id, "market_caps": [], "source": "coingecko", "error": str(e)}

    async def _get_exchange_daily_closes(
        self,
        client: httpx.AsyncClient,
        symbol: str,
        days: int,
    ) -> list[ExchangeClose]:
        if self._preferred_exchange(symbol) == "okx":
            return await self._get_okx_daily_closes(client, symbol, days)
        return await self._get_binance_daily_closes(client, symbol, days)

    def _preferred_exchange(self, symbol: str) -> str:
        if symbol.upper() == "OKB":
            return "okx"
        return "binance"

    async def _get_binance_daily_closes(
        self,
        client: httpx.AsyncClient,
        symbol: str,
        days: int,
    ) -> list[ExchangeClose]:
        pair_symbol = f"{symbol.upper()}USDT"
        params = {
            "symbol": pair_symbol,
            "interval": "1d",
            "limit": min(max(days + 5, 1), 1000),
        }
        spot_rows = await self._get_binance_kline_rows(
            client,
            url=f"{self.binance_base_url}/api/v3/klines",
            params=params,
            pair_symbol=pair_symbol,
            market="spot",
        )
        if spot_rows:
            return self._normalize_binance_closes(spot_rows, days)

        usdm_rows = await self._get_binance_kline_rows(
            client,
            url=f"{settings.BINANCE_FUTURES_USDM_BASE_URL.rstrip('/')}/fapi/v1/klines",
            params=params,
            pair_symbol=pair_symbol,
            market="usdm",
        )
        return self._normalize_binance_closes(usdm_rows, days)

    async def _get_binance_kline_rows(
        self,
        client: httpx.AsyncClient,
        *,
        url: str,
        params: dict[str, Any],
        pair_symbol: str,
        market: str,
    ) -> Any:
        try:
            response = await client.get(
                url,
                params=params,
                timeout=settings.BINANCE_PUBLIC_TIMEOUT,
            )
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            logger.debug(f"Binance {market} crypto index history unavailable for {pair_symbol}: {exc}")
            return []

    async def _get_okx_daily_closes(
        self,
        client: httpx.AsyncClient,
        symbol: str,
        days: int,
    ) -> list[ExchangeClose]:
        instrument_id = f"{symbol.upper()}-USDT"
        rows: list[Any] = []
        after: str | None = None
        try:
            while len(rows) < days + 5:
                params = {
                    "instId": instrument_id,
                    "bar": "1D",
                    "limit": min(100, days + 5 - len(rows)),
                }
                if after:
                    params["after"] = after
                response = await client.get(
                    f"{self.okx_base_url}/api/v5/market/history-candles",
                    params=params,
                    timeout=settings.BINANCE_PUBLIC_TIMEOUT,
                )
                response.raise_for_status()
                data = response.json().get("data") or []
                if not data:
                    break
                rows.extend(data)
                oldest_ts = str(data[-1][0])
                if oldest_ts == after or len(data) < params["limit"]:
                    break
                after = oldest_ts
            return self._normalize_okx_closes(rows, days)
        except Exception as exc:
            logger.debug(f"OKX crypto index history unavailable for {instrument_id}: {exc}")
            return []

    @staticmethod
    def _normalize_binance_closes(rows: Any, days: int) -> list[ExchangeClose]:
        closes: list[ExchangeClose] = []
        if not isinstance(rows, list):
            return closes
        for row in rows:
            if not isinstance(row, list) or len(row) < 5:
                continue
            timestamp = CryptoIndexService._positive_int(row[0])
            close = CryptoIndexService._positive_float(row[4])
            if timestamp and close:
                closes.append(ExchangeClose(timestamp=timestamp, close=close))
        return sorted(closes, key=lambda item: item.timestamp)[-days:]

    @staticmethod
    def _normalize_okx_closes(rows: Any, days: int) -> list[ExchangeClose]:
        closes: list[ExchangeClose] = []
        if not isinstance(rows, list):
            return closes
        for row in rows:
            if not isinstance(row, list) or len(row) < 5:
                continue
            timestamp = CryptoIndexService._positive_int(row[0])
            close = CryptoIndexService._positive_float(row[4])
            if timestamp and close:
                closes.append(ExchangeClose(timestamp=timestamp, close=close))
        unique = {item.timestamp: item for item in closes}
        return sorted(unique.values(), key=lambda item: item.timestamp)[-days:]

    @staticmethod
    def _positive_float(value: Any) -> float | None:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        return number if number > 0 else None

    @staticmethod
    def _positive_int(value: Any) -> int | None:
        try:
            number = int(value)
        except (TypeError, ValueError):
            return None
        return number if number > 0 else None

    async def build_index(self, top_n: int = 20, days: int = 90, base_value: float = 1000.0) -> Dict[str, Any]:
        index_cache_key = self._index_cache_key(top_n, days, base_value)
        cached_index = optional_cache_get(self.cache_service, index_cache_key)
        if cached_index is not None:
            return cached_index

        constituents = await self.get_top_market_caps(top_n)
        if not constituents:
            return {
                "top_n": top_n,
                "days": days,
                "base_value": base_value,
                "constituents": [],
                "history": [],
                "is_partial": False,
                "resolved_constituents_count": 0,
                "missing_symbols": [],
            }

        async with httpx.AsyncClient(timeout=self.timeout, headers=self._headers()) as client:
            histories: List[Dict[str, Any]] = []
            for start in range(0, len(constituents), self.max_concurrency):
                chunk = constituents[start:start + self.max_concurrency]
                histories.extend(
                    await asyncio.gather(
                        *[
                            self._get_coin_market_caps(client, item, days)
                            for item in chunk
                        ]
                    )
                )
                if start + self.max_concurrency < len(constituents):
                    await asyncio.sleep(self.request_gap)

        available_ids = {item["id"] for item in histories if item["market_caps"]}
        available_sources = {
            item.get("source")
            for item in histories
            if item.get("market_caps") and item.get("source")
        }
        filtered_constituents = [item for item in constituents if item["id"] in available_ids]
        missing_symbols = [item["symbol"] for item in constituents if item["id"] not in available_ids]
        is_partial = len(filtered_constituents) != len(constituents)

        series_by_coin: Dict[str, Dict[str, float]] = {}
        first_dates: List[str] = []
        all_dates = set()

        for item in histories:
            per_date: Dict[str, float] = {}
            for ts, market_cap in item["market_caps"]:
                date_key = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
                per_date[date_key] = market_cap
                all_dates.add(date_key)

            if per_date:
                first_date = min(per_date.keys())
                first_dates.append(first_date)
                series_by_coin[item["id"]] = per_date

        if not series_by_coin or not first_dates:
            result = {
                "top_n": top_n,
                "days": days,
                "base_value": base_value,
                "constituents": filtered_constituents,
                "history": [],
                "is_partial": True,
                "resolved_constituents_count": len(filtered_constituents),
                "missing_symbols": missing_symbols,
            }
            optional_cache_set(self.cache_service, index_cache_key, result, ttl=max(60, self.cache_ttl // 3), default_ttl=self.cache_ttl)
            return result

        common_start = max(first_dates)
        ordered_dates = sorted(date for date in all_dates if date >= common_start)

        rolling_caps: Dict[str, float] = {}
        aggregated_caps: Dict[str, float] = defaultdict(float)

        for date in ordered_dates:
            for coin_id, series in series_by_coin.items():
                if date in series:
                    rolling_caps[coin_id] = series[date]
                if coin_id in rolling_caps:
                    aggregated_caps[date] += rolling_caps[coin_id]

        valid_dates = [date for date in ordered_dates if aggregated_caps[date] > 0]
        if not valid_dates:
            result = {
                "top_n": top_n,
                "days": days,
                "base_value": base_value,
                "constituents": filtered_constituents,
                "history": [],
                "is_partial": True,
                "resolved_constituents_count": len(filtered_constituents),
                "missing_symbols": missing_symbols,
            }
            optional_cache_set(self.cache_service, index_cache_key, result, ttl=max(60, self.cache_ttl // 3), default_ttl=self.cache_ttl)
            return result

        base_cap = aggregated_caps[valid_dates[0]]
        history = [
            {
                "date": date,
                "timestamp": int(datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()),
                "market_cap": aggregated_caps[date],
                "index_value": round(base_value * aggregated_caps[date] / base_cap, 2),
            }
            for date in valid_dates
        ]

        current_basket_cap = sum(item["market_cap"] for item in filtered_constituents if item.get("market_cap"))
        weighted_change_numerator = sum(
            (item.get("market_cap_change_24h_pct") or 0) * (item.get("market_cap") or 0)
            for item in filtered_constituents
        )
        weighted_change = weighted_change_numerator / current_basket_cap if current_basket_cap else 0.0

        btc_market_cap = next((item["market_cap"] for item in filtered_constituents if item["symbol"] == "BTC"), 0)
        eth_market_cap = next((item["market_cap"] for item in filtered_constituents if item["symbol"] == "ETH"), 0)
        history_method = "exchange-price-history" if available_sources <= {"binance", "okx"} else "mixed-price-history"

        result = {
            "top_n": top_n,
            "days": days,
            "base_value": base_value,
            "constituents": filtered_constituents,
            "history": history,
            "is_partial": is_partial,
            "resolved_constituents_count": len(filtered_constituents),
            "missing_symbols": missing_symbols,
            "summary": {
                "current_basket_market_cap": current_basket_cap,
                "current_index_value": history[-1]["index_value"],
                "basket_change_24h_pct": round(weighted_change, 2),
                "btc_weight_pct": round((btc_market_cap / current_basket_cap) * 100, 2) if current_basket_cap else 0.0,
                "eth_weight_pct": round((eth_market_cap / current_basket_cap) * 100, 2) if current_basket_cap else 0.0,
                "common_start_date": valid_dates[0],
                "methodology": f"fixed-current-market-cap-weighted-{history_method}-partial" if is_partial else f"fixed-current-market-cap-weighted-{history_method}",
            },
        }
        optional_cache_set(
            self.cache_service,
            index_cache_key,
            result,
            ttl=self.cache_ttl if not is_partial else max(60, self.cache_ttl // 3),
            default_ttl=self.cache_ttl,
        )
        return result
