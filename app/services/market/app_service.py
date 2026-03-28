from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import Any, Callable

from app.infra.llm_client import LLMClient
from app.services.market.crypto_index_app_service import CryptoIndexAppService
from app.services.market.funding_rate_service import FundingRateService
from app.services.market.history_service import HistoryService
from app.services.market.indicator_service import IndicatorService
from app.services.market.market_data_service import MarketDataService
from app.services.market.realtime_service import RealtimeService
from config import settings
from app.domain.market.constants import Timeframe
from utils.logger import logger


class MarketAppService:
    def __init__(
        self,
        crypto_index_service: CryptoIndexAppService,
        realtime_service: RealtimeService,
        indicator_service: IndicatorService,
        history_service: HistoryService,
        funding_rate_service: FundingRateService,
    ) -> None:
        self.crypto_index_service = crypto_index_service
        self.realtime_service = realtime_service
        self.indicator_service = indicator_service
        self.history_service = history_service
        self.funding_rate_service = funding_rate_service
        self.valid_symbols = settings.SYMBOLS
        self.valid_timeframes = [item.value for item in Timeframe]

    @lru_cache(maxsize=1)
    def get_llm_client(self) -> LLMClient | None:
        if not settings.DEEPSEEK_API_KEY or len(settings.DEEPSEEK_API_KEY) < 10:
            return None
        return LLMClient()

    def validate_market_request(self, symbol: str, timeframe: str) -> None:
        if symbol not in self.valid_symbols:
            raise ValueError(f"无效交易对。可选: {self.valid_symbols}")
        if timeframe not in self.valid_timeframes:
            raise ValueError(f"无效时间周期。可选: {self.valid_timeframes}")

    async def get_realtime(
        self,
        *,
        market_data_service: MarketDataService,
        symbol: str,
        timeframe: str | None,
        limit: int | None,
    ) -> dict[str, Any]:
        resolved_timeframe = timeframe or settings.TIMEFRAME
        self.validate_market_request(symbol, resolved_timeframe)
        resolved_limit = limit or settings.LIMIT

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.realtime_service.compute_market_snapshot(
                market_data_service,
                symbol,
                resolved_timeframe,
                resolved_limit,
            ),
        )
        if result is None:
            raise RuntimeError("获取数据失败")

        kline_data, indicators = result
        ai_analysis = None
        llm_client = self.get_llm_client()
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
        self.validate_market_request(symbol, timeframe)
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.realtime_service.compute_market_snapshot(
                market_data_service,
                symbol,
                timeframe,
                limit,
            ),
        )
        if not result:
            return None

        kline_data, indicators = result
        ai_analysis = None
        if use_ai:
            llm_client = self.get_llm_client()
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
        self.validate_market_request(symbol, timeframe)
        return self.history_service.get_history(market_data_service, symbol, timeframe, end_ts, limit)

    async def get_full_history(
        self,
        *,
        market_data_service: MarketDataService,
        symbol: str,
        timeframe: str,
        start_date: str,
        persist_klines: Callable[[str, str, list[list[float]]], None] | None = None,
    ) -> list[list[float]]:
        self.validate_market_request(symbol, timeframe)
        return await self.history_service.get_full_history(
            market_data_service=market_data_service,
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            persist_klines=persist_klines,
        )

    def get_indicators(self, category: str | None, days: int) -> list[dict[str, Any]]:
        return self.indicator_service.get_indicators(category=category, days=days)

    async def get_crypto_index(self, top_n: int, days: int) -> dict[str, Any]:
        return await self.crypto_index_service.get_index(top_n=top_n, days=days)

    async def get_current_funding_rate(self, symbol: str) -> dict[str, Any]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.funding_rate_service.fetch_current_rate(symbol),
        )

    async def sync_funding_rate_history(
        self,
        *,
        symbol: str,
        start_date: str | None,
        end_date: str | None,
    ) -> dict[str, Any]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.funding_rate_service.sync_history(
                symbol,
                start_date=start_date,
                end_date=end_date,
            ),
        )

    async def get_funding_rate_history(
        self,
        *,
        symbol: str,
        start_date: str | None,
        end_date: str | None,
        limit: int | None,
    ) -> dict[str, Any]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.funding_rate_service.get_history(
                symbol,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
            ),
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
        self.validate_market_request(symbol, timeframe)
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.realtime_service.compute_market_snapshot(
                market_data_service,
                symbol,
                timeframe,
                limit,
                atr_period=atr_period,
                volatility_period=volatility_period,
            ),
        )
        if not result:
            raise RuntimeError("获取数据失败")

        kline_data, indicators = result
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
