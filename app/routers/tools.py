"""
工具类 API 路由
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from app.dependencies import get_tools_app_service
from app.rate_limit import limiter
from app.schemas.tools import DCARequestSchema, DynamicToolResponse, PairCompareRequestSchema
from app.services.tools.app_service import ToolsAppService
from app.services.tools.contracts import ComparePairsCommand, SimulateDcaCommand
from config import settings
from utils.logger import logger


router = APIRouter()


@router.post("/dca_simulate", response_model=DynamicToolResponse)
@limiter.limit(settings.RATE_LIMIT_HEAVY)
async def dca_simulate(
    request: Request,
    body: DCARequestSchema,
    service: ToolsAppService = Depends(get_tools_app_service),
):
    try:
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
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"API Error (DCA): {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/compare_pairs", response_model=DynamicToolResponse)
@limiter.limit(settings.RATE_LIMIT_HEAVY)
async def compare_pairs(
    request: Request,
    body: PairCompareRequestSchema,
    service: ToolsAppService = Depends(get_tools_app_service),
):
    try:
        return await service.compare_pairs(
            ComparePairsCommand(
                symbol_a=body.symbol_a,
                symbol_b=body.symbol_b,
                days=body.days,
                timeframe=body.timeframe,
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"API Error (Pair Comparison): {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")
