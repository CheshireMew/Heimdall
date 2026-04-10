from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Callable

from app.services.market.market_data_service import MarketDataService


class HistoryService:
    def get_recent_klines(
        self,
        market_data_service: MarketDataService,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> list[list[float]]:
        return market_data_service.get_recent_candles(symbol, timeframe, limit)

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

    async def get_full_history_batch(
        self,
        market_data_service: MarketDataService,
        symbols: list[str],
        timeframe: str,
        start_date: str,
        persist_klines: Callable[[str, str, list[list[float]]], None] | None = None,
    ) -> dict[str, list[list[float]]]:
        results = await asyncio.gather(
            *[
                self.get_full_history(
                    market_data_service=market_data_service,
                    symbol=symbol,
                    timeframe=timeframe,
                    start_date=start_date,
                    persist_klines=persist_klines,
                )
                for symbol in symbols
            ],
        )
        return {
            symbol: data
            for symbol, data in zip(symbols, results, strict=False)
        }
