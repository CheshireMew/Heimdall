from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from app.infra.executor import run_sync
from app.services.market.app_service_support import validate_market_request
from app.services.market.market_data_service import MarketDataService
from app.services.market.query_payloads import current_price_response
from config import settings


class MarketPriceQueryService:
    def __init__(
        self,
        *,
        market_data_service: MarketDataService,
        binance_snapshot_service=None,
    ) -> None:
        self.market_data_service = market_data_service
        self.binance_snapshot_service = binance_snapshot_service

    async def get_current_price(
        self,
        *,
        symbol: str,
        timeframe: str,
    ) -> dict[str, Any]:
        validate_market_request(symbol, timeframe)
        current_price = await self._get_current_price_from_snapshot(symbol)
        if current_price is None:
            current_price = await self._get_current_price_from_kline_tail(
                symbol=symbol,
                timeframe=timeframe,
            )
        return current_price_response(
            symbol=symbol,
            timeframe=timeframe,
            timestamp=datetime.now().isoformat(),
            current_price=current_price,
        )

    async def get_current_price_batch(
        self,
        *,
        symbols: list[str],
        timeframe: str,
    ) -> dict[str, Any]:
        normalized_symbols: list[str] = []
        seen_symbols: set[str] = set()
        for symbol in symbols:
            validate_market_request(symbol, timeframe)
            if symbol in seen_symbols:
                continue
            seen_symbols.add(symbol)
            normalized_symbols.append(symbol)

        items = await asyncio.gather(
            *[
                self._build_current_price_batch_item(symbol=symbol, timeframe=timeframe)
                for symbol in normalized_symbols
            ],
        )
        return {"timeframe": timeframe, "items": items}

    async def _build_current_price_batch_item(
        self,
        *,
        symbol: str,
        timeframe: str,
    ) -> dict[str, Any]:
        current_price = await self._get_current_price_from_snapshot(symbol)
        source = "websocket_snapshot" if current_price is not None else "kline_tail"
        if current_price is None:
            current_price = await self._get_current_price_from_kline_tail(
                symbol=symbol,
                timeframe=timeframe,
            )
        return current_price_response(
            symbol=symbol,
            timeframe=timeframe,
            timestamp=datetime.now().isoformat(),
            current_price=current_price,
            source=source if current_price is not None else "unavailable",
        )

    async def _get_current_price_from_snapshot(self, symbol: str) -> float | None:
        if self.binance_snapshot_service is None:
            return None
        return await self.binance_snapshot_service.get_current_price(symbol)

    async def _get_current_price_from_kline_tail(
        self,
        *,
        symbol: str,
        timeframe: str,
    ) -> float | None:
        kline_data = await run_sync(
            lambda: self.market_data_service.get_recent_candles(
                symbol,
                timeframe,
                1,
                allow_cached_response=False,
                live_max_retries=settings.EXCHANGE_TAIL_MAX_RETRIES,
            )
        )
        return kline_data[-1][4] if kline_data else None
