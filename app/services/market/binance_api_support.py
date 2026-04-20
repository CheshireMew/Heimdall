from __future__ import annotations

import asyncio
import hashlib
import json
from typing import Any
from urllib.parse import urlencode

import httpx

from config import settings
from utils.logger import logger

from app.infra.cache import RedisService


class BinanceApiSupport:
    def __init__(
        self,
        *,
        base_url: str,
        cache_namespace: str,
        user_agent: str | None = None,
        cache_service: RedisService | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.cache_namespace = cache_namespace
        self.user_agent = user_agent
        self.cache_service = cache_service
        self.timeout = settings.BINANCE_PUBLIC_TIMEOUT
        self.cache_ttl = settings.BINANCE_PUBLIC_CACHE_TTL
        self.max_retries = settings.BINANCE_PUBLIC_MAX_RETRIES
        self.retry_delay = settings.BINANCE_PUBLIC_RETRY_DELAY

    def _headers(self, extra_headers: dict[str, str] | None = None) -> dict[str, str]:
        headers = {"accept": "application/json", "Accept-Encoding": "identity"}
        if self.user_agent:
            headers["User-Agent"] = self.user_agent
        if extra_headers:
            headers.update(extra_headers)
        return headers

    def _cache_key(self, method: str, path: str, params: dict[str, Any] | None, body: dict[str, Any] | None) -> str:
        raw = json.dumps(
            {
                "base_url": self.base_url,
                "method": method,
                "path": path,
                "params": params or {},
                "body": body or {},
            },
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        digest = hashlib.md5(raw.encode("utf-8")).hexdigest()
        return f"{self.cache_namespace}:{digest}"

    def _cache_get(self, key: str) -> Any | None:
        if self.cache_service is None:
            return None
        return self.cache_service.get(key)

    def _cache_set(self, key: str, value: Any, ttl: int | None = None) -> None:
        if self.cache_service is None:
            return
        self.cache_service.set(key, value, ttl=ttl or self.cache_ttl)

    async def _request_json(
        self,
        *,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
        ttl: int | None = None,
        extra_headers: dict[str, str] | None = None,
        use_cache: bool = True,
    ) -> Any:
        cache_key = self._cache_key(method, path, params, body)
        if use_cache:
            cached = self._cache_get(cache_key)
            if cached is not None:
                return cached

        last_error: Exception | None = None
        async with httpx.AsyncClient(timeout=self.timeout, headers=self._headers(extra_headers)) as client:
            for attempt in range(1, self.max_retries + 1):
                try:
                    response = await client.request(
                        method=method,
                        url=f"{self.base_url}{path}",
                        params=params,
                        json=body,
                    )
                    response.raise_for_status()
                    payload = response.json()
                    if use_cache:
                        self._cache_set(cache_key, payload, ttl=ttl)
                    return payload
                except httpx.HTTPStatusError as exc:
                    last_error = exc
                    status_code = exc.response.status_code
                    if status_code >= 500 and attempt < self.max_retries:
                        await asyncio.sleep(self.retry_delay * attempt)
                        continue
                    logger.warning(f"Binance API request failed: {method} {path} status={status_code}")
                    break
                except httpx.RequestError as exc:
                    last_error = exc
                    if attempt < self.max_retries:
                        await asyncio.sleep(self.retry_delay * attempt)
                        continue
                    logger.warning(f"Binance API request error: {method} {path} error={exc}")
                    break

        if last_error is not None:
            raise last_error
        raise RuntimeError(f"Binance API request failed: {method} {path}")

    async def get_json(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        ttl: int | None = None,
        extra_headers: dict[str, str] | None = None,
        use_cache: bool = True,
    ) -> Any:
        return await self._request_json(
            method="GET",
            path=path,
            params=params,
            ttl=ttl,
            extra_headers=extra_headers,
            use_cache=use_cache,
        )

    async def post_json(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
        ttl: int | None = None,
        extra_headers: dict[str, str] | None = None,
        use_cache: bool = True,
    ) -> Any:
        return await self._request_json(
            method="POST",
            path=path,
            params=params,
            body=body,
            ttl=ttl,
            extra_headers=extra_headers,
            use_cache=use_cache,
        )


def encode_symbol_list(symbols: list[str] | None) -> str | None:
    if not symbols:
        return None
    return json.dumps([str(symbol).upper() for symbol in symbols], separators=(",", ":"))


def compact_query(params: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in params.items()
        if value is not None and value != "" and value != []
    }


def build_query_key(params: dict[str, Any]) -> str:
    return urlencode(compact_query(params), doseq=True)
