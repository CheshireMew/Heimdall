import pytest

from app.services.market.realtime_query_service import MarketRealtimeQueryService
from app.services.market.realtime_service import MarketSnapshot, RealtimeService


class RecordingRealtimeService:
    def __init__(self) -> None:
        self.calls = []

    def compute_market_snapshot(
        self,
        market_data_service,
        symbol,
        timeframe,
        limit,
    ):
        self.calls.append(
            {
                "market_data_service": market_data_service,
                "symbol": symbol,
                "timeframe": timeframe,
                "limit": limit,
            }
        )
        return MarketSnapshot(kline_data=[[1, 2, 3, 1, 2, 10]], indicators={})


class FakeMarketDataService:
    def get_recent_candles(self, symbol, timeframe, limit):
        return [
            [
                1710000000000 + index * 86_400_000,
                100.0 + index,
                103.0 + index,
                98.0 + index,
                101.0 + index,
                1000.0 + index,
            ]
            for index in range(limit)
        ]


@pytest.mark.asyncio
async def test_load_snapshot_delegates_request_without_indicator_period_overrides():
    realtime_service = RecordingRealtimeService()
    market_data_service = object()
    service = MarketRealtimeQueryService(
        market_data_service=market_data_service,
        realtime_service=realtime_service,
    )

    snapshot = await service.load_snapshot(symbol="BTC/USDT", timeframe="1d", limit=100)

    assert snapshot.kline_data
    assert realtime_service.calls == [
        {
            "market_data_service": market_data_service,
            "symbol": "BTC/USDT",
            "timeframe": "1d",
            "limit": 100,
        }
    ]


@pytest.mark.asyncio
async def test_get_realtime_uses_default_periods_with_real_snapshot_service():
    service = MarketRealtimeQueryService(
        market_data_service=FakeMarketDataService(),
        realtime_service=RealtimeService(),
    )

    response = (await service.get_realtime(symbol="BTC/USDT", timeframe="1d", limit=100)).model_dump()

    assert response["symbol"] == "BTC/USDT"
    assert response["timeframe"] == "1d"
    assert response["indicators"]["atr"] is not None
    assert response["indicators"]["realized_volatility_pct"] is not None
