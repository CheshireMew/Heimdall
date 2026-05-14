from __future__ import annotations

import asyncio
import hashlib
from typing import Any, Dict, List

import httpx

from app.infra.cache import RedisService, optional_cache_get, optional_cache_set
from app.services.market.crypto_index_calculator import build_crypto_index_payload
from app.services.market.crypto_index_exchange_history import CryptoIndexExchangeHistory, positive_float
from config import settings
from utils.logger import logger


class CryptoIndexService:
    """Build a fixed-basket crypto market index from current top-N market cap coins."""

    def __init__(
        self,
        cache_service: RedisService | None = None,
        exchange_history: CryptoIndexExchangeHistory | None = None,
    ) -> None:
        self.cache_service = cache_service
        self.exchange_history = exchange_history or CryptoIndexExchangeHistory()
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

        market_cap = positive_float(coin.get("market_cap"))
        current_price = positive_float(coin.get("price"))
        if market_cap and current_price:
            exchange_closes = await self.exchange_history.get_daily_closes(client, symbol, days)
            if exchange_closes:
                market_caps = [
                    [row.timestamp, market_cap * row.close / current_price]
                    for row in exchange_closes
                    if row.close > 0
                ]
                if market_caps:
                    source = self.exchange_history.preferred_exchange(symbol)
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

    async def build_index(self, top_n: int = 20, days: int = 90, base_value: float = 1000.0) -> Dict[str, Any]:
        index_cache_key = self._index_cache_key(top_n, days, base_value)
        cached_index = optional_cache_get(self.cache_service, index_cache_key)
        if cached_index is not None:
            return cached_index

        constituents = await self.get_top_market_caps(top_n)

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

        result = build_crypto_index_payload(
            top_n=top_n,
            days=days,
            base_value=base_value,
            constituents=constituents,
            histories=histories,
        )
        optional_cache_set(
            self.cache_service,
            index_cache_key,
            result,
            ttl=self.cache_ttl if not result["is_partial"] else max(60, self.cache_ttl // 3),
            default_ttl=self.cache_ttl,
        )
        return result
