from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Callable, Literal

from app.exceptions import ServiceUnavailableError
from app.schemas.market import (
    CurrentPriceBatchItemResponse,
    CurrentPriceBatchResponse,
    CurrentPriceResponse,
    KlineTailResponse,
    MarketHistoryBatchResponse,
    MarketHistoryResponse,
    RealtimeResponse,
    TechnicalMetricsResponse,
    build_market_history_batch_response,
    build_market_history_response,
    build_ohlcv_points,
)
from app.services.market.app_service_support import (
    VALID_MARKET_SYMBOLS,
    VALID_MARKET_TIMEFRAMES,
    validate_market_request,
)
from app.services.market.market_data_service import MarketDataService
from app.services.market.realtime_service import MarketSnapshot, RealtimeService
from app.services.executor import run_sync
from config import settings
from utils.logger import logger


class MarketQueryAppService:
    def __init__(
        self,
        *,
        market_data_service: MarketDataService,
        realtime_service: RealtimeService,
        binance_snapshot_service=None,
        llm_client_factory: Callable[[], Any | None] | None = None,
    ) -> None:
        self.market_data_service = market_data_service
        self.realtime_service = realtime_service
        self.binance_snapshot_service = binance_snapshot_service
        self.llm_client_factory = llm_client_factory or (lambda: None)
        self.valid_symbols = list(VALID_MARKET_SYMBOLS)
        self.valid_timeframes = list(VALID_MARKET_TIMEFRAMES)

    async def load_snapshot(
        self,
        *,
        symbol: str,
        timeframe: str,
        limit: int,
        atr_period: int | None = None,
        volatility_period: int | None = None,
    ) -> MarketSnapshot:
        validate_market_request(symbol, timeframe)
        result = await run_sync(
            lambda: self.realtime_service.compute_market_snapshot(
                self.market_data_service,
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
        symbol: str,
        timeframe: str | None,
        limit: int | None,
    ) -> RealtimeResponse:
        resolved_timeframe = timeframe or settings.TIMEFRAME
        resolved_limit = limit or settings.LIMIT
        try:
            snapshot = await self.load_snapshot(
                symbol=symbol,
                timeframe=resolved_timeframe,
                limit=resolved_limit,
            )
        except Exception as exc:
            err_str = str(exc).lower()
            if "network" in err_str or "connection" in err_str or "timeout" in err_str:
                logger.error(f"实时行情连接失败: {exc}")
                raise ServiceUnavailableError("无法连接到交易所 (Network Error)") from exc
            raise
        kline_data = snapshot.kline_data
        indicators = snapshot.indicators

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
        symbol: str,
        timeframe: str,
        limit: int,
        use_ai: bool,
    ) -> RealtimeResponse:
        snapshot = await self.load_snapshot(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )
        kline_data = snapshot.kline_data
        indicators = snapshot.indicators

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

    async def get_history(
        self,
        *,
        symbol: str,
        timeframe: str,
        end_ts: int,
        limit: int,
    ) -> MarketHistoryResponse:
        validate_market_request(symbol, timeframe)
        rows = await run_sync(
            lambda: self.market_data_service.get_history_data(symbol, timeframe, end_ts, limit)
        )
        return build_market_history_response(symbol=symbol, timeframe=timeframe, rows=rows)

    async def get_recent_klines(
        self,
        *,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> MarketHistoryResponse:
        validate_market_request(symbol, timeframe)
        rows = await run_sync(
            lambda: self.market_data_service.get_recent_candles(
                symbol,
                timeframe,
                limit,
                allow_cached_response=True,
            )
        )
        return build_market_history_response(symbol=symbol, timeframe=timeframe, rows=rows)

    async def get_live_kline_tail(
        self,
        *,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> KlineTailResponse:
        validate_market_request(symbol, timeframe)
        kline_data = await run_sync(
            lambda: self.market_data_service.get_recent_candles(
                symbol,
                timeframe,
                limit,
                allow_cached_response=False,
                live_max_retries=settings.EXCHANGE_TAIL_MAX_RETRIES,
            )
        )
        current_price = kline_data[-1][4] if kline_data else None
        return KlineTailResponse.model_validate(
            {
                "symbol": symbol,
                "timeframe": timeframe,
                "timestamp": datetime.now().isoformat(),
                "current_price": current_price,
                "kline_data": build_ohlcv_points(kline_data),
            }
        )

    async def get_current_price(
        self,
        *,
        symbol: str,
        timeframe: str,
    ) -> CurrentPriceResponse:
        validate_market_request(symbol, timeframe)
        current_price = await self._get_current_price_from_snapshot(symbol)
        if current_price is None:
            current_price = await self._get_current_price_from_kline_tail(
                symbol=symbol,
                timeframe=timeframe,
            )
        return CurrentPriceResponse(
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
    ) -> CurrentPriceBatchResponse:
        normalized_symbols: list[str] = []
        seen_symbols: set[str] = set()
        for symbol in symbols:
            validate_market_request(symbol, timeframe)
            if symbol in seen_symbols:
                continue
            seen_symbols.add(symbol)
            normalized_symbols.append(symbol)

        items: list[CurrentPriceBatchItemResponse] = []
        for symbol in normalized_symbols:
            current_price = await self._get_current_price_from_snapshot(symbol)
            source = "websocket_snapshot" if current_price is not None else "kline_tail"
            if current_price is None:
                current_price = await self._get_current_price_from_kline_tail(
                    symbol=symbol,
                    timeframe=timeframe,
                )
            items.append(
                CurrentPriceBatchItemResponse(
                    symbol=symbol,
                    timeframe=timeframe,
                    timestamp=datetime.now().isoformat(),
                    current_price=current_price,
                    source=source if current_price is not None else "unavailable",
                )
            )
        return CurrentPriceBatchResponse(timeframe=timeframe, items=items)

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

    async def get_full_history(
        self,
        *,
        symbol: str,
        timeframe: str,
        start_date: str,
        fetch_policy: Literal["cache_only", "hydrate"] = "hydrate",
        persist_klines: Callable[[str, str, list[list[float]]], None] | None = None,
    ) -> MarketHistoryResponse:
        validate_market_request(symbol, timeframe)
        rows = await self._load_full_history_rows(
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            fetch_policy=fetch_policy,
            persist_klines=persist_klines,
        )
        return build_market_history_response(symbol=symbol, timeframe=timeframe, rows=rows)

    async def get_full_history_batch(
        self,
        *,
        symbols: list[str],
        timeframe: str,
        start_date: str,
        fetch_policy: Literal["cache_only", "hydrate"] = "hydrate",
        persist_klines: Callable[[str, str, list[list[float]]], None] | None = None,
    ) -> MarketHistoryBatchResponse:
        normalized_symbols: list[str] = []
        seen_symbols: set[str] = set()
        for symbol in symbols:
            validate_market_request(symbol, timeframe)
            if symbol in seen_symbols:
                continue
            seen_symbols.add(symbol)
            normalized_symbols.append(symbol)

        rows = await asyncio.gather(
            *[
                self._load_full_history_rows(
                    symbol=symbol,
                    timeframe=timeframe,
                    start_date=start_date,
                    fetch_policy=fetch_policy,
                    persist_klines=persist_klines,
                )
                for symbol in normalized_symbols
            ],
        )
        return build_market_history_batch_response(
            timeframe=timeframe,
            series_by_symbol=dict(zip(normalized_symbols, rows, strict=False)),
        )

    async def _load_full_history_rows(
        self,
        *,
        symbol: str,
        timeframe: str,
        start_date: str,
        fetch_policy: Literal["cache_only", "hydrate"],
        persist_klines: Callable[[str, str, list[list[float]]], None] | None,
    ) -> list[list[float]]:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("start_date 必须是 YYYY-MM-DD") from exc

        end_dt = datetime.now()
        if fetch_policy == "cache_only":
            return await run_sync(
                lambda: self.market_data_service.get_cached_ohlcv_range(
                    symbol,
                    timeframe,
                    start_dt,
                    end_dt,
                ),
            )
        return await run_sync(
            lambda: self.market_data_service.fetch_ohlcv_range(
                symbol,
                timeframe,
                start_dt,
                end_dt,
                persist_klines=persist_klines,
            ),
        )

    async def get_technical_metrics(
        self,
        *,
        symbol: str,
        timeframe: str,
        limit: int,
        atr_period: int,
        volatility_period: int,
    ) -> TechnicalMetricsResponse:
        snapshot = await self.load_snapshot(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            atr_period=atr_period,
            volatility_period=volatility_period,
        )
        kline_data = snapshot.kline_data
        indicators = snapshot.indicators
        current_price = kline_data[-1][4]
        return TechnicalMetricsResponse(
            symbol=symbol,
            timeframe=timeframe,
            sample_size=len(kline_data),
            current_price=current_price,
            atr=indicators.atr,
            atr_pct=indicators.atr_pct,
            realized_volatility_pct=indicators.realized_volatility_pct,
            annualized_volatility_pct=indicators.annualized_volatility_pct,
        )
