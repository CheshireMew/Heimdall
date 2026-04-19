"""
回测相关 API 路由
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.dependencies import get_backtest_command_service, get_backtest_query_service
from app.rate_limit import limiter
from app.routers.errors import service_http_error
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


@router.post("/backtest/start", response_model=BacktestStartResponse)
@limiter.limit(settings.RATE_LIMIT_HEAVY)
async def start_backtest(
    request: Request,
    body: BacktestStartRequest,
    service: BacktestCommandService = Depends(get_backtest_command_service),
):
    try:
        return await service.start_backtest(body.to_command())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except HTTPException:
        raise
    except Exception as exc:
        raise service_http_error("API /backtest/start 错误", exc)


@router.post("/paper/start", response_model=PaperStartResponse)
@limiter.limit(settings.RATE_LIMIT_HEAVY)
async def start_paper_run(
    request: Request,
    body: PaperStartRequest,
    service: BacktestCommandService = Depends(get_backtest_command_service),
):
    try:
        return await service.start_paper_run(body.to_command())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except HTTPException:
        raise
    except Exception as exc:
        raise service_http_error("API /paper/start 错误", exc)


@router.post("/paper/{run_id}/stop", response_model=PaperStopResponse)
async def stop_paper_run(
    run_id: int,
    service: BacktestCommandService = Depends(get_backtest_command_service),
):
    try:
        return await service.stop_paper_run(run_id)
    except Exception as exc:
        raise service_http_error(f"API /paper/{run_id}/stop 错误", exc)


@router.delete("/backtest/{backtest_id}", response_model=BacktestDeleteResponse)
async def delete_backtest(
    backtest_id: int,
    service: BacktestCommandService = Depends(get_backtest_command_service),
):
    try:
        return await service.delete_backtest(backtest_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise service_http_error(f"API /backtest/{backtest_id} 删除错误", exc)


@router.delete("/paper/{run_id}", response_model=BacktestDeleteResponse)
async def delete_paper_run(
    run_id: int,
    service: BacktestCommandService = Depends(get_backtest_command_service),
):
    try:
        return await service.delete_paper_run(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise service_http_error(f"API /paper/{run_id} 删除错误", exc)


@router.get("/backtest/strategies", response_model=list[StrategyDefinitionResponse])
async def list_strategies(service: BacktestQueryService = Depends(get_backtest_query_service)):
    try:
        return await service.list_strategies()
    except Exception as exc:
        raise service_http_error("API /backtest/strategies 错误", exc)


@router.get("/backtest/templates", response_model=list[StrategyTemplateResponse])
async def list_strategy_templates(service: BacktestQueryService = Depends(get_backtest_query_service)):
    try:
        return await service.list_templates()
    except Exception as exc:
        raise service_http_error("API /backtest/templates 错误", exc)


@router.get("/backtest/editor-contract", response_model=StrategyEditorContractResponse)
async def get_strategy_editor_contract(service: BacktestQueryService = Depends(get_backtest_query_service)):
    try:
        return await service.get_editor_contract()
    except Exception as exc:
        raise service_http_error("API /backtest/editor-contract 错误", exc)


@router.post("/backtest/templates", response_model=StrategyTemplateResponse)
async def create_strategy_template(
    body: StrategyTemplateCreateRequest,
    service: BacktestCommandService = Depends(get_backtest_command_service),
):
    try:
        return await service.create_template(body.to_command())
    except Exception as exc:
        raise service_http_error("API /backtest/templates 创建错误", exc)


@router.get("/backtest/indicators", response_model=list[StrategyIndicatorRegistryResponse])
async def list_indicators(service: BacktestQueryService = Depends(get_backtest_query_service)):
    try:
        return await service.list_indicators()
    except Exception as exc:
        raise service_http_error("API /backtest/indicators 错误", exc)


@router.get("/backtest/indicator-engines", response_model=list[StrategyIndicatorEngineResponse])
async def list_indicator_engines(service: BacktestQueryService = Depends(get_backtest_query_service)):
    try:
        return await service.list_indicator_engines()
    except Exception as exc:
        raise service_http_error("API /backtest/indicator-engines 错误", exc)


@router.post("/backtest/indicators", response_model=StrategyIndicatorRegistryResponse)
async def create_indicator(
    body: IndicatorDefinitionCreateRequest,
    service: BacktestCommandService = Depends(get_backtest_command_service),
):
    try:
        return await service.create_indicator(body.to_command())
    except Exception as exc:
        raise service_http_error("API /backtest/indicators 创建错误", exc)


@router.post("/backtest/strategies", response_model=StrategyVersionResponse)
async def create_strategy_version(
    body: StrategyVersionCreateRequest,
    service: BacktestCommandService = Depends(get_backtest_command_service),
):
    try:
        return await service.create_strategy_version(body.to_command())
    except Exception as exc:
        raise service_http_error("API /backtest/strategies 创建错误", exc)


@router.get("/backtest/list", response_model=list[BacktestRunResponse])
async def list_backtests(service: BacktestQueryService = Depends(get_backtest_query_service)):
    try:
        return await service.list_runs()
    except Exception as exc:
        raise service_http_error("API /backtest/list 错误", exc)


@router.get("/backtest/{backtest_id}", response_model=BacktestDetailResponse)
async def get_backtest(
    backtest_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    service: BacktestQueryService = Depends(get_backtest_query_service),
):
    try:
        result = await service.get_run(backtest_id, page, page_size)
        if not result:
            raise HTTPException(status_code=404, detail="回测记录不存在")
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise service_http_error(f"API /backtest/{backtest_id} 错误", exc)


@router.get("/paper/list", response_model=list[BacktestRunResponse])
async def list_paper_runs(service: BacktestQueryService = Depends(get_backtest_query_service)):
    try:
        return await service.list_paper_runs()
    except Exception as exc:
        raise service_http_error("API /paper/list 错误", exc)


@router.get("/paper/{run_id}", response_model=BacktestDetailResponse)
async def get_paper_run(
    run_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    service: BacktestQueryService = Depends(get_backtest_query_service),
):
    try:
        result = await service.get_paper_run(run_id, page, page_size)
        if not result:
            raise HTTPException(status_code=404, detail="模拟盘记录不存在")
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise service_http_error(f"API /paper/{run_id} 错误", exc)
