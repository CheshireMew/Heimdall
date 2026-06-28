from __future__ import annotations

from typing import Any, Callable

from app.contracts.dto.market import DliLiquidityResponse, MarketIndicatorResponse, TradeSetupResponse
from app.domain.market.prompt_engine import PromptEngine
from app.domain.market.trade_setup import TradeSetupEngine, TradeSetupRequest
from app.services.market.indicator_service import IndicatorService
from app.services.market.query_app_service import MarketQueryAppService
from app.infra.executor import run_database


class MarketInsightAppService:
    def __init__(
        self,
        *,
        indicator_service: IndicatorService,
        market_query_service: MarketQueryAppService,
        llm_client_factory: Callable[[], Any | None] | None = None,
    ) -> None:
        self.indicator_service = indicator_service
        self.market_query_service = market_query_service
        self.llm_client_factory = llm_client_factory or (lambda: None)
        self.trade_setup_engine = TradeSetupEngine()

    def get_indicators(
        self,
        category: str | None,
        days: int,
    ) -> list[MarketIndicatorResponse]:
        return self.indicator_service.get_indicators(category=category, days=days)

    def get_dli_liquidity(self, days: int, change_days: int = 30) -> DliLiquidityResponse:
        return self.indicator_service.get_dli_liquidity(days=days, change_days=change_days)

    async def get_indicators_async(
        self,
        category: str | None,
        days: int,
    ) -> list[MarketIndicatorResponse]:
        return await run_database(lambda: self.get_indicators(category=category, days=days))

    async def get_dli_liquidity_async(self, days: int, change_days: int = 30) -> DliLiquidityResponse:
        return await run_database(lambda: self.get_dli_liquidity(days=days, change_days=change_days))

    async def get_trade_setup(
        self,
        *,
        symbol: str,
        timeframe: str,
        limit: int,
        account_size: float,
        style: str,
        strategy: str,
        mode: str,
    ) -> TradeSetupResponse:
        if mode not in {"rules", "ai"}:
            raise ValueError("无效判断方式。可选: rules, ai")

        snapshot = await self.market_query_service.load_snapshot(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )
        kline_data = snapshot.kline_data
        indicators = snapshot.indicators
        request = TradeSetupRequest(
            symbol=symbol,
            timeframe=timeframe,
            account_size=account_size,
            style=style,
            strategy=strategy,
            mode=mode,
        )
        if mode == "rules":
            return self.trade_setup_engine.build_rules(
                request,
                kline_data,
                indicators,
            )

        llm_client = self.llm_client_factory()
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
