from __future__ import annotations

import sys
import types
from datetime import datetime, timezone

import pandas as pd

from app.domain.market.constants import KLINE_SYMBOL_MAX_LENGTH
from app.domain.market.index_catalog import INDEX_CATALOG, get_index_instrument, get_supported_index_symbols
from app.services.market.index_data_service import IndexDataService
from config import settings


class FakeKlineStore:
    def __init__(self, cached: list[list[float]] | None = None) -> None:
        self.cached = list(cached or [])
        self.saved: list[tuple[str, str, list[list[float]]]] = []

    def get_range(self, symbol: str, timeframe: str, start_ts: int, end_ts: int) -> list[list[float]]:
        return [
            row
            for row in self.cached
            if start_ts <= row[0] <= end_ts
        ]

    def save(self, symbol: str, timeframe: str, klines: list[list[float]]) -> None:
        self.saved.append((symbol, timeframe, klines))


class FakeResponse:
    def __init__(self, payload=None, text: str = "") -> None:
        self._payload = payload
        self.text = text

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self._payload


def test_index_catalog_contains_core_us_cn_hk_indexes():
    assert get_supported_index_symbols() == [
        "US_SP500",
        "US_NASDAQ_COMP",
        "US_NASDAQ100",
        "US_DOW",
        "US_RUSSELL2000",
        "US_VIX",
        "CN_CSI300",
        "CN_CSI_A500",
        "CN_SSE50",
        "CN_CSI500",
        "CN_CSI1000",
        "CN_SSE_COMP",
        "CN_SZSE_COMPONENT",
        "CN_CHINEXT",
        "CN_STAR50",
        "HK_HSI",
        "HK_HSTECH",
        "HK_HSCEI",
    ]

    assert get_index_instrument("CN_CSI300").eastmoney_secid == "1.000300"
    assert get_index_instrument("CN_CSI300").sohu_code == "zs_000300"
    assert get_index_instrument("CN_CSI300").baostock_code == "sh.000300"
    assert get_index_instrument("CN_CSI_A500").sina_cn_symbol == "sh000510"
    assert get_index_instrument("CN_CSI_A500").pricing_symbol == "sh560610"
    assert "恒生" in get_index_instrument("HK_HSI").aliases
    assert get_index_instrument("HK_HSI").sina_hk_symbol == "HSI"
    assert get_index_instrument("HK_HSI").pricing_symbol == "02800"
    assert "标普500" in get_index_instrument("US_SP500").aliases
    assert get_index_instrument("US_SP500").eastmoney_secid == "100.SPX"
    assert get_index_instrument("US_NASDAQ100").sina_us_symbol == ".NDX"
    assert get_index_instrument("US_NASDAQ100").pricing_symbol == "QQQ"
    assert get_index_instrument("HK_HSTECH").eastmoney_secid == "124.HSTECH"


def test_index_storage_symbols_fit_kline_cache_contract():
    storage_symbols: list[str] = []
    for instrument in INDEX_CATALOG.values():
        storage_symbols.append(instrument.storage_symbol)
        if instrument.pricing_storage_symbol:
            storage_symbols.append(instrument.pricing_storage_symbol)

    assert max(len(symbol) for symbol in storage_symbols) <= KLINE_SYMBOL_MAX_LENGTH


def test_eastmoney_history_is_normalized_and_cached(monkeypatch):
    service = IndexDataService(kline_store=FakeKlineStore())

    def fake_get(*args, **kwargs):
        return FakeResponse(
            payload={
                "data": {
                    "klines": [
                        "2024-01-02,1.0,2.0,3.0,0.5,100,1000",
                        "2024-01-03,2.0,2.5,2.8,1.8,120,1200",
                    ]
                }
            }
        )

    monkeypatch.setattr("app.services.market.index_data_service.requests.get", fake_get)

    result = service.get_history(
        symbol="CN_CSI300",
        timeframe="1d",
        start_date="2024-01-01",
        end_date="2024-01-10",
    )

    assert result["source"] == "eastmoney"
    assert result["is_close_only"] is False
    assert result["count"] == 2
    assert result["data"][0] == [
        int(datetime(2024, 1, 2, tzinfo=timezone.utc).timestamp() * 1000),
        1.0,
        3.0,
        0.5,
        2.0,
        100.0,
    ]
    assert service.kline_store.saved[0][0] == "index:CN:CSI300"


def test_sina_hk_history_is_normalized_and_cached(monkeypatch):
    service = IndexDataService(kline_store=FakeKlineStore())

    fake_akshare = types.SimpleNamespace(
        stock_hk_index_daily_sina=lambda symbol: pd.DataFrame([
            {"date": "2024-01-01", "open": 10, "high": 12, "low": 9, "close": 11, "volume": 1000},
            {"date": "2024-01-02", "open": 11, "high": 13, "low": 10, "close": 12, "volume": 1100},
        ])
    )
    monkeypatch.setitem(sys.modules, "akshare", fake_akshare)

    result = service.get_history(
        symbol="HK_HSI",
        timeframe="1d",
        start_date="2024-01-01",
        end_date="2024-01-10",
    )

    assert result["source"] == "sina_hk"
    assert result["is_close_only"] is False
    assert result["count"] == 2
    assert result["data"][0] == [
        int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp() * 1000),
        10.0,
        12.0,
        9.0,
        11.0,
        1000.0,
    ]
    assert service.kline_store.saved[0][0] == "index:HK:HSI"


def test_sina_cn_history_is_normalized_and_cached(monkeypatch):
    service = IndexDataService(kline_store=FakeKlineStore())

    fake_akshare = types.SimpleNamespace(
        stock_zh_index_daily=lambda symbol: pd.DataFrame([
            {"date": "2025-01-02", "open": 20, "high": 23, "low": 19, "close": 22, "volume": 2000},
            {"date": "2025-01-03", "open": 22, "high": 24, "low": 21, "close": 23, "volume": 2100},
        ])
    )
    monkeypatch.setitem(sys.modules, "akshare", fake_akshare)

    result = service.get_history(
        symbol="CN_CSI_A500",
        timeframe="1d",
        start_date="2025-01-01",
        end_date="2025-01-10",
    )

    assert result["source"] == "sina_cn"
    assert result["is_close_only"] is False
    assert result["count"] == 2
    assert result["data"][0] == [
        int(datetime(2025, 1, 2, tzinfo=timezone.utc).timestamp() * 1000),
        20.0,
        23.0,
        19.0,
        22.0,
        2000.0,
    ]
    assert service.kline_store.saved[0][0] == "index:CN:CSI_A500"


def test_sina_us_history_is_normalized_and_cached(monkeypatch):
    service = IndexDataService(kline_store=FakeKlineStore())

    fake_akshare = types.SimpleNamespace(
        index_us_stock_sina=lambda symbol: pd.DataFrame([
            {"date": "2024-01-02", "open": 30, "high": 33, "low": 29, "close": 32, "volume": 3000},
            {"date": "2024-01-03", "open": 32, "high": 34, "low": 31, "close": 33, "volume": 3100},
        ])
    )
    monkeypatch.setitem(sys.modules, "akshare", fake_akshare)

    result = service.get_history(
        symbol="US_NASDAQ100",
        timeframe="1d",
        start_date="2024-01-01",
        end_date="2024-01-10",
    )

    assert result["source"] == "sina_us"
    assert result["is_close_only"] is False
    assert result["count"] == 2
    assert result["data"][0] == [
        int(datetime(2024, 1, 2, tzinfo=timezone.utc).timestamp() * 1000),
        30.0,
        33.0,
        29.0,
        32.0,
        3000.0,
    ]
    assert service.kline_store.saved[0][0] == "index:US:NASDAQ100"


def test_pricing_history_uses_proxy_etf_source(monkeypatch):
    service = IndexDataService(kline_store=FakeKlineStore())

    fake_akshare = types.SimpleNamespace(
        stock_hk_daily=lambda symbol, adjust='': pd.DataFrame([
            {"date": "2024-01-02", "open": 20, "high": 21, "low": 19, "close": 20.5, "volume": 2000},
            {"date": "2024-01-03", "open": 20.5, "high": 21.5, "low": 20.1, "close": 21.0, "volume": 2100},
        ])
    )
    monkeypatch.setitem(sys.modules, "akshare", fake_akshare)
    monkeypatch.setattr(service, "_fetch_usd_fx_rates", lambda *args, **kwargs: {
        "2024-01-02": 0.128,
        "2024-01-03": 0.129,
    })

    result = service.get_pricing_history(
        symbol="HK_HSI",
        timeframe="1d",
        start_date="2024-01-01",
        end_date="2024-01-10",
    )

    assert result["price_basis"] == "proxy_etf"
    assert result["source"] == "sina_hk_etf:usd"
    assert result["pricing_symbol"] == "02800"
    assert result["pricing_currency"] == "USD"
    assert result["native_currency"] == "HKD"
    assert result["count"] == 2
    assert result["data"][0] == [
        int(datetime(2024, 1, 2, tzinfo=timezone.utc).timestamp() * 1000),
        2.56,
        2.688,
        2.432,
        2.624,
        2000.0,
    ]
    assert service.kline_store.saved[0][0] == "proxy:HK:HSI:02800"


def test_fred_history_close_only_is_not_cached(monkeypatch):
    service = IndexDataService(kline_store=FakeKlineStore())
    instrument = get_index_instrument("US_VIX")
    monkeypatch.setattr(settings, "FRED_API_KEY", "")

    def fake_get(*args, **kwargs):
        return FakeResponse(text="observation_date,VIXCLS\n2024-01-02,13.20\n2024-01-03,.\n")

    monkeypatch.setattr("app.services.market.index_data_service.requests.get", fake_get)

    result = service._fetch_fred_history(
        instrument,
        datetime(2024, 1, 1, tzinfo=timezone.utc),
        datetime(2024, 1, 10, tzinfo=timezone.utc),
    )

    assert result.source == "fred"
    assert result.is_close_only is True
    assert result.data == [
        [
            int(datetime(2024, 1, 2, tzinfo=timezone.utc).timestamp() * 1000),
            13.2,
            13.2,
            13.2,
            13.2,
            0.0,
        ]
    ]


def test_cached_history_is_used_before_upstream_fetch(monkeypatch):
    cached_rows = [
        [
            int(datetime(2024, 1, 2, tzinfo=timezone.utc).timestamp() * 1000),
            1.0,
            2.0,
            0.5,
            1.5,
            100.0,
        ],
        [
            int(datetime(2024, 1, 3, tzinfo=timezone.utc).timestamp() * 1000),
            1.5,
            2.2,
            1.2,
            2.0,
            120.0,
        ],
    ]
    service = IndexDataService(kline_store=FakeKlineStore(cached=cached_rows))

    def fail_fetch(*args, **kwargs):
        raise AssertionError("should not fetch upstream when cache already covers the range")

    monkeypatch.setattr(service, "_fetch_history", fail_fetch)

    result = service.get_history(
        symbol="CN_CSI300",
        timeframe="1d",
        start_date="2024-01-02",
        end_date="2024-01-03",
    )

    assert result["source"] == "cache"
    assert result["is_close_only"] is False
    assert result["count"] == 2
    assert result["data"] == cached_rows
