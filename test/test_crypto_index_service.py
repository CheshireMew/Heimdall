from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.services.market.crypto_index_service import CryptoIndexService, ExchangeClose


def day_ms(year: int, month: int, day: int) -> int:
    return int(datetime(year, month, day, tzinfo=timezone.utc).timestamp() * 1000)


class FakeBinanceResponse:
    def __init__(self, payload, *, fail: bool = False) -> None:
        self.payload = payload
        self.fail = fail

    def raise_for_status(self) -> None:
        if self.fail:
            raise RuntimeError("upstream rejected symbol")

    def json(self):
        return self.payload


class FakeBinanceClient:
    def __init__(self) -> None:
        self.urls: list[str] = []

    async def get(self, url: str, **kwargs):
        self.urls.append(url)
        if "/api/v3/klines" in url:
            return FakeBinanceResponse([], fail=True)
        return FakeBinanceResponse([
            [day_ms(2026, 5, 11), "42", "43", "40", "41", "100", day_ms(2026, 5, 12)],
        ])


@pytest.mark.asyncio
async def test_binance_history_uses_usdm_when_spot_symbol_is_unavailable():
    service = CryptoIndexService(cache_service=None)
    client = FakeBinanceClient()

    rows = await service._get_binance_daily_closes(client, "HYPE", 1)

    assert ["/api/v3/klines" in url for url in client.urls] == [True, False]
    assert ["/fapi/v1/klines" in url for url in client.urls] == [False, True]
    assert rows == [ExchangeClose(day_ms(2026, 5, 11), 41.0)]


@pytest.mark.asyncio
async def test_crypto_index_uses_exchange_history_before_coingecko(monkeypatch):
    service = CryptoIndexService(cache_service=None)
    coins = [
        {
            "id": "bitcoin",
            "symbol": "BTC",
            "name": "Bitcoin",
            "price": 100.0,
            "market_cap": 1000.0,
            "market_cap_change_24h_pct": 10.0,
        },
        {
            "id": "okb",
            "symbol": "OKB",
            "name": "OKB",
            "price": 50.0,
            "market_cap": 500.0,
            "market_cap_change_24h_pct": 5.0,
        },
    ]
    binance_calls: list[str] = []
    okx_calls: list[str] = []

    async def fake_top_market_caps(top_n: int):
        return coins[:top_n]

    async def fake_binance_closes(client, symbol: str, days: int):
        binance_calls.append(symbol)
        return [
            ExchangeClose(day_ms(2026, 5, 10), 50.0),
            ExchangeClose(day_ms(2026, 5, 11), 100.0),
        ]

    async def fake_okx_closes(client, symbol: str, days: int):
        okx_calls.append(symbol)
        return [
            ExchangeClose(day_ms(2026, 5, 10), 25.0),
            ExchangeClose(day_ms(2026, 5, 11), 50.0),
        ]

    async def fail_coingecko_history(*args, **kwargs):
        raise AssertionError("CoinGecko market_chart should not be called for exchange-covered assets")

    monkeypatch.setattr(service, "get_top_market_caps", fake_top_market_caps)
    monkeypatch.setattr(service, "_get_binance_daily_closes", fake_binance_closes)
    monkeypatch.setattr(service, "_get_okx_daily_closes", fake_okx_closes)
    monkeypatch.setattr(service, "_get_json", fail_coingecko_history)

    result = await service.build_index(top_n=2, days=2, base_value=100.0)

    assert binance_calls == ["BTC"]
    assert okx_calls == ["OKB"]
    assert result["history"] == [
        {
            "date": "2026-05-10",
            "timestamp": 1778371200,
            "market_cap": 750.0,
            "index_value": 100.0,
        },
        {
            "date": "2026-05-11",
            "timestamp": 1778457600,
            "market_cap": 1500.0,
            "index_value": 200.0,
        },
    ]
    assert result["summary"]["methodology"] == "fixed-current-market-cap-weighted-exchange-price-history"


@pytest.mark.asyncio
async def test_crypto_index_falls_back_to_coingecko_when_exchange_history_is_unavailable(monkeypatch):
    service = CryptoIndexService(cache_service=None)
    coin = {
        "id": "ripple",
        "symbol": "XRP",
        "name": "XRP",
        "price": 2.0,
        "market_cap": 200.0,
        "market_cap_change_24h_pct": 1.0,
    }
    coingecko_paths: list[str] = []

    async def fake_top_market_caps(top_n: int):
        return [coin]

    async def empty_binance_closes(client, symbol: str, days: int):
        return []

    async def fake_coingecko_json(client, path: str, params, max_retries=None):
        coingecko_paths.append(path)
        return {"market_caps": [[day_ms(2026, 5, 11), 200.0]]}

    monkeypatch.setattr(service, "get_top_market_caps", fake_top_market_caps)
    monkeypatch.setattr(service, "_get_binance_daily_closes", empty_binance_closes)
    monkeypatch.setattr(service, "_get_json", fake_coingecko_json)

    result = await service.build_index(top_n=1, days=1, base_value=100.0)

    assert coingecko_paths == ["/coins/ripple/market_chart"]
    assert result["history"][0]["market_cap"] == 200.0
    assert result["summary"]["methodology"] == "fixed-current-market-cap-weighted-mixed-price-history"
