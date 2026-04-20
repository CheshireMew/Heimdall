from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app.schemas.market import CurrencyRatesResponse
from config import settings
from utils.logger import logger


FALLBACK_RATES_PER_USD: dict[str, float] = {
    "USD": 1.0,
    "CNY": 7.25,
    "EUR": 0.92,
    "GBP": 0.79,
    "JPY": 150.0,
    "HKD": 7.8,
    "SGD": 1.35,
    "AUD": 1.52,
}

DISPLAY_CURRENCY_META: dict[str, dict[str, Any]] = {
    "USD": {"name": "US Dollar", "symbol": "$", "locale": "en-US", "fraction_digits": 2},
    "CNY": {"name": "人民币", "symbol": "¥", "locale": "zh-CN", "fraction_digits": 2},
    "EUR": {"name": "Euro", "symbol": "€", "locale": "de-DE", "fraction_digits": 2},
    "GBP": {"name": "British Pound", "symbol": "£", "locale": "en-GB", "fraction_digits": 2},
    "JPY": {"name": "Japanese Yen", "symbol": "¥", "locale": "ja-JP", "fraction_digits": 0},
    "HKD": {"name": "Hong Kong Dollar", "symbol": "HK$", "locale": "zh-HK", "fraction_digits": 2},
    "SGD": {"name": "Singapore Dollar", "symbol": "S$", "locale": "en-SG", "fraction_digits": 2},
    "AUD": {"name": "Australian Dollar", "symbol": "A$", "locale": "en-AU", "fraction_digits": 2},
}


class CurrencyRateService:
    def __init__(self) -> None:
        self._cache: CurrencyRatesResponse | None = None
        self._expires_at: datetime | None = None

    async def get_rates(self) -> CurrencyRatesResponse:
        now = datetime.now(timezone.utc)
        if self._cache and self._expires_at and self._expires_at > now:
            return self._cache

        payload = await self._fetch_rates(now)
        self._cache = payload
        self._expires_at = now + timedelta(seconds=max(settings.CURRENCY_RATES_TTL, 60))
        return payload

    async def _fetch_rates(self, now: datetime) -> CurrencyRatesResponse:
        supported_codes = self._supported_codes()
        fallback = self._build_payload(
            rates={code: FALLBACK_RATES_PER_USD[code] for code in supported_codes},
            updated_at=now,
            source="fallback",
            is_fallback=True,
        )

        try:
            async with httpx.AsyncClient(timeout=settings.CURRENCY_RATES_TIMEOUT) as client:
                response = await client.get(settings.CURRENCY_RATES_URL)
                response.raise_for_status()
                data = response.json()
        except Exception as exc:
            logger.warning(f"Currency rate fetch failed, using fallback rates: {exc}")
            return fallback

        raw_rates = data.get("rates") if isinstance(data, dict) else None
        if not isinstance(raw_rates, dict):
            return fallback

        rates: dict[str, float] = {}
        for code in supported_codes:
            value = raw_rates.get(code)
            if isinstance(value, (int, float)) and value > 0:
                rates[code] = float(value)

        if "USD" not in rates:
            rates["USD"] = 1.0
        if len(rates) < 2:
            return fallback

        for code in supported_codes:
            rates.setdefault(code, FALLBACK_RATES_PER_USD[code])

        updated_at = self._parse_updated_at(data, now)
        return self._build_payload(
            rates=rates,
            updated_at=updated_at,
            source=settings.CURRENCY_RATES_URL,
            is_fallback=False,
        )

    def _supported_codes(self) -> list[str]:
        seen: set[str] = set()
        codes: list[str] = []
        for raw_code in settings.DISPLAY_CURRENCIES:
            code = str(raw_code).upper()
            if code in seen or code not in FALLBACK_RATES_PER_USD:
                continue
            seen.add(code)
            codes.append(code)
        return codes or ["USD", "CNY"]

    def _build_payload(
        self,
        *,
        rates: dict[str, float],
        updated_at: datetime,
        source: str,
        is_fallback: bool,
    ) -> CurrencyRatesResponse:
        supported = []
        for code in self._supported_codes():
            meta = DISPLAY_CURRENCY_META[code]
            supported.append({"code": code, **meta})

        return CurrencyRatesResponse.model_validate({
            "base": "USD",
            "rates": {code: rates[code] for code in self._supported_codes()},
            "supported": supported,
            "updated_at": updated_at.isoformat(),
            "source": source,
            "is_fallback": is_fallback,
        })

    @staticmethod
    def _parse_updated_at(data: dict[str, Any], fallback: datetime) -> datetime:
        unix_time = data.get("time_last_update_unix")
        if isinstance(unix_time, (int, float)) and unix_time > 0:
            return datetime.fromtimestamp(float(unix_time), tz=timezone.utc)
        date_text = data.get("date")
        if isinstance(date_text, str):
            try:
                return datetime.fromisoformat(date_text).replace(tzinfo=timezone.utc)
            except ValueError:
                pass
        return fallback
