from __future__ import annotations

from datetime import datetime, timedelta

from app.services.market.market_data_service import MarketDataService
from config import settings


class FakeKlineStore:
    def __init__(self, cached_rows: list[list[float]]) -> None:
        self.cached_rows = list(cached_rows)
        self.saved_rows: list[list[float]] = []

    def get_range(self, symbol: str, timeframe: str, start_ts: int, end_ts: int) -> list[list[float]]:
        return [row for row in self.cached_rows if start_ts <= row[0] <= end_ts]

    def save(self, symbol: str, timeframe: str, klines: list[list[float]]) -> None:
        self.saved_rows.extend(klines)
        self.cached_rows.extend(klines)


class FakeExchangeGateway:
    exchange_id = "binance"
    max_task_seconds = 60

    def __init__(self, missing_rows: dict[int, list[float]]) -> None:
        self.missing_rows = missing_rows
        self.calls: list[tuple[str, str, int | None, int | None]] = []

    def fetch_ohlcv(self, symbol: str, timeframe: str, since: int | None = None, limit: int | None = None):
        self.calls.append((symbol, timeframe, since, limit))
        row = self.missing_rows.get(int(since or 0))
        return ([row] if row else [], 1)

    def sleep_for_rate_limit(self) -> None:
        return


def test_fetch_ohlcv_range_repairs_middle_gap():
    base = datetime(2024, 1, 1, 0, 0, 0)
    one_hour_ms = 60 * 60 * 1000
    base_ts = int(base.timestamp() * 1000)

    first_row = [base_ts, 1.0, 1.0, 1.0, 1.0, 10.0]
    missing_row = [base_ts + one_hour_ms, 2.0, 2.0, 2.0, 2.0, 20.0]
    third_row = [base_ts + (2 * one_hour_ms), 3.0, 3.0, 3.0, 3.0, 30.0]

    exchange_gateway = FakeExchangeGateway({missing_row[0]: missing_row})
    kline_store = FakeKlineStore([first_row, third_row])
    service = MarketDataService(
        exchange_gateway=exchange_gateway,
        kline_store=kline_store,
    )

    data = service.fetch_ohlcv_range(
        "BTC/USDT",
        "1h",
        base,
        base + timedelta(hours=2),
    )

    assert [row[0] for row in data] == [first_row[0], missing_row[0], third_row[0]]
    assert exchange_gateway.calls == [("BTC/USDT", "1h", missing_row[0], settings.EXCHANGE_FETCH_LIMIT)]
    assert kline_store.saved_rows == [missing_row]
