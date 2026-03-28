from __future__ import annotations

import asyncio
from typing import Any

from app.services.backtest.run_repository import BacktestRunRepository
from app.services.backtest.strategy_query_service import StrategyQueryService


class BacktestQueryService:
    def __init__(
        self,
        *,
        run_repository: BacktestRunRepository,
        strategy_query_service: StrategyQueryService,
    ) -> None:
        self.strategy_query_service = strategy_query_service
        self.run_repository = run_repository

    async def list_strategies(self) -> list[dict[str, Any]]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.strategy_query_service.list_strategies)

    async def list_templates(self) -> list[dict[str, Any]]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.strategy_query_service.list_templates)

    async def get_editor_contract(self) -> dict[str, Any]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.strategy_query_service.get_editor_contract)

    async def list_indicators(self) -> list[dict[str, Any]]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.strategy_query_service.list_indicators)

    async def list_indicator_engines(self) -> list[dict[str, Any]]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.strategy_query_service.list_indicator_engines)

    async def list_runs(self) -> list[dict[str, Any]]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.run_repository.list_runs)

    async def get_run(self, backtest_id: int, page: int, page_size: int) -> dict[str, Any] | None:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: self.run_repository.get_run(backtest_id, page, page_size))

    async def list_paper_runs(self) -> list[dict[str, Any]]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: self.run_repository.list_runs("paper_live"))

    async def get_paper_run(self, run_id: int, page: int, page_size: int) -> dict[str, Any] | None:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: self.run_repository.get_run(run_id, page, page_size, "paper_live"))
