from __future__ import annotations

from app.services.backtest.run_repository import BacktestRunRepository
from app.services.backtest.strategy_query_service import StrategyQueryService
from app.services.executor import run_sync
from app.schemas.backtest import (
    BacktestDetailResponse,
    BacktestRunResponse,
    StrategyDefinitionResponse,
    StrategyEditorContractResponse,
    StrategyIndicatorEngineResponse,
    StrategyIndicatorRegistryResponse,
    StrategyTemplateResponse,
)


class BacktestQueryService:
    def __init__(
        self,
        *,
        run_repository: BacktestRunRepository,
        strategy_query_service: StrategyQueryService,
    ) -> None:
        self.strategy_query_service = strategy_query_service
        self.run_repository = run_repository

    async def list_strategies(self) -> list[StrategyDefinitionResponse]:
        return await run_sync(self.strategy_query_service.list_strategies)

    async def list_templates(self) -> list[StrategyTemplateResponse]:
        return await run_sync(self.strategy_query_service.list_templates)

    async def get_editor_contract(self) -> StrategyEditorContractResponse:
        return await run_sync(self.strategy_query_service.get_editor_contract)

    async def list_indicators(self) -> list[StrategyIndicatorRegistryResponse]:
        return await run_sync(self.strategy_query_service.list_indicators)

    async def list_indicator_engines(self) -> list[StrategyIndicatorEngineResponse]:
        return await run_sync(self.strategy_query_service.list_indicator_engines)

    async def list_runs(self) -> list[BacktestRunResponse]:
        return await run_sync(self.run_repository.list_runs)

    async def get_run(self, backtest_id: int, page: int, page_size: int) -> BacktestDetailResponse | None:
        return await run_sync(lambda: self.run_repository.get_run(backtest_id, page, page_size))

    async def list_paper_runs(self) -> list[BacktestRunResponse]:
        return await run_sync(lambda: self.run_repository.list_runs("paper_live"))

    async def get_paper_run(self, run_id: int, page: int, page_size: int) -> BacktestDetailResponse | None:
        return await run_sync(
            lambda: self.run_repository.get_run(run_id, page, page_size, "paper_live")
        )
