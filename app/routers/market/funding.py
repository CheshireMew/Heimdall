from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.dependencies import runtime_dependency
from app.rate_limit import limiter
from app.routers.errors import service_http_error
from app.schemas.market import FundingRateHistoryResponse, FundingRateSnapshotResponse, FundingRateSyncResponse
from config import settings

if TYPE_CHECKING:
    from app.services.market.funding_rate_app_service import FundingRateAppService


router = APIRouter(tags=["Market Data"])
funding_rate_dependency = runtime_dependency("market.funding_rate_app_service")


@router.get("/funding-rate/current", response_model=FundingRateSnapshotResponse)
@limiter.limit(settings.RATE_LIMIT_HEAVY)
async def get_current_funding_rate(
    request: Request,
    symbol: str = Query(..., description="合约 symbol，例如 BTCUSDT 或 BTC/USDT:USDT"),
    service: FundingRateAppService = Depends(funding_rate_dependency),
):
    try:
        return await service.get_current_funding_rate(symbol)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise service_http_error("API /funding-rate/current 错误", exc)


@router.post("/funding-rate/sync", response_model=FundingRateSyncResponse)
@limiter.limit(settings.RATE_LIMIT_HEAVY)
async def sync_funding_rate_history(
    request: Request,
    symbol: str = Query(..., description="合约 symbol，例如 BTCUSDT"),
    start_date: str = Query("2019-09-01", description="开始日期 YYYY-MM-DD"),
    end_date: str | None = Query(None, description="结束日期 YYYY-MM-DD，默认当前时间"),
    service: FundingRateAppService = Depends(funding_rate_dependency),
):
    try:
        return await service.sync_funding_rate_history(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise service_http_error("API /funding-rate/sync 错误", exc)


@router.get("/funding-rate/history", response_model=FundingRateHistoryResponse)
async def get_funding_rate_history(
    symbol: str = Query(..., description="合约 symbol，例如 BTCUSDT"),
    start_date: str | None = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: str | None = Query(None, description="结束日期 YYYY-MM-DD"),
    limit: int | None = Query(None, ge=1, le=20000),
    service: FundingRateAppService = Depends(funding_rate_dependency),
):
    try:
        return await service.get_funding_rate_history(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise service_http_error("API /funding-rate/history 错误", exc)
