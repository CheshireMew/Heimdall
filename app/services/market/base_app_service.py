from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Callable, Literal

from app.domain.market.constants import Timeframe
from app.domain.market.prompt_engine import PromptEngine
from app.domain.market.symbol_catalog import get_supported_crypto_symbols
from app.domain.market.trade_setup import TradeSetupEngine, TradeSetupRequest
from app.infra.llm_client import LLMClient
from app.services.market.crypto_index_service import CryptoIndexService
from app.services.market.funding_rate_service import FundingRateService
from app.services.market.history_service import HistoryService
from app.services.market.indicator_service import IndicatorService
from app.services.market.market_data_service import MarketDataService
from app.services.market.realtime_service import RealtimeService
from config import settings
from utils.logger import logger


class BaseMarketAppService:
    def __init__(
        self,
        realtime_service: RealtimeService,
        indicator_service: IndicatorService,
        history_service: HistoryService,
        funding_rate_service: FundingRateService,
        crypto_index_service: CryptoIndexService,
    ) -> None:
        self.realtime_service = realtime_service
        self.indicator_service = indicator_service
        self.history_service = history_service
        self.funding_rate_service = funding_rate_service
        self.crypto_index_service = crypto_index_service
        self.trade_setup_engine = TradeSetupEngine()
        self.valid_symbols = get_supported_crypto_symbols()
        self.valid_timeframes = [item.value for item in Timeframe]

    @staticmethod
    def get_llm_client() -> LLMClient | None:
        return LLMClient()

    def validate_market_request(self, symbol: str, timeframe: str) -> None:
        if symbol not in self.valid_symbols:
            raise ValueError(f"无效交易对。可选: {self.valid_symbols}")
        if timeframe not in self.valid_timeframes:
            raise ValueError(f"无效时间周期。可选: {self.valid_timeframes}")

    async def _run_in_thread(self, action: Callable[[], Any]) -> Any:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, action)

    async def _compute_snapshot(
        self,
        *,
        market_data_service: MarketDataService,
        symbol: str,
        timeframe: str,
        limit: int,
        atr_period: int | None = None,
        volatility_period: int | None = None,
    ) -> tuple[list[list[float]], dict[str, Any]]:
        self.validate_market_request(symbol, timeframe)
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
        kline_data, indicators = await self._compute_snapshot(
            market_data_service=market_data_service,
            symbol=symbol,
            timeframe=resolved_timeframe,
            limit=resolved_limit,
        )

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
        kline_data, indicators = await self._compute_snapshot(
            market_data_service=market_data_service,
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )

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

    def get_recent_klines(
        self,
        *,
        market_data_service: MarketDataService,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> list[list[float]]:
        self.validate_market_request(symbol, timeframe)
        return self.history_service.get_recent_klines(market_data_service, symbol, timeframe, limit)

    async def get_live_kline_tail(
        self,
        *,
        market_data_service: MarketDataService,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> dict[str, Any]:
        self.validate_market_request(symbol, timeframe)
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
        self.validate_market_request(symbol, timeframe)
        kline_data = await self._run_in_thread(
            lambda: self.history_service.get_live_tail(
                market_data_service,
                symbol,
                timeframe,
                1,
            )
        )
        current_price = kline_data[-1][4] if kline_data else None
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "timestamp": datetime.now().isoformat(),
            "current_price": current_price,
        }

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
        self.validate_market_request(symbol, timeframe)
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
            self.validate_market_request(symbol, timeframe)
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

    def get_indicators(self, category: str | None, days: int) -> list[dict[str, Any]]:
        return self.indicator_service.get_indicators(category=category, days=days)

    async def get_crypto_index(self, top_n: int, days: int) -> dict[str, Any]:
        return await self.crypto_index_service.build_index(top_n=top_n, days=days)

    async def get_current_funding_rate(self, symbol: str) -> dict[str, Any]:
        return await self._run_in_thread(lambda: self.funding_rate_service.fetch_current_rate(symbol))

    async def sync_funding_rate_history(
        self,
        *,
        symbol: str,
        start_date: str | None,
        end_date: str | None,
    ) -> dict[str, Any]:
        return await self._run_in_thread(
            lambda: self.funding_rate_service.sync_history(
                symbol,
                start_date=start_date,
                end_date=end_date,
            )
        )

    async def get_funding_rate_history(
        self,
        *,
        symbol: str,
        start_date: str | None,
        end_date: str | None,
        limit: int | None,
    ) -> dict[str, Any]:
        return await self._run_in_thread(
            lambda: self.funding_rate_service.get_history(
                symbol,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
            )
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
        kline_data, indicators = await self._compute_snapshot(
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

    async def get_trade_setup(
        self,
        *,
        market_data_service: MarketDataService,
        symbol: str,
        timeframe: str,
        limit: int,
        account_size: float,
        style: str,
        strategy: str,
        mode: str,
    ) -> dict[str, Any]:
        if mode not in {"rules", "ai"}:
            raise ValueError("无效判断方式。可选: rules, ai")

        kline_data, indicators = await self._compute_snapshot(
            market_data_service=market_data_service,
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )
        request = TradeSetupRequest(
            symbol=symbol,
            timeframe=timeframe,
            account_size=account_size,
            style=style,
            strategy=strategy,
            mode=mode,
        )
        if mode == "rules":
            return self.trade_setup_engine.build_rules(request, kline_data, indicators)

        llm_client = self.get_llm_client()
        if not llm_client:
            return self.trade_setup_engine.build_ai(request, kline_data, None)
        prompt = PromptEngine.build_trade_setup_prompt(
            symbol,
            timeframe,
            kline_data,
            indicators,
            account_size,
            style,
            strategy,
        )
        ai_payload = await llm_client.analyze(prompt)
        return self.trade_setup_engine.build_ai(request, kline_data, ai_payload)
