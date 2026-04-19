from __future__ import annotations

from typing import Any, Callable

from app.domain.market.prompt_engine import PromptEngine
from app.domain.market.trade_setup import TradeSetupEngine, TradeSetupRequest
from app.services.market.crypto_index_service import CryptoIndexService
from app.services.market.indicator_service import IndicatorService
from app.services.market.market_data_service import MarketDataService
from app.services.market.query_app_service import MarketQueryAppService


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

    def get_indicators(self, category: str | None, days: int) -> list[dict]:
        return self.indicator_service.get_indicators(category=category, days=days)

    async def get_crypto_index(self, top_n: int, days: int) -> dict:
        return await self.crypto_index_service.build_index(top_n=top_n, days=days)

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
    ) -> dict:
        if mode not in {"rules", "ai"}:
            raise ValueError("无效判断方式。可选: rules, ai")

        kline_data, indicators = await self.market_query_service.load_snapshot(
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
