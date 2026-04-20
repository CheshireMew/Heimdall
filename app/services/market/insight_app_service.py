from __future__ import annotations

from typing import Any, Callable

from app.domain.market.prompt_engine import PromptEngine
from app.domain.market.trade_setup import TradeSetupEngine, TradeSetupRequest
from app.schemas.market import CryptoIndexResponse, MarketIndicatorResponse, TradeSetupResponse
from app.services.market.crypto_index_service import CryptoIndexService
from app.services.market.indicator_service import IndicatorService
from app.services.market.query_app_service import MarketQueryAppService
from app.services.executor import run_sync


class MarketInsightAppService:
    def __init__(
        self,
        *,
        indicator_service: IndicatorService,
        crypto_index_service: CryptoIndexService,
        market_query_service: MarketQueryAppService,
        llm_client_factory: Callable[[], Any | None] | None = None,
    ) -> None:
        self.indicator_service = indicator_service
        self.crypto_index_service = crypto_index_service
        self.market_query_service = market_query_service
        self.llm_client_factory = llm_client_factory or (lambda: None)
        self.trade_setup_engine = TradeSetupEngine()

    def get_indicators(
        self,
        category: str | None,
        days: int,
    ) -> list[MarketIndicatorResponse]:
        return self.indicator_service.get_indicators(category=category, days=days)

    async def get_indicators_async(
        self,
        category: str | None,
        days: int,
    ) -> list[MarketIndicatorResponse]:
        return await run_sync(lambda: self.get_indicators(category=category, days=days))

    async def get_crypto_index(self, top_n: int, days: int) -> CryptoIndexResponse:
        return CryptoIndexResponse.model_validate(
            await self.crypto_index_service.build_index(top_n=top_n, days=days)
        )

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
            return TradeSetupResponse.model_validate(
                self.trade_setup_engine.build_rules(
                    request,
                    kline_data,
                    indicators.model_dump(),
                )
            )

        llm_client = self.llm_client_factory()
        if not llm_client:
            return TradeSetupResponse.model_validate(
                self.trade_setup_engine.build_ai(request, kline_data, None)
            )
        prompt = PromptEngine.build_trade_setup_prompt(
            symbol,
            timeframe,
            kline_data,
            indicators.model_dump(),
            account_size,
            style,
            strategy,
        )
        ai_payload = await llm_client.analyze(prompt)
        return TradeSetupResponse.model_validate(
            self.trade_setup_engine.build_ai(request, kline_data, ai_payload)
        )
