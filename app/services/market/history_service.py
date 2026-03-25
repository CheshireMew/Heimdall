from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Callable

from app.services.market.market_data_service import MarketDataService


class HistoryService:
    def get_history(
        self,
        market_data_service: MarketDataService,
        symbol: str,
        timeframe: str,
        end_ts: int,
        limit: int,
    ) -> list[list[float]]:
        return market_data_service.get_history_data(symbol, timeframe, end_ts, limit)

    async def get_full_history(
        self,
        market_data_service: MarketDataService,
        symbol: str,
        timeframe: str,
        start_date: str,
        persist_klines: Callable[[str, str, list[list[float]]], None] | None = None,
    ) -> list[list[float]]:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            start_dt = datetime(2010, 1, 1)

        end_dt = datetime.now()
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            lambda: market_data_service.fetch_ohlcv_range(
                symbol,
                timeframe,
                start_dt,
                end_dt,
                persist_klines=persist_klines,
            ),
        )
