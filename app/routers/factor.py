from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends

from app.dependencies import runtime_dependency
from app.runtime_refs import (
    FACTORS_EXECUTION_SERVICE,
    FACTORS_PAPER_RUN_MANAGER,
    FACTORS_RESEARCH_SERVICE,
)
from app.schemas.factor import (
    FactorCatalogResponse,
    FactorResearchContractResponse,
    FactorExecutionRequest,
    FactorExecutionResponse,
    FactorResearchRequest,
    FactorResearchResponse,
    FactorResearchRunDetailResponse,
    FactorResearchRunListItemResponse,
)

if TYPE_CHECKING:
    from app.services.factors.execution import FactorExecutionService
    from app.services.factors.paper_manager import FactorPaperRunManager
    from app.services.factors.service import FactorResearchService


router = APIRouter(tags=["Factor Research"])
factor_research_dependency = runtime_dependency(FACTORS_RESEARCH_SERVICE)
factor_execution_dependency = runtime_dependency(FACTORS_EXECUTION_SERVICE)
factor_paper_dependency = runtime_dependency(FACTORS_PAPER_RUN_MANAGER)


@router.get("/factor-research/contract", response_model=FactorResearchContractResponse)
async def get_factor_contract():
    return FactorResearchContractResponse(
        research_defaults=FactorResearchRequest.model_validate({}),
        execution_defaults=FactorExecutionRequest.model_validate({}),
    )


@router.get("/factor-research/catalog", response_model=FactorCatalogResponse)
async def get_factor_catalog(
    service: FactorResearchService = Depends(factor_research_dependency),
):
    return await service.get_catalog_async()


@router.post("/factor-research/analyze", response_model=FactorResearchResponse)
async def analyze_factors(
    body: FactorResearchRequest,
    service: FactorResearchService = Depends(factor_research_dependency),
):
    return await service.analyze_async(
        symbol=body.symbol,
        timeframe=body.timeframe,
        days=body.days,
        horizon_bars=body.horizon_bars,
        max_lag_bars=body.max_lag_bars,
        categories=body.categories,
        factor_ids=body.factor_ids,
    )


@router.get("/factor-research/runs", response_model=list[FactorResearchRunListItemResponse])
async def list_factor_runs(
    limit: int = 20,
    service: FactorResearchService = Depends(factor_research_dependency),
):
    return await service.list_runs_async(limit=limit)


@router.get("/factor-research/runs/{run_id}", response_model=FactorResearchRunDetailResponse)
async def get_factor_run(
    run_id: int,
    service: FactorResearchService = Depends(factor_research_dependency),
):
    return await service.get_run_async(run_id)


@router.post("/factor-research/runs/{run_id}/backtest", response_model=FactorExecutionResponse)
async def start_factor_backtest(
    run_id: int,
    body: FactorExecutionRequest,
    service: FactorExecutionService = Depends(factor_execution_dependency),
):
    backtest_id = await service.run_backtest_async(body.to_config(run_id))
    return FactorExecutionResponse(success=True, run_id=backtest_id, message="因子组合回测已完成")


@router.post("/factor-research/runs/{run_id}/paper", response_model=FactorExecutionResponse)
async def start_factor_paper_run(
    run_id: int,
    body: FactorExecutionRequest,
    service: FactorPaperRunManager = Depends(factor_paper_dependency),
):
    return await service.start_run(body.to_config(run_id))
