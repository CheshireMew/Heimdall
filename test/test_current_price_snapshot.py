from __future__ import annotations

import pytest

from app.services.market.query_app_service import MarketQueryAppService


class FakeSnapshot:
    def __init__(self, prices: dict[str, float | None]) -> None:
        self.prices = prices

    async def get_current_price(self, symbol: str) -> float | None:
        return self.prices.get(symbol)


class FakeMarketDataService:
    def __init__(self) -> None:
        self.tail_calls: list[str] = []

    def get_recent_candles(self, symbol: str, timeframe: str, limit: int, **kwargs):
        self.tail_calls.append(symbol)
        return [[1717000000000, 1.0, 2.0, 0.5, 456.0, 1000.0]]


class FakeRealtime:
    pass


def make_service(snapshot: FakeSnapshot, market_data_service: FakeMarketDataService) -> MarketQueryAppService:
    service = MarketQueryAppService(
        market_data_service=market_data_service,
        realtime_service=FakeRealtime(),
        binance_snapshot_service=snapshot,
    )
    service.valid_symbols = ["BTC/USDT", "ETH/USDT"]
    service.valid_timeframes = ["1d"]
    return service


@pytest.mark.asyncio
async def test_current_price_prefers_websocket_snapshot():
    market_data_service = FakeMarketDataService()
    service = make_service(FakeSnapshot({"BTC/USDT": 123.0}), market_data_service)

    response = await service.get_current_price(
        symbol="BTC/USDT",
        timeframe="1d",
    )

    assert response.current_price == 123.0
    assert market_data_service.tail_calls == []


@pytest.mark.asyncio
async def test_current_price_falls_back_to_kline_tail():
    market_data_service = FakeMarketDataService()
    service = make_service(FakeSnapshot({"BTC/USDT": None}), market_data_service)

    response = await service.get_current_price(
        symbol="BTC/USDT",
        timeframe="1d",
    )

    assert response.current_price == 456.0
    assert market_data_service.tail_calls == ["BTC/USDT"]


@pytest.mark.asyncio
async def test_current_price_batch_uses_shared_snapshot_first_logic():
    market_data_service = FakeMarketDataService()
    service = make_service(FakeSnapshot({"BTC/USDT": 123.0, "ETH/USDT": None}), market_data_service)

    response = await service.get_current_price_batch(
        symbols=["BTC/USDT", "ETH/USDT", "BTC/USDT"],
        timeframe="1d",
    )

    assert [item.symbol for item in response.items] == ["BTC/USDT", "ETH/USDT"]
    assert response.items[0].current_price == 123.0
    assert response.items[0].source == "websocket_snapshot"
    assert response.items[1].current_price == 456.0
    assert response.items[1].source == "kline_tail"
    assert market_data_service.tail_calls == ["ETH/USDT"]
