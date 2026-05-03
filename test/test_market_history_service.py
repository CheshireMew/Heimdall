import pytest

from app.services.market.query_app_service import MarketQueryAppService
from config import settings


class FakeMarketDataService:
    def __init__(self) -> None:
        self.calls = []

    def get_recent_candles(self, symbol, timeframe, limit, **kwargs):
        self.calls.append(
            {
                "symbol": symbol,
                "timeframe": timeframe,
                "limit": limit,
                **kwargs,
            }
        )
        return [[1717000000000, 1.0, 2.0, 0.5, 456.0, 1000.0]]


class FakeRealtimeService:
    pass


@pytest.mark.asyncio
async def test_live_tail_uses_bounded_exchange_retry_policy():
    market_data_service = FakeMarketDataService()
    service = MarketQueryAppService(
        market_data_service=market_data_service,
        realtime_service=FakeRealtimeService(),
    )

    response = await service.get_live_kline_tail(symbol="BTC/USDT", timeframe="1h", limit=16)

    assert response.current_price == 456.0
    assert market_data_service.calls == [
        {
            "symbol": "BTC/USDT",
            "timeframe": "1h",
            "limit": 16,
            "allow_cached_response": False,
            "live_max_retries": settings.EXCHANGE_TAIL_MAX_RETRIES,
        }
    ]
