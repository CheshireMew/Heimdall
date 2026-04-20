from __future__ import annotations

import pytest

from app.schemas.binance_market import BinanceKlineResponse, BinanceMarkPriceResponse, BinanceTickerStatsResponse
from app.services.market.binance_market_intel_service import BinanceMarketIntelService


def make_breakout_klines(start_price: float, bars: int = 80) -> list[dict]:
    rows: list[dict] = []
    price = start_price
    for index in range(bars):
        open_price = price
        change = 0.0038 if index % 6 else 0.0014
        close_price = open_price * (1.0 + change)
        high_price = close_price * 1.002
        low_price = open_price * 0.998
        rows.append(
            {
                "open_time": 1717000000000 + index * 900000,
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "volume": 1_000_000 + index * 1000,
                "close_time": 1717000000000 + (index + 1) * 900000 - 1,
            }
        )
        price = close_price
    return rows


@pytest.mark.asyncio
async def test_market_breakout_monitor_unifies_and_scores_candidates(monkeypatch):
    service = BinanceMarketIntelService()

    async def fake_spot_ticker_24hr(**kwargs):
        return BinanceTickerStatsResponse.model_validate({
            "exchange": "binance",
            "market": "spot",
            "items": [
                {"symbol": "DOGEUSDT", "last_price": 0.164, "price_change_pct": 8.6, "quote_volume": 310_000_000.0},
                {"symbol": "XRPUPUSDT", "last_price": 0.42, "price_change_pct": 18.0, "quote_volume": 60_000_000.0},
                {"symbol": "BTCFDUSD", "last_price": 68000.0, "price_change_pct": 5.5, "quote_volume": 200_000_000.0},
            ],
        })

    async def fake_usdm_ticker_24hr(**kwargs):
        return BinanceTickerStatsResponse.model_validate({
            "exchange": "binance",
            "market": "usdm",
            "items": [
                {"symbol": "SUIUSDT", "last_price": 1.82, "price_change_pct": 6.2, "quote_volume": 180_000_000.0},
                {"symbol": "BTCUSDT_260626", "last_price": 70200.0, "price_change_pct": 7.0, "quote_volume": 90_000_000.0},
            ],
        })

    async def fake_usdm_mark_price(**kwargs):
        return BinanceMarkPriceResponse.model_validate({
            "exchange": "binance",
            "market": "usdm",
            "items": [
                {"symbol": "SUIUSDT", "mark_price": 1.81, "last_funding_rate": 0.00012},
                {"symbol": "BTCUSDT_260626", "mark_price": 70180.0, "last_funding_rate": 0.00005},
            ],
        })

    async def fake_spot_klines(**kwargs):
        return BinanceKlineResponse.model_validate({"exchange": "binance", "market": "spot", "symbol": "DOGEUSDT", "interval": "15m", "items": make_breakout_klines(0.12)})

    async def fake_usdm_klines(**kwargs):
        return BinanceKlineResponse.model_validate({"exchange": "binance", "market": "usdm", "symbol": "SUIUSDT", "interval": "15m", "items": make_breakout_klines(1.35)})

    monkeypatch.setattr(service, "get_spot_ticker_24hr", fake_spot_ticker_24hr)
    monkeypatch.setattr(service, "get_usdm_ticker_24hr", fake_usdm_ticker_24hr)
    monkeypatch.setattr(service, "get_usdm_mark_price", fake_usdm_mark_price)
    monkeypatch.setattr(service, "get_spot_klines", fake_spot_klines)
    monkeypatch.setattr(service, "get_usdm_klines", fake_usdm_klines)

    response = (await service.get_market_breakout_monitor(min_rise_pct=5.0, limit=10, quote_asset="USDT")).model_dump()

    assert response["summary"]["monitored_count"] == 2
    assert response["summary"]["spot_count"] == 1
    assert response["summary"]["contract_count"] == 1

    symbols = {item["symbol"] for item in response["items"]}
    assert symbols == {"DOGEUSDT", "SUIUSDT"}

    spot_item = next(item for item in response["items"] if item["symbol"] == "DOGEUSDT")
    assert spot_item["structure_ok"] is True
    assert spot_item["momentum_ok"] is True
    assert spot_item["verdict"] == "优先关注"
    assert spot_item["follow_status"] in {"继续上行", "高位蓄势"}
    assert spot_item["reasons"]


@pytest.mark.asyncio
async def test_market_page_payload_returns_partial_data_when_a_source_fails(monkeypatch):
    service = BinanceMarketIntelService()

    async def fake_spot_ticker_24hr(**kwargs):
        return BinanceTickerStatsResponse.model_validate({
            "exchange": "binance",
            "market": "spot",
            "items": [
                {"symbol": "DOGEUSDT", "last_price": 0.164, "price_change_pct": 8.6, "quote_volume": 310_000_000.0},
            ],
        })

    async def fake_usdm_ticker_24hr(**kwargs):
        raise RuntimeError("upstream timeout")

    async def fake_usdm_mark_price(**kwargs):
        return BinanceMarkPriceResponse.model_validate({
            "exchange": "binance",
            "market": "usdm",
            "items": [],
        })

    async def fake_spot_klines(**kwargs):
        return BinanceKlineResponse.model_validate({"exchange": "binance", "market": "spot", "symbol": "DOGEUSDT", "interval": "15m", "items": make_breakout_klines(0.12)})

    monkeypatch.setattr(service, "get_spot_ticker_24hr", fake_spot_ticker_24hr)
    monkeypatch.setattr(service, "get_usdm_ticker_24hr", fake_usdm_ticker_24hr)
    monkeypatch.setattr(service, "get_usdm_mark_price", fake_usdm_mark_price)
    monkeypatch.setattr(service, "get_spot_klines", fake_spot_klines)

    response = (await service.get_market_page_payload(min_rise_pct=5.0, limit=24, quote_asset="USDT")).model_dump()

    assert response["load_errors"] == ["U本位24H"]
    assert response["spot_ticker"]["items"]
    assert response["usdm_ticker"]["items"] == []
    assert response["monitor"]["summary"]["monitored_count"] == 1
    assert {item["symbol"] for item in response["monitor"]["items"]} == {"DOGEUSDT"}
