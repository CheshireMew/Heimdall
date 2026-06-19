"""
工具类 API 路由
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.dependencies import runtime_dependency
from app.router_ports.tools import ToolsAppPort
from app.runtime_refs import TOOLS_TOOLS_APP_SERVICE
from app.rate_limit import limiter
from app.contracts.dto.tools import (
    DCAResponse,
    PairCompareToolResponse,
    ToolsPageContractResponse,
)
from app.contracts.tools import ComparePairsCommand, DCA_STRATEGY_KEYS, SimulateDcaCommand
from config import settings


router = APIRouter()
tools_app_dependency = runtime_dependency(TOOLS_TOOLS_APP_SERVICE)


@router.get("/contract", response_model=ToolsPageContractResponse)
async def get_tools_contract():
    return ToolsPageContractResponse(
        dca_defaults=SimulateDcaCommand.model_validate({}),
        dca_strategies=list(DCA_STRATEGY_KEYS),
        dca_multiplier_default=settings.DCA_DEFAULT_MULTIPLIER,
        compare_defaults=ComparePairsCommand.model_validate({}),
    )


@router.post("/dca_simulate", response_model=DCAResponse)
@limiter.limit(settings.RATE_LIMIT_HEAVY)
async def dca_simulate(
    request: Request,
    body: SimulateDcaCommand,
    service: ToolsAppPort = Depends(tools_app_dependency),
):
    return await service.simulate_dca(body)


@router.post("/compare_pairs", response_model=PairCompareToolResponse)
@limiter.limit(settings.RATE_LIMIT_HEAVY)
async def compare_pairs(
    request: Request,
    body: ComparePairsCommand,
    service: ToolsAppPort = Depends(tools_app_dependency),
):
    return await service.compare_pairs(body)
