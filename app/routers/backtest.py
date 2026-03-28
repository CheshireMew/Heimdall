"""
回测相关 API 路由
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.dependencies import get_backtest_command_service, get_backtest_query_service
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
from app.services.backtest.command_service import BacktestCommandService
from app.services.backtest.contracts import (
    BacktestStartCommand,
    CreateIndicatorDefinitionCommand,
    CreateStrategyTemplateCommand,
    CreateStrategyVersionCommand,
    PaperStartCommand,
)
from app.services.backtest.models import PortfolioConfigRecord, ResearchConfigRecord
from app.services.backtest.query_service import BacktestQueryService
from config import settings
from utils.logger import logger


router = APIRouter()


@router.post("/backtest/start", response_model=BacktestStartResponse)
@limiter.limit(settings.RATE_LIMIT_HEAVY)
async def start_backtest(
    request: Request,
    body: BacktestStartRequest,
    service: BacktestCommandService = Depends(get_backtest_command_service),
):
    try:
        return await service.start_backtest(
            BacktestStartCommand(
                strategy_key=body.strategy_key,
                strategy_version=body.strategy_version,
                timeframe=body.timeframe,
                days=body.days,
                initial_cash=body.initial_cash,
                fee_rate=body.fee_rate,
                portfolio=PortfolioConfigRecord(
                    symbols=list(body.portfolio.symbols),
                    max_open_trades=body.portfolio.max_open_trades,
                    position_size_pct=body.portfolio.position_size_pct,
                    stake_mode=body.portfolio.stake_mode,
                ),
                research=ResearchConfigRecord(
                    slippage_bps=body.research.slippage_bps,
                    funding_rate_daily=body.research.funding_rate_daily,
                    in_sample_ratio=body.research.in_sample_ratio,
                    optimize_metric=body.research.optimize_metric,
                    optimize_trials=body.research.optimize_trials,
                    rolling_windows=body.research.rolling_windows,
                ),
            )
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"API /backtest/start 错误: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/paper/start", response_model=PaperStartResponse)
@limiter.limit(settings.RATE_LIMIT_HEAVY)
async def start_paper_run(
    request: Request,
    body: PaperStartRequest,
    service: BacktestCommandService = Depends(get_backtest_command_service),
):
    try:
        return await service.start_paper_run(
            PaperStartCommand(
                strategy_key=body.strategy_key,
                strategy_version=body.strategy_version,
                timeframe=body.timeframe,
                initial_cash=body.initial_cash,
                fee_rate=body.fee_rate,
                portfolio=PortfolioConfigRecord(
                    symbols=list(body.portfolio.symbols),
                    max_open_trades=body.portfolio.max_open_trades,
                    position_size_pct=body.portfolio.position_size_pct,
                    stake_mode=body.portfolio.stake_mode,
                ),
            )
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"API /paper/start 错误: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/paper/{run_id}/stop", response_model=PaperStopResponse)
async def stop_paper_run(
    run_id: int,
    service: BacktestCommandService = Depends(get_backtest_command_service),
):
    try:
        return await service.stop_paper_run(run_id)
    except Exception as exc:
        logger.error(f"API /paper/{run_id}/stop 错误: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")


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
        logger.error(f"API /backtest/{backtest_id} 删除错误: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")


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
        logger.error(f"API /paper/{run_id} 删除错误: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/backtest/strategies", response_model=list[StrategyDefinitionResponse])
async def list_strategies(service: BacktestQueryService = Depends(get_backtest_query_service)):
    try:
        return await service.list_strategies()
    except Exception as exc:
        logger.error(f"API /backtest/strategies 错误: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/backtest/templates", response_model=list[StrategyTemplateResponse])
async def list_strategy_templates(service: BacktestQueryService = Depends(get_backtest_query_service)):
    try:
        return await service.list_templates()
    except Exception as exc:
        logger.error(f"API /backtest/templates 错误: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/backtest/editor-contract", response_model=StrategyEditorContractResponse)
async def get_strategy_editor_contract(service: BacktestQueryService = Depends(get_backtest_query_service)):
    try:
        return await service.get_editor_contract()
    except Exception as exc:
        logger.error(f"API /backtest/editor-contract 错误: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/backtest/templates", response_model=StrategyTemplateResponse)
async def create_strategy_template(
    body: StrategyTemplateCreateRequest,
    service: BacktestCommandService = Depends(get_backtest_command_service),
):
    try:
        return await service.create_template(
            CreateStrategyTemplateCommand(
                key=body.key,
                name=body.name,
                category=body.category,
                description=body.description,
                indicator_keys=list(body.indicator_keys),
                default_config=body.default_config,
                default_parameter_space=body.default_parameter_space,
            )
        )
    except Exception as exc:
        logger.error(f"API /backtest/templates 创建错误: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/backtest/indicators", response_model=list[StrategyIndicatorRegistryResponse])
async def list_indicators(service: BacktestQueryService = Depends(get_backtest_query_service)):
    try:
        return await service.list_indicators()
    except Exception as exc:
        logger.error(f"API /backtest/indicators 错误: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/backtest/indicator-engines", response_model=list[StrategyIndicatorEngineResponse])
async def list_indicator_engines(service: BacktestQueryService = Depends(get_backtest_query_service)):
    try:
        return await service.list_indicator_engines()
    except Exception as exc:
        logger.error(f"API /backtest/indicator-engines 错误: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/backtest/indicators", response_model=StrategyIndicatorRegistryResponse)
async def create_indicator(
    body: IndicatorDefinitionCreateRequest,
    service: BacktestCommandService = Depends(get_backtest_command_service),
):
    try:
        return await service.create_indicator(
            CreateIndicatorDefinitionCommand(
                key=body.key,
                name=body.name,
                engine_key=body.engine_key,
                description=body.description,
                params=list(body.params),
            )
        )
    except Exception as exc:
        logger.error(f"API /backtest/indicators 创建错误: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/backtest/strategies", response_model=StrategyVersionResponse)
async def create_strategy_version(
    body: StrategyVersionCreateRequest,
    service: BacktestCommandService = Depends(get_backtest_command_service),
):
    try:
        return await service.create_strategy_version(
            CreateStrategyVersionCommand(
                key=body.key,
                name=body.name,
                template=body.template,
                category=body.category,
                description=body.description,
                config=body.config,
                parameter_space=body.parameter_space,
                notes=body.notes,
                make_default=body.make_default,
            )
        )
    except Exception as exc:
        logger.error(f"API /backtest/strategies 创建错误: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/backtest/list", response_model=list[BacktestRunResponse])
async def list_backtests(service: BacktestQueryService = Depends(get_backtest_query_service)):
    try:
        return await service.list_runs()
    except Exception as exc:
        logger.error(f"API /backtest/list 错误: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")


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
        logger.error(f"API /backtest/{backtest_id} 错误: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/paper/list", response_model=list[BacktestRunResponse])
async def list_paper_runs(service: BacktestQueryService = Depends(get_backtest_query_service)):
    try:
        return await service.list_paper_runs()
    except Exception as exc:
        logger.error(f"API /paper/list 错误: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")


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
        logger.error(f"API /paper/{run_id} 错误: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")
