from __future__ import annotations

from app.exceptions import NotFoundError
from app.contracts.dto.backtest import (
    BacktestDetailResponse,
    BacktestRunResponse,
    StrategyDefinitionResponse,
    StrategyEditorContractResponse,
    StrategyIndicatorEngineResponse,
    StrategyIndicatorRegistryResponse,
    StrategyTemplateResponse,
)
from app.application.backtest.ports import BacktestRunReader, StrategyReader
from app.infra.executor import run_sync


class BacktestQueryService:
    """API adapter: async boundary that assembles app.contracts.dto responses from repositories."""

    def __init__(
        self,
        *,
        run_repository: BacktestRunReader,
        strategy_query_service: StrategyReader,
    ) -> None:
        self.strategy_query_service = strategy_query_service
        self.run_repository = run_repository

    async def list_strategies(self) -> list[StrategyDefinitionResponse]:
        rows = await run_sync(self.strategy_query_service.list_strategies)
        return [StrategyDefinitionResponse.model_validate(row) for row in rows]

    async def list_templates(self) -> list[StrategyTemplateResponse]:
        rows = await run_sync(self.strategy_query_service.list_templates)
        return [StrategyTemplateResponse.model_validate(row) for row in rows]

    async def get_editor_contract(self) -> StrategyEditorContractResponse:
        row = await run_sync(self.strategy_query_service.get_editor_contract)
        return StrategyEditorContractResponse.model_validate(row)

    async def list_indicators(self) -> list[StrategyIndicatorRegistryResponse]:
        rows = await run_sync(self.strategy_query_service.list_indicators)
        return [StrategyIndicatorRegistryResponse.model_validate(row) for row in rows]

    async def list_indicator_engines(self) -> list[StrategyIndicatorEngineResponse]:
        rows = await run_sync(self.strategy_query_service.list_indicator_engines)
        return [StrategyIndicatorEngineResponse.model_validate(row) for row in rows]

    async def list_runs(self) -> list[BacktestRunResponse]:
        rows = await run_sync(self.run_repository.list_runs)
        return [BacktestRunResponse.model_validate(row) for row in rows]

    async def get_run(self, backtest_id: int, page: int, page_size: int) -> BacktestDetailResponse:
        result = await run_sync(lambda: self.run_repository.get_run(backtest_id, page, page_size))
        if result is None:
            raise NotFoundError("回测记录不存在")
        return BacktestDetailResponse.model_validate(result)

    async def list_paper_runs(self) -> list[BacktestRunResponse]:
        rows = await run_sync(lambda: self.run_repository.list_runs("paper_live"))
        return [BacktestRunResponse.model_validate(row) for row in rows]

    async def get_paper_run(self, run_id: int, page: int, page_size: int) -> BacktestDetailResponse:
        result = await run_sync(
            lambda: self.run_repository.get_run(run_id, page, page_size, "paper_live")
        )
        if result is None:
            raise NotFoundError("模拟盘记录不存在")
        return BacktestDetailResponse.model_validate(result)
