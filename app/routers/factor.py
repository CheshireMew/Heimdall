from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_factor_execution_service, get_factor_paper_run_manager, get_factor_research_service
from app.routers.errors import service_http_error
from app.schemas.factor import (
    FactorCatalogResponse,
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


@router.get("/factor-research/catalog", response_model=FactorCatalogResponse)
async def get_factor_catalog(
    service: FactorResearchService = Depends(get_factor_research_service),
):
    try:
        return await service.get_catalog_async()
    except Exception as exc:
        raise service_http_error("API /factor-research/catalog 错误", exc)


@router.post("/factor-research/analyze", response_model=FactorResearchResponse)
async def analyze_factors(
    body: FactorResearchRequest,
    service: FactorResearchService = Depends(get_factor_research_service),
):
    try:
        return await service.analyze_async(
            symbol=body.symbol,
            timeframe=body.timeframe,
            days=body.days,
            horizon_bars=body.horizon_bars,
            max_lag_bars=body.max_lag_bars,
            categories=body.categories,
            factor_ids=body.factor_ids,
        )
    except Exception as exc:
        raise service_http_error("API /factor-research/analyze 错误", exc)


@router.get("/factor-research/runs", response_model=list[FactorResearchRunListItemResponse])
async def list_factor_runs(
    limit: int = 20,
    service: FactorResearchService = Depends(get_factor_research_service),
):
    try:
        return await service.list_runs_async(limit=limit)
    except Exception as exc:
        raise service_http_error("API /factor-research/runs 错误", exc)


@router.get("/factor-research/runs/{run_id}", response_model=FactorResearchRunDetailResponse)
async def get_factor_run(
    run_id: int,
    service: FactorResearchService = Depends(get_factor_research_service),
):
    try:
        result = await service.get_run_async(run_id)
        if not result:
            raise HTTPException(status_code=404, detail="Factor run not found")
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise service_http_error(f"API /factor-research/runs/{run_id} 错误", exc)


@router.post("/factor-research/runs/{run_id}/backtest", response_model=FactorExecutionResponse)
async def start_factor_backtest(
    run_id: int,
    body: FactorExecutionRequest,
    service: FactorExecutionService = Depends(get_factor_execution_service),
):
    try:
        backtest_id = await service.run_backtest_async(
            research_run_id=run_id,
            initial_cash=body.initial_cash,
            fee_rate=body.fee_rate,
            position_size_pct=body.position_size_pct,
            stake_mode=body.stake_mode,
            entry_threshold=body.entry_threshold,
            exit_threshold=body.exit_threshold,
            stoploss_pct=body.stoploss_pct,
            takeprofit_pct=body.takeprofit_pct,
            max_hold_bars=body.max_hold_bars,
        )
        return FactorExecutionResponse(success=True, run_id=backtest_id, message="因子组合回测已完成")
    except Exception as exc:
        raise service_http_error(f"API /factor-research/runs/{run_id}/backtest 错误", exc)


@router.post("/factor-research/runs/{run_id}/paper", response_model=FactorExecutionResponse)
async def start_factor_paper_run(
    run_id: int,
    body: FactorExecutionRequest,
    service: FactorPaperRunManager = Depends(get_factor_paper_run_manager),
):
    try:
        return await service.start_run(
            research_run_id=run_id,
            initial_cash=body.initial_cash,
            fee_rate=body.fee_rate,
            position_size_pct=body.position_size_pct,
            stake_mode=body.stake_mode,
            entry_threshold=body.entry_threshold,
            exit_threshold=body.exit_threshold,
            stoploss_pct=body.stoploss_pct,
            takeprofit_pct=body.takeprofit_pct,
            max_hold_bars=body.max_hold_bars,
        )
    except Exception as exc:
        raise service_http_error(f"API /factor-research/runs/{run_id}/paper 错误", exc)
