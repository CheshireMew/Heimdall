from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Callable, Literal

from app.infra.llm_client import LLMClient
from app.services.market.app_service_support import (
    VALID_MARKET_SYMBOLS,
    VALID_MARKET_TIMEFRAMES,
    build_llm_client,
    validate_market_request,
)
from app.services.market.history_service import HistoryService
from app.services.market.market_data_service import MarketDataService
from app.services.market.realtime_service import RealtimeService
from config import settings
from utils.logger import logger


class MarketQueryAppService:
    def __init__(
        self,
        *,
        realtime_service: RealtimeService,
        history_service: HistoryService,
        binance_snapshot_service=None,
        llm_client_factory: Callable[[], LLMClient | None] = build_llm_client,
    ) -> None:
        self.realtime_service = realtime_service
        self.history_service = history_service
        self.binance_snapshot_service = binance_snapshot_service
        self.llm_client_factory = llm_client_factory
        self.valid_symbols = list(VALID_MARKET_SYMBOLS)
        self.valid_timeframes = list(VALID_MARKET_TIMEFRAMES)

    async def _run_in_thread(self, action: Callable[[], Any]) -> Any:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, action)

    async def load_snapshot(
        self,
        *,
        market_data_service: MarketDataService,
        symbol: str,
        timeframe: str,
        limit: int,
        atr_period: int | None = None,
        volatility_period: int | None = None,
    ) -> tuple[list[list[float]], dict[str, Any]]:
        validate_market_request(symbol, timeframe)
        result = await self._run_in_thread(
            lambda: self.realtime_service.compute_market_snapshot(
                market_data_service,
                symbol,
                timeframe,
                limit,
                atr_period=atr_period,
                volatility_period=volatility_period,
            )
        )
        if not result:
            raise RuntimeError("获取数据失败")
        return result

    async def get_realtime(
        self,
        *,
        market_data_service: MarketDataService,
        symbol: str,
        timeframe: str | None,
        limit: int | None,
    ) -> dict[str, Any]:
        resolved_timeframe = timeframe or settings.TIMEFRAME
        resolved_limit = limit or settings.LIMIT
        kline_data, indicators = await self.load_snapshot(
            market_data_service=market_data_service,
            symbol=symbol,
            timeframe=resolved_timeframe,
            limit=resolved_limit,
        )

        ai_analysis = None
        llm_client = self.llm_client_factory()
        if llm_client:
            try:
                ai_analysis = await self.realtime_service.maybe_run_ai(llm_client, symbol, kline_data, indicators)
            except Exception as exc:
                logger.warning(f"AI 分析失败: {exc}")
        return self.realtime_service.build_response_payload(
            symbol,
            resolved_timeframe,
            kline_data,
            indicators,
            ai_analysis=ai_analysis,
        )

    async def get_realtime_ws_payload(
        self,
        *,
        market_data_service: MarketDataService,
        symbol: str,
        timeframe: str,
        limit: int,
        use_ai: bool,
    ) -> dict[str, Any] | None:
        kline_data, indicators = await self.load_snapshot(
            market_data_service=market_data_service,
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )

        ai_analysis = None
        if use_ai:
            llm_client = self.llm_client_factory()
            if llm_client:
                try:
                    ai_analysis = await self.realtime_service.maybe_run_ai(llm_client, symbol, kline_data, indicators)
                except Exception as exc:
                    logger.warning(f"WS AI 分析失败: {exc}")
        return self.realtime_service.build_response_payload(
            symbol,
            timeframe,
            kline_data,
            indicators,
            ai_analysis=ai_analysis,
            include_type=True,
        )

    def get_history(
        self,
        *,
        market_data_service: MarketDataService,
        symbol: str,
        timeframe: str,
        end_ts: int,
        limit: int,
    ) -> list[list[float]]:
        validate_market_request(symbol, timeframe)
        return self.history_service.get_history(market_data_service, symbol, timeframe, end_ts, limit)

    def get_recent_klines(
        self,
        *,
        market_data_service: MarketDataService,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> list[list[float]]:
        validate_market_request(symbol, timeframe)
        return self.history_service.get_recent_klines(market_data_service, symbol, timeframe, limit)

    async def get_live_kline_tail(
        self,
        *,
        market_data_service: MarketDataService,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> dict[str, Any]:
        validate_market_request(symbol, timeframe)
        kline_data = await self._run_in_thread(
            lambda: self.history_service.get_live_tail(
                market_data_service,
                symbol,
                timeframe,
                limit,
            )
        )
        current_price = kline_data[-1][4] if kline_data else None
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "timestamp": datetime.now().isoformat(),
            "current_price": current_price,
            "kline_data": kline_data,
        }

    async def get_current_price(
        self,
        *,
        market_data_service: MarketDataService,
        symbol: str,
        timeframe: str,
    ) -> dict[str, Any]:
        validate_market_request(symbol, timeframe)
        current_price = await self._get_current_price_from_snapshot(symbol)
        if current_price is None:
            current_price = await self._get_current_price_from_kline_tail(
                market_data_service=market_data_service,
                symbol=symbol,
                timeframe=timeframe,
            )
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "timestamp": datetime.now().isoformat(),
            "current_price": current_price,
        }

    async def get_current_price_batch(
        self,
        *,
        market_data_service: MarketDataService,
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

        items: list[dict[str, Any]] = []
        for symbol in normalized_symbols:
            current_price = await self._get_current_price_from_snapshot(symbol)
            source = "websocket_snapshot" if current_price is not None else "kline_tail"
            if current_price is None:
                current_price = await self._get_current_price_from_kline_tail(
                    market_data_service=market_data_service,
                    symbol=symbol,
                    timeframe=timeframe,
                )
            items.append(
                {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "timestamp": datetime.now().isoformat(),
                    "current_price": current_price,
                    "source": source if current_price is not None else "unavailable",
                }
            )
        return {
            "timeframe": timeframe,
            "items": items,
        }

    async def _get_current_price_from_snapshot(self, symbol: str) -> float | None:
        if self.binance_snapshot_service is None:
            return None
        return await self.binance_snapshot_service.get_current_price(symbol)

    async def _get_current_price_from_kline_tail(
        self,
        *,
        market_data_service: MarketDataService,
        symbol: str,
        timeframe: str,
    ) -> float | None:
        kline_data = await self._run_in_thread(
            lambda: self.history_service.get_live_tail(
                market_data_service,
                symbol,
                timeframe,
                1,
            )
        )
        return kline_data[-1][4] if kline_data else None

    async def get_full_history(
        self,
        *,
        market_data_service: MarketDataService,
        symbol: str,
        timeframe: str,
        start_date: str,
        fetch_policy: Literal["cache_only", "hydrate"] = "hydrate",
        persist_klines: Callable[[str, str, list[list[float]]], None] | None = None,
    ) -> list[list[float]]:
        validate_market_request(symbol, timeframe)
        return await self.history_service.get_full_history(
            market_data_service=market_data_service,
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            fetch_policy=fetch_policy,
            persist_klines=persist_klines,
        )

    async def get_full_history_batch(
        self,
        *,
        market_data_service: MarketDataService,
        symbols: list[str],
        timeframe: str,
        start_date: str,
        fetch_policy: Literal["cache_only", "hydrate"] = "hydrate",
        persist_klines: Callable[[str, str, list[list[float]]], None] | None = None,
    ) -> dict[str, list[list[float]]]:
        normalized_symbols: list[str] = []
        seen_symbols: set[str] = set()
        for symbol in symbols:
            validate_market_request(symbol, timeframe)
            if symbol in seen_symbols:
                continue
            seen_symbols.add(symbol)
            normalized_symbols.append(symbol)

        return await self.history_service.get_full_history_batch(
            market_data_service=market_data_service,
            symbols=normalized_symbols,
            timeframe=timeframe,
            start_date=start_date,
            fetch_policy=fetch_policy,
            persist_klines=persist_klines,
        )

    async def get_technical_metrics(
        self,
        *,
        market_data_service: MarketDataService,
        symbol: str,
        timeframe: str,
        limit: int,
        atr_period: int,
        volatility_period: int,
    ) -> dict[str, Any]:
        kline_data, indicators = await self.load_snapshot(
            market_data_service=market_data_service,
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            atr_period=atr_period,
            volatility_period=volatility_period,
        )
        current_price = kline_data[-1][4]
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "sample_size": len(kline_data),
            "current_price": current_price,
            "atr": indicators.get("atr"),
            "atr_pct": indicators.get("atr_pct") * 100.0 if indicators.get("atr_pct") is not None else None,
            "realized_volatility_pct": indicators.get("realized_volatility") * 100.0
            if indicators.get("realized_volatility") is not None
            else None,
            "annualized_volatility_pct": indicators.get("annualized_volatility") * 100.0
            if indicators.get("annualized_volatility") is not None
            else None,
        }
