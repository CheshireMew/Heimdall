"""
工具类 API 路由
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Request

from app.dependencies import runtime_dependency
from app.runtime_graph import TOOLS_TOOLS_APP_SERVICE
from app.rate_limit import limiter
from app.schemas.tools import (
    DCARequestSchema,
    DCAResponse,
    PairCompareRequestSchema,
    PairCompareToolResponse,
    ToolsPageContractResponse,
)
from app.services.tools.contracts import ComparePairsCommand, SimulateDcaCommand
from app.services.tools.app_service import DCA_STRATEGY_KEYS
from config import settings

if TYPE_CHECKING:
    from app.services.tools.app_service import ToolsAppService


router = APIRouter()
tools_app_dependency = runtime_dependency(TOOLS_TOOLS_APP_SERVICE)


@router.get("/contract", response_model=ToolsPageContractResponse)
async def get_tools_contract():
    return ToolsPageContractResponse(
        dca_defaults=DCARequestSchema.model_validate({}),
        dca_strategies=list(DCA_STRATEGY_KEYS),
        dca_multiplier_default=settings.DCA_DEFAULT_MULTIPLIER,
        compare_defaults=PairCompareRequestSchema.model_validate({}),
    )


@router.post("/dca_simulate", response_model=DCAResponse)
@limiter.limit(settings.RATE_LIMIT_HEAVY)
async def dca_simulate(
    request: Request,
    body: DCARequestSchema,
    service: ToolsAppService = Depends(tools_app_dependency),
):
    return await service.simulate_dca(
        SimulateDcaCommand(
            symbol=body.symbol,
            amount=body.amount,
            start_date=body.start_date,
            investment_time=body.investment_time,
            timezone=body.timezone,
            days=body.days,
            strategy=body.strategy,
            strategy_params=dict(body.strategy_params or {}),
        )
    )


@router.post("/compare_pairs", response_model=PairCompareToolResponse)
@limiter.limit(settings.RATE_LIMIT_HEAVY)
async def compare_pairs(
    request: Request,
    body: PairCompareRequestSchema,
    service: ToolsAppService = Depends(tools_app_dependency),
):
    return await service.compare_pairs(
        ComparePairsCommand(
            symbol_a=body.symbol_a,
            symbol_b=body.symbol_b,
            days=body.days,
            timeframe=body.timeframe,
        )
    )
