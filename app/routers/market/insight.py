from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Query, Request

from app.dependencies import runtime_dependency
from app.runtime_refs import MARKET_INSIGHT_APP_SERVICE, MARKET_QUERY_APP_SERVICE
from app.rate_limit import limiter
from app.schemas.market import CryptoIndexResponse, MarketIndicatorResponse, TechnicalMetricsResponse, TradeSetupResponse
from config import settings

if TYPE_CHECKING:
    from app.services.market.insight_app_service import MarketInsightAppService
    from app.services.market.query_app_service import MarketQueryAppService


router = APIRouter(tags=["Market Data"])
market_query_dependency = runtime_dependency(MARKET_QUERY_APP_SERVICE)
market_insight_dependency = runtime_dependency(MARKET_INSIGHT_APP_SERVICE)


@router.get("/indicators", response_model=list[MarketIndicatorResponse])
async def get_market_indicators(
    category: str | None = Query(None, description="过滤分类, 如 Macro, Onchain, Sentiment, General"),
    days: int = Query(settings.INDICATORS_DEFAULT_DAYS, description="历史数据天数"),
    service: MarketInsightAppService = Depends(market_insight_dependency),
):
    return await service.get_indicators_async(category=category, days=days)


@router.get("/technical-metrics", response_model=TechnicalMetricsResponse)
async def get_technical_metrics(
    symbol: str = Query(..., description="交易对，如 BTC/USDT"),
    timeframe: str = Query("1d", description="时间周期，如 1d"),
    limit: int = Query(120, ge=30, le=settings.API_MAX_LIMIT),
    atr_period: int = Query(14, ge=2, le=200),
    volatility_period: int = Query(20, ge=2, le=365),
    service: MarketQueryAppService = Depends(market_query_dependency),
):
    return await service.get_technical_metrics(
        symbol=symbol,
        timeframe=timeframe,
        limit=limit,
        atr_period=atr_period,
        volatility_period=volatility_period,
    )


@router.get("/trade-setup", response_model=TradeSetupResponse)
async def get_trade_setup(
    symbol: str = Query(..., description="交易对，如 BTC/USDT"),
    timeframe: str = Query("1h", description="时间周期，如 1h"),
    limit: int = Query(120, ge=30, le=settings.API_MAX_LIMIT),
    account_size: float = Query(1000, ge=0),
    style: str = Query("Scalping"),
    strategy: str = Query("最大收益"),
    mode: str = Query("rules", pattern="^(rules|ai)$"),
    service: MarketInsightAppService = Depends(market_insight_dependency),
):
    return await service.get_trade_setup(
        symbol=symbol,
        timeframe=timeframe,
        limit=limit,
        account_size=account_size,
        style=style,
        strategy=strategy,
        mode=mode,
    )


@router.get("/crypto_index", response_model=CryptoIndexResponse)
@limiter.limit(settings.RATE_LIMIT_HEAVY)
async def get_crypto_index(
    request: Request,
    top_n: int = Query(20, ge=5, le=100, description="Current top N market cap assets"),
    days: int = Query(90, ge=30, le=365, description="Historical days"),
    service: MarketInsightAppService = Depends(market_insight_dependency),
):
    return await service.get_crypto_index(top_n=top_n, days=days)
