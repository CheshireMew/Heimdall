import pytest

from app.services.market.query_app_service import MarketQueryAppService


class FakeMarketDataService:
    def __init__(self) -> None:
        self.calls = []

    def get_history_data(self, symbol, timeframe, end_ts, limit):
        self.calls.append(
            {
                "symbol": symbol,
                "timeframe": timeframe,
                "end_ts": end_ts,
                "limit": limit,
            }
        )
        return [[1717000000000, 1.0, 2.0, 0.5, 456.0, 1000.0]]


class FakeRealtimeService:
    pass


@pytest.mark.asyncio
async def test_live_tail_reads_cached_history_without_exchange_fetch():
    market_data_service = FakeMarketDataService()
    service = MarketQueryAppService(
        market_data_service=market_data_service,
        realtime_service=FakeRealtimeService(),
    )

    response = (await service.get_live_kline_tail(symbol="BTC/USDT", timeframe="1h", limit=16)).model_dump()

    assert response["current_price"] == 456.0
    assert len(market_data_service.calls) == 1
    assert market_data_service.calls[0]["symbol"] == "BTC/USDT"
    assert market_data_service.calls[0]["timeframe"] == "1h"
    assert market_data_service.calls[0]["limit"] == 16
    assert isinstance(market_data_service.calls[0]["end_ts"], int)
