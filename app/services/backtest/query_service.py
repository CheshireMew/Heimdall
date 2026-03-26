from __future__ import annotations

import asyncio
from typing import Any

from app.services.backtest.run_repository import BacktestRunRepository
from app.services.backtest.strategy_library import StrategyLibraryService


class BacktestQueryService:
    def __init__(
        self,
        strategy_library: StrategyLibraryService | None = None,
        run_repository: BacktestRunRepository | None = None,
    ) -> None:
        self.strategy_library = strategy_library or StrategyLibraryService()
        self.run_repository = run_repository or BacktestRunRepository()

    async def list_strategies(self) -> list[dict[str, Any]]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.strategy_library.list_strategies)

    async def list_templates(self) -> list[dict[str, Any]]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.strategy_library.list_templates)

    async def get_editor_contract(self) -> dict[str, Any]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.strategy_library.get_editor_contract)

    async def list_indicators(self) -> list[dict[str, Any]]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.strategy_library.list_indicators)

    async def list_indicator_engines(self) -> list[dict[str, Any]]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.strategy_library.list_indicator_engines)

    async def repair_run_storage(self) -> int:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.run_repository.repair_run_contracts)

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
