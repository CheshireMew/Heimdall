from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.infra.cache import RedisService, optional_cache_get, optional_cache_set
from app.services.market.ttl_cache import TtlMemoryCache
from config import settings


DLI_LIQUIDITY_CACHE_PREFIX = "market:dli:liquidity:v1"


class DliLiquidityCache:
    def __init__(
        self,
        *,
        cache_service: RedisService | None = None,
        ttl_seconds: int | None = None,
    ) -> None:
        self.cache_service = cache_service
        self.ttl_seconds = int(ttl_seconds or settings.DLI_CACHE_TTL)
        self.memory_cache: TtlMemoryCache[str, dict[str, Any]] = TtlMemoryCache(
            self.ttl_seconds,
            copy_value=deepcopy,
        )

    @staticmethod
    def key(days: int) -> str:
        return f"{DLI_LIQUIDITY_CACHE_PREFIX}:days:{days}"

    def get(self, *, days: int) -> dict[str, Any] | None:
        cache_key = self.key(days)
        cached = self.memory_cache.get(cache_key)
        if cached is not None:
            return cached

        cached = optional_cache_get(self.cache_service, cache_key)
        if not isinstance(cached, dict):
            return None

        self.memory_cache.set(cache_key, cached)
        return deepcopy(cached)

    def set(self, *, days: int, payload: dict[str, Any]) -> None:
        cache_key = self.key(days)
        self.memory_cache.set(cache_key, payload)
        optional_cache_set(
            self.cache_service,
            cache_key,
            payload,
            ttl=self.ttl_seconds,
            default_ttl=self.ttl_seconds,
        )

    def invalidate_all(self) -> None:
        self.memory_cache.clear()
        if self.cache_service is not None:
            self.cache_service.delete_prefix(DLI_LIQUIDITY_CACHE_PREFIX)
