from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import datetime, timedelta
from typing import Any

from app.infra.cache import redis_service
from app.services.tools.contracts import ComparePairsCommand, SimulateDcaCommand
from app.services.tools.dca_service import DCAService
from app.services.tools.pair_compare_service import PairCompareService
from app.domain.market.symbol_catalog import get_supported_market_symbols
from config import settings
from utils.logger import logger


VALID_STRATEGIES = ["standard", "ema_deviation", "rsi_dynamic", "ahr999", "fear_greed", "value_averaging"]


class ToolsAppService:
    def __init__(self, dca_service: DCAService, pair_compare_service: PairCompareService) -> None:
        self.dca_service = dca_service
        self.pair_compare_service = pair_compare_service

    @staticmethod
    def _dca_cache_key(command: SimulateDcaCommand, start_date_str: str) -> str:
        raw = (
            f"{command.symbol}:{start_date_str}:{command.amount}:{command.investment_time}:"
            f"{command.timezone}:{command.strategy}:{json.dumps(command.strategy_params or {}, sort_keys=True)}"
        )
        return f"dca:{hashlib.md5(raw.encode()).hexdigest()}"

    def _validate_dca(self, command: SimulateDcaCommand) -> None:
        if (
            command.symbol not in get_supported_market_symbols()
            and self.dca_service.index_data_service.get_instrument(command.symbol) is None
        ):
            raise ValueError("无效标的")
        if command.strategy not in VALID_STRATEGIES:
            raise ValueError(f"无效策略。可选: {VALID_STRATEGIES}")

    def _validate_compare(self, command: ComparePairsCommand) -> tuple[str, str]:
        symbol_a = command.symbol_a.upper()
        symbol_b = command.symbol_b.upper()
        valid_symbols = set(get_supported_market_symbols())
        valid_bases = {symbol.split("/")[0] for symbol in valid_symbols}
        if symbol_a not in valid_bases and symbol_a not in valid_symbols and self.pair_compare_service.index_data_service.get_instrument(symbol_a) is None:
            raise ValueError(f"无效标的 {symbol_a}")
        if symbol_b not in valid_bases and symbol_b not in valid_symbols and self.pair_compare_service.index_data_service.get_instrument(symbol_b) is None:
            raise ValueError(f"无效标的 {symbol_b}")
        if symbol_a == symbol_b:
            raise ValueError("两个标的不能相同")
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
        logger.info(f"标的对比请求: {symbol_a} vs {symbol_b}, {command.days}天, {command.timeframe}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.pair_compare_service.compare_pairs(symbol_a, symbol_b, command.days, command.timeframe),
        )
        if "error" in result:
            raise ValueError(result["error"])
        return result
