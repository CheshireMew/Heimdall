from __future__ import annotations

import asyncio
import hashlib
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List

import httpx

from config import settings
from utils.logger import logger

try:
    from app.infra.cache import redis_service
except ImportError:
    redis_service = None


class CryptoIndexService:
    """Build a fixed-basket crypto market index from current top-N market cap coins."""

    def __init__(self) -> None:
        self.base_url = settings.COINGECKO_BASE_URL.rstrip("/")
        self.api_key = settings.COINGECKO_API_KEY
        self.timeout = settings.COINGECKO_TIMEOUT
        self.max_concurrency = settings.COINGECKO_MAX_CONCURRENCY
        self.max_retries = settings.COINGECKO_MAX_RETRIES
        self.retry_delay = settings.COINGECKO_RETRY_DELAY
        self.request_gap = settings.COINGECKO_REQUEST_GAP
        self.cache_ttl = settings.COINGECKO_CACHE_TTL

    def _headers(self) -> Dict[str, str]:
        headers = {"accept": "application/json"}
        if self.api_key:
            headers["x-cg-pro-api-key"] = self.api_key
        return headers

    def _cache_get(self, key: str) -> Any | None:
        if redis_service is None:
            return None
        return redis_service.get(key)

    def _cache_set(self, key: str, value: Any, ttl: int | None = None) -> None:
        if redis_service is None:
            return
        redis_service.set(key, value, ttl=ttl or self.cache_ttl)

    def _index_cache_key(self, top_n: int, days: int, base_value: float) -> str:
        raw = f"crypto-index:{top_n}:{days}:{base_value}"
        return f"crypto_index:{hashlib.md5(raw.encode()).hexdigest()}"

    def _top_market_caps_cache_key(self, top_n: int) -> str:
        return f"crypto_index:top_market_caps:{top_n}"

    def _coin_history_cache_key(self, coin_id: str, days: int) -> str:
        return f"crypto_index:coin_history:{coin_id}:{days}"

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
        cached = self._cache_get(cache_key)
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
        self._cache_set(cache_key, result)
        return result

    async def _get_coin_market_caps(
        self,
        client: httpx.AsyncClient,
        coin_id: str,
        days: int,
    ) -> Dict[str, Any]:
        cache_key = self._coin_history_cache_key(coin_id, days)
        cached = self._cache_get(cache_key)
        if cached is not None:
            return {"id": coin_id, "market_caps": cached, "error": None}

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
                self._cache_set(cache_key, market_caps)
            return {"id": coin_id, "market_caps": market_caps, "error": None}
        except Exception as e:
            logger.warning(f"CoinGecko history fetch failed for {coin_id}: {e}")
            return {"id": coin_id, "market_caps": [], "error": str(e)}

    async def build_index(self, top_n: int = 20, days: int = 90, base_value: float = 1000.0) -> Dict[str, Any]:
        index_cache_key = self._index_cache_key(top_n, days, base_value)
        cached_index = self._cache_get(index_cache_key)
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
                            self._get_coin_market_caps(client, item["id"], days)
                            for item in chunk
                        ]
                    )
                )
                if start + self.max_concurrency < len(constituents):
                    await asyncio.sleep(self.request_gap)

        history_by_id = {item["id"]: item for item in histories}
        available_ids = {item["id"] for item in histories if item["market_caps"]}
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
            self._cache_set(index_cache_key, result, ttl=max(60, self.cache_ttl // 3))
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
            self._cache_set(index_cache_key, result, ttl=max(60, self.cache_ttl // 3))
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
                "methodology": "fixed-basket-market-cap-weighted-partial" if is_partial else "fixed-basket-market-cap-weighted",
            },
        }
        self._cache_set(index_cache_key, result, ttl=self.cache_ttl if not is_partial else max(60, self.cache_ttl // 3))
        return result
