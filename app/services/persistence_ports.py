from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any, Protocol


class CacheServicePort(Protocol):
    def get(self, key: str) -> Any | None: ...
    def set(self, key: str, value: Any, ttl: int = 300) -> bool: ...
    def delete_prefix(self, prefix: str) -> int: ...


class KlineStorePort(Protocol):
    def get_before(self, symbol: str, timeframe: str, end_ts: int, limit: int) -> list[list[float]]: ...
    def get_after(self, symbol: str, timeframe: str, start_ts: int, limit: int) -> list[list[float]]: ...
    def get_range(self, symbol: str, timeframe: str, start_ts: int, end_ts: int) -> list[list[float]]: ...
    def get_latest(self, symbol: str, timeframe: str, limit: int) -> list[list[float]]: ...
    def save_klines(self, symbol: str, timeframe: str, rows: list[list[float]]) -> int: ...


class IndicatorRepositoryPort(Protocol):
    pass


class FactorResearchRepositoryPort(Protocol):
    pass


class FundingRateStorePort(Protocol):
    pass


class BinanceMarketResearchStorePort(Protocol):
    pass


class SentimentRepositoryPort(Protocol):
    def get_latest_date(self) -> datetime | None: ...
    def save_missing(self, records: list[dict[str, Any]]) -> int: ...
    def list_history(self, start_date: datetime | None, end_date: datetime | None) -> dict[str, int]: ...
    def get_latest_index(self) -> dict[str, int | str] | None: ...


DataRetentionCleanup = Callable[[], Any]
