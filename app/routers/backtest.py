"""
回测相关 API 路由
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Query, Request

from app.dependencies import runtime_dependency
from app.exceptions import NotFoundError
from app.runtime_refs import BACKTEST_COMMAND_SERVICE, BACKTEST_QUERY_SERVICE
from app.rate_limit import limiter
from app.schemas.backtest import (
    BacktestDetailResponse,
    BacktestDeleteResponse,
    BacktestRunResponse,
    BacktestStartRequest,
    BacktestStartResponse,
    IndicatorDefinitionCreateRequest,
    StrategyEditorContractResponse,
    StrategyIndicatorEngineResponse,
    StrategyIndicatorRegistryResponse,
    StrategyDefinitionResponse,
    StrategyTemplateCreateRequest,
    StrategyTemplateResponse,
    StrategyVersionCreateRequest,
    StrategyVersionResponse,
    PaperStartRequest,
    PaperStartResponse,
    PaperStopResponse,
)
from config import settings

if TYPE_CHECKING:
    from app.services.backtest.command_service import BacktestCommandService
    from app.services.backtest.query_service import BacktestQueryService


router = APIRouter()
backtest_command_dependency = runtime_dependency(BACKTEST_COMMAND_SERVICE)
backtest_query_dependency = runtime_dependency(BACKTEST_QUERY_SERVICE)


@router.post("/backtest/start", response_model=BacktestStartResponse)
@limiter.limit(settings.RATE_LIMIT_HEAVY)
async def start_backtest(
    request: Request,
    body: BacktestStartRequest,
    service: BacktestCommandService = Depends(backtest_command_dependency),
):
    return await service.start_backtest(body.to_command())


@router.post("/paper/start", response_model=PaperStartResponse)
@limiter.limit(settings.RATE_LIMIT_HEAVY)
async def start_paper_run(
    request: Request,
    body: PaperStartRequest,
    service: BacktestCommandService = Depends(backtest_command_dependency),
):
    return await service.start_paper_run(body.to_command())


@router.post("/paper/{run_id}/stop", response_model=PaperStopResponse)
async def stop_paper_run(
    run_id: int,
    service: BacktestCommandService = Depends(backtest_command_dependency),
):
    return await service.stop_paper_run(run_id)


@router.delete("/backtest/{backtest_id}", response_model=BacktestDeleteResponse)
async def delete_backtest(
    backtest_id: int,
    service: BacktestCommandService = Depends(backtest_command_dependency),
):
    return await service.delete_backtest(backtest_id)


@router.delete("/paper/{run_id}", response_model=BacktestDeleteResponse)
async def delete_paper_run(
    run_id: int,
    service: BacktestCommandService = Depends(backtest_command_dependency),
):
    return await service.delete_paper_run(run_id)


@router.get("/backtest/strategies", response_model=list[StrategyDefinitionResponse])
async def list_strategies(service: BacktestQueryService = Depends(backtest_query_dependency)):
    return await service.list_strategies()


@router.get("/backtest/templates", response_model=list[StrategyTemplateResponse])
async def list_strategy_templates(service: BacktestQueryService = Depends(backtest_query_dependency)):
    return await service.list_templates()


@router.get("/backtest/editor-contract", response_model=StrategyEditorContractResponse)
async def get_strategy_editor_contract(service: BacktestQueryService = Depends(backtest_query_dependency)):
    return await service.get_editor_contract()


@router.post("/backtest/templates", response_model=StrategyTemplateResponse)
async def create_strategy_template(
    body: StrategyTemplateCreateRequest,
    service: BacktestCommandService = Depends(backtest_command_dependency),
):
    return await service.create_template(body.to_command())


@router.get("/backtest/indicators", response_model=list[StrategyIndicatorRegistryResponse])
async def list_indicators(service: BacktestQueryService = Depends(backtest_query_dependency)):
    return await service.list_indicators()


@router.get("/backtest/indicator-engines", response_model=list[StrategyIndicatorEngineResponse])
async def list_indicator_engines(service: BacktestQueryService = Depends(backtest_query_dependency)):
    return await service.list_indicator_engines()


@router.post("/backtest/indicators", response_model=StrategyIndicatorRegistryResponse)
async def create_indicator(
    body: IndicatorDefinitionCreateRequest,
    service: BacktestCommandService = Depends(backtest_command_dependency),
):
    return await service.create_indicator(body.to_command())


@router.post("/backtest/strategies", response_model=StrategyVersionResponse)
async def create_strategy_version(
    body: StrategyVersionCreateRequest,
    service: BacktestCommandService = Depends(backtest_command_dependency),
):
    return await service.create_strategy_version(body.to_command())


@router.get("/backtest/list", response_model=list[BacktestRunResponse])
async def list_backtests(service: BacktestQueryService = Depends(backtest_query_dependency)):
    return await service.list_runs()


@router.get("/backtest/{backtest_id}", response_model=BacktestDetailResponse)
async def get_backtest(
    backtest_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    service: BacktestQueryService = Depends(backtest_query_dependency),
):
    result = await service.get_run(backtest_id, page, page_size)
    if result is None:
        raise NotFoundError("回测记录不存在")
    return result


@router.get("/paper/list", response_model=list[BacktestRunResponse])
async def list_paper_runs(service: BacktestQueryService = Depends(backtest_query_dependency)):
    return await service.list_paper_runs()


@router.get("/paper/{run_id}", response_model=BacktestDetailResponse)
async def get_paper_run(
    run_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    service: BacktestQueryService = Depends(backtest_query_dependency),
):
    result = await service.get_paper_run(run_id, page, page_size)
    if result is None:
        raise NotFoundError("模拟盘记录不存在")
    return result
