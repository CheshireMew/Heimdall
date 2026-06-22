from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.dependencies import runtime_dependency
from app.router_ports.market import MarketInsightPort, MarketQueryPort
from app.runtime_refs import MARKET_INSIGHT_APP_SERVICE, MARKET_QUERY_APP_SERVICE
from app.contracts.dto.market import (
    DliLiquidityResponse,
    MarketIndicatorResponse,
    TechnicalMetricsResponse,
    TradeSetupResponse,
)
from app.domain.market.constants import DEFAULT_ATR_PERIOD, DEFAULT_VOLATILITY_PERIOD
from config import settings


router = APIRouter(tags=["Market Data"])
market_query_dependency = runtime_dependency(MARKET_QUERY_APP_SERVICE)
market_insight_dependency = runtime_dependency(MARKET_INSIGHT_APP_SERVICE)


@router.get("/indicators", response_model=list[MarketIndicatorResponse])
async def get_market_indicators(
    category: str | None = Query(None, description="过滤分类, 如 Macro, Onchain, Sentiment, General"),
    days: int = Query(settings.INDICATORS_DEFAULT_DAYS, description="历史数据天数"),
    service: MarketInsightPort = Depends(market_insight_dependency),
):
    return await service.get_indicators_async(category=category, days=days)


@router.get("/indicators/dli", response_model=DliLiquidityResponse)
async def get_dli_liquidity(
    days: int = Query(settings.INDICATORS_DEFAULT_DAYS, ge=30, le=3650, description="展示历史数据天数"),
    change_days: int = Query(30, ge=1, le=365, description="变化统计周期天数"),
    service: MarketInsightPort = Depends(market_insight_dependency),
):
    return await service.get_dli_liquidity_async(days=days, change_days=change_days)


@router.get("/technical-metrics", response_model=TechnicalMetricsResponse)
async def get_technical_metrics(
    symbol: str = Query(..., description="交易对，如 BTC/USDT"),
    timeframe: str = Query("1d", description="时间周期，如 1d"),
    limit: int = Query(120, ge=30, le=settings.API_MAX_LIMIT),
    atr_period: int = Query(DEFAULT_ATR_PERIOD, ge=2, le=200),
    volatility_period: int = Query(DEFAULT_VOLATILITY_PERIOD, ge=2, le=365),
    service: MarketQueryPort = Depends(market_query_dependency),
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
    service: MarketInsightPort = Depends(market_insight_dependency),
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


