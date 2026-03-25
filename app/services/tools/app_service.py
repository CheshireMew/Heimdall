from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import datetime, timedelta
from typing import Any

from app.infra.cache import redis_service
from app.services.market.market_data_service import MarketDataService
from app.services.sentiment_service import SentimentService
from app.services.tools.contracts import ComparePairsCommand, SimulateDcaCommand
from app.services.tools.dca_service import DCAService
from app.services.tools.pair_compare_service import PairCompareService
from config import settings
from utils.logger import logger


VALID_STRATEGIES = ["standard", "ema_deviation", "rsi_dynamic", "ahr999", "fear_greed", "value_averaging"]


class ToolsAppService:
    def __init__(self, market_data_service: MarketDataService) -> None:
        self.market_data_service = market_data_service
        self.sentiment_service = SentimentService()
        self.dca_service = DCAService(
            market_data_service=market_data_service,
            sentiment_service=self.sentiment_service,
        )
        self.pair_compare_service = PairCompareService(market_data_service=market_data_service)

    @staticmethod
    def _dca_cache_key(command: SimulateDcaCommand, start_date_str: str) -> str:
        raw = (
            f"{command.symbol}:{start_date_str}:{command.amount}:{command.investment_time}:"
            f"{command.timezone}:{command.strategy}:{json.dumps(command.strategy_params or {}, sort_keys=True)}"
        )
        return f"dca:{hashlib.md5(raw.encode()).hexdigest()}"

    def _validate_dca(self, command: SimulateDcaCommand) -> None:
        if command.symbol not in settings.SYMBOLS:
            raise ValueError(f"无效交易对。可选: {settings.SYMBOLS}")
        if command.strategy not in VALID_STRATEGIES:
            raise ValueError(f"无效策略。可选: {VALID_STRATEGIES}")

    def _validate_compare(self, command: ComparePairsCommand) -> tuple[str, str]:
        symbol_a = command.symbol_a.upper()
        symbol_b = command.symbol_b.upper()
        valid_bases = {symbol.split("/")[0] for symbol in settings.SYMBOLS}
        if symbol_a not in valid_bases:
            raise ValueError(f"无效币种 {symbol_a}。可选: {sorted(valid_bases)}")
        if symbol_b not in valid_bases:
            raise ValueError(f"无效币种 {symbol_b}。可选: {sorted(valid_bases)}")
        if symbol_a == symbol_b:
            raise ValueError("两个币种不能相同")
        return symbol_a, symbol_b

    async def simulate_dca(self, command: SimulateDcaCommand) -> dict[str, Any]:
        self._validate_dca(command)
        start_date_str = command.start_date or (datetime.now() - timedelta(days=command.days or 365)).strftime("%Y-%m-%d")
        cache_key = self._dca_cache_key(command, start_date_str)
        cached = redis_service.get(cache_key)
        if cached:
            return cached

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.dca_service.calculate_dca(
                symbol=command.symbol,
                start_date_str=start_date_str,
                end_date_str=None,
                daily_investment=command.amount,
                target_time_str=command.investment_time,
                timezone=command.timezone,
                strategy=command.strategy,
                strategy_params=command.strategy_params,
            ),
        )
        if "error" in result:
            raise ValueError(result["error"])
        redis_service.set(cache_key, result, ttl=settings.DCA_CACHE_TTL)
        return result

    async def compare_pairs(self, command: ComparePairsCommand) -> dict[str, Any]:
        symbol_a, symbol_b = self._validate_compare(command)
        logger.info(f"币种对比请求: {symbol_a} vs {symbol_b}, {command.days}天, {command.timeframe}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.pair_compare_service.compare_pairs(symbol_a, symbol_b, command.days, command.timeframe),
        )
        if "error" in result:
            raise ValueError(result["error"])
        return result
