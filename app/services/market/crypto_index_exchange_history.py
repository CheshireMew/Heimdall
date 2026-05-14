from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from config import settings
from utils.logger import logger


@dataclass(frozen=True, slots=True)
class ExchangeClose:
    timestamp: int
    close: float


class CryptoIndexExchangeHistory:
    def __init__(
        self,
        *,
        binance_base_url: str | None = None,
        okx_base_url: str | None = None,
    ) -> None:
        self.binance_base_url = (binance_base_url or settings.BINANCE_PUBLIC_BASE_URL).rstrip("/")
        self.okx_base_url = (okx_base_url or settings.OKX_PUBLIC_BASE_URL).rstrip("/")

    async def get_daily_closes(
        self,
        client: httpx.AsyncClient,
        symbol: str,
        days: int,
    ) -> list[ExchangeClose]:
        if self.preferred_exchange(symbol) == "okx":
            return await self.get_okx_daily_closes(client, symbol, days)
        return await self.get_binance_daily_closes(client, symbol, days)

    def preferred_exchange(self, symbol: str) -> str:
        if symbol.upper() == "OKB":
            return "okx"
        return "binance"

    async def get_binance_daily_closes(
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
            return self.normalize_binance_closes(spot_rows, days)

        usdm_rows = await self._get_binance_kline_rows(
            client,
            url=f"{settings.BINANCE_FUTURES_USDM_BASE_URL.rstrip('/')}/fapi/v1/klines",
            params=params,
            pair_symbol=pair_symbol,
            market="usdm",
        )
        return self.normalize_binance_closes(usdm_rows, days)

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

    async def get_okx_daily_closes(
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
            return self.normalize_okx_closes(rows, days)
        except Exception as exc:
            logger.debug(f"OKX crypto index history unavailable for {instrument_id}: {exc}")
            return []

    @staticmethod
    def normalize_binance_closes(rows: Any, days: int) -> list[ExchangeClose]:
        closes: list[ExchangeClose] = []
        if not isinstance(rows, list):
            return closes
        for row in rows:
            if not isinstance(row, list) or len(row) < 5:
                continue
            timestamp = positive_int(row[0])
            close = positive_float(row[4])
            if timestamp and close:
                closes.append(ExchangeClose(timestamp=timestamp, close=close))
        return sorted(closes, key=lambda item: item.timestamp)[-days:]

    @staticmethod
    def normalize_okx_closes(rows: Any, days: int) -> list[ExchangeClose]:
        closes: list[ExchangeClose] = []
        if not isinstance(rows, list):
            return closes
        for row in rows:
            if not isinstance(row, list) or len(row) < 5:
                continue
            timestamp = positive_int(row[0])
            close = positive_float(row[4])
            if timestamp and close:
                closes.append(ExchangeClose(timestamp=timestamp, close=close))
        unique = {item.timestamp: item for item in closes}
        return sorted(unique.values(), key=lambda item: item.timestamp)[-days:]


def positive_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def positive_int(value: Any) -> int | None:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None
