from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Query, Request

from app.dependencies import runtime_dependency
from app.rate_limit import limiter
from app.routers.errors import service_http_error
from app.schemas.binance_market import (
    BinanceBookTickerResponse,
    BinanceExchangeInfoResponse,
    BinanceKlineResponse,
    BinanceOrderBookResponse,
    BinancePriceTickerResponse,
    BinanceTickerStatsResponse,
    BinanceTradeListResponse,
)
from config import settings

if TYPE_CHECKING:
    from app.services.market.binance_market_intel_service import BinanceMarketIntelService


router = APIRouter(tags=["Market Data"])
binance_market_dependency = runtime_dependency("market.binance_market_intel")


@router.get("/binance/spot/exchange_info", response_model=BinanceExchangeInfoResponse)
@limiter.limit(settings.RATE_LIMIT_HEAVY)
async def get_binance_spot_exchange_info(
    request: Request,
    symbols: list[str] | None = Query(None),
    permissions: list[str] | None = Query(None),
    symbol_status: str | None = Query(None),
    service: BinanceMarketIntelService = Depends(binance_market_dependency),
):
    try:
        return await service.spot.get_exchange_info(
            symbols=symbols,
            permissions=permissions,
            symbol_status=symbol_status,
        )
    except Exception as exc:
        raise service_http_error("API /binance/spot/exchange_info 错误", exc)


@router.get("/binance/spot/ticker_24hr", response_model=BinanceTickerStatsResponse)
async def get_binance_spot_ticker_24hr(
    symbols: list[str] | None = Query(None),
    service: BinanceMarketIntelService = Depends(binance_market_dependency),
):
    try:
        return await service.spot.get_ticker_24hr(symbols=symbols)
    except Exception as exc:
        raise service_http_error("API /binance/spot/ticker_24hr 错误", exc)


@router.get("/binance/spot/ticker_window", response_model=BinanceTickerStatsResponse)
async def get_binance_spot_ticker_window(
    symbols: list[str] | None = Query(None),
    window_size: str | None = Query(None),
    service: BinanceMarketIntelService = Depends(binance_market_dependency),
):
    try:
        return await service.spot.get_ticker_window(symbols=symbols, window_size=window_size)
    except Exception as exc:
        raise service_http_error("API /binance/spot/ticker_window 错误", exc)


@router.get("/binance/spot/price", response_model=BinancePriceTickerResponse)
async def get_binance_spot_price(
    symbols: list[str] | None = Query(None),
    service: BinanceMarketIntelService = Depends(binance_market_dependency),
):
    try:
        return await service.spot.get_price(symbols=symbols)
    except Exception as exc:
        raise service_http_error("API /binance/spot/price 错误", exc)


@router.get("/binance/spot/book_ticker", response_model=BinanceBookTickerResponse)
async def get_binance_spot_book_ticker(
    symbols: list[str] | None = Query(None),
    service: BinanceMarketIntelService = Depends(binance_market_dependency),
):
    try:
        return await service.spot.get_book_ticker(symbols=symbols)
    except Exception as exc:
        raise service_http_error("API /binance/spot/book_ticker 错误", exc)


@router.get("/binance/spot/depth", response_model=BinanceOrderBookResponse)
async def get_binance_spot_depth(
    symbol: str = Query(...),
    limit: int = Query(20, ge=5, le=5000),
    service: BinanceMarketIntelService = Depends(binance_market_dependency),
):
    try:
        return await service.spot.get_depth(symbol=symbol, limit=limit)
    except Exception as exc:
        raise service_http_error("API /binance/spot/depth 错误", exc)


@router.get("/binance/spot/trades", response_model=BinanceTradeListResponse)
async def get_binance_spot_trades(
    symbol: str = Query(...),
    limit: int = Query(50, ge=1, le=1000),
    service: BinanceMarketIntelService = Depends(binance_market_dependency),
):
    try:
        return await service.spot.get_trades(symbol=symbol, limit=limit)
    except Exception as exc:
        raise service_http_error("API /binance/spot/trades 错误", exc)


@router.get("/binance/spot/agg_trades", response_model=BinanceTradeListResponse)
async def get_binance_spot_agg_trades(
    symbol: str = Query(...),
    limit: int = Query(50, ge=1, le=1000),
    start_time: int | None = Query(None),
    end_time: int | None = Query(None),
    service: BinanceMarketIntelService = Depends(binance_market_dependency),
):
    try:
        return await service.spot.get_agg_trades(
            symbol=symbol,
            limit=limit,
            start_time=start_time,
            end_time=end_time,
        )
    except Exception as exc:
        raise service_http_error("API /binance/spot/agg_trades 错误", exc)


@router.get("/binance/spot/klines", response_model=BinanceKlineResponse)
async def get_binance_spot_klines(
    symbol: str = Query(...),
    interval: str = Query(...),
    limit: int = Query(200, ge=1, le=1000),
    start_time: int | None = Query(None),
    end_time: int | None = Query(None),
    service: BinanceMarketIntelService = Depends(binance_market_dependency),
):
    try:
        return await service.spot.get_klines(
            symbol=symbol,
            interval=interval,
            limit=limit,
            start_time=start_time,
            end_time=end_time,
            ui_mode=False,
        )
    except Exception as exc:
        raise service_http_error("API /binance/spot/klines 错误", exc)


@router.get("/binance/spot/ui_klines", response_model=BinanceKlineResponse)
async def get_binance_spot_ui_klines(
    symbol: str = Query(...),
    interval: str = Query(...),
    limit: int = Query(200, ge=1, le=1000),
    start_time: int | None = Query(None),
    end_time: int | None = Query(None),
    service: BinanceMarketIntelService = Depends(binance_market_dependency),
):
    try:
        return await service.spot.get_klines(
            symbol=symbol,
            interval=interval,
            limit=limit,
            start_time=start_time,
            end_time=end_time,
            ui_mode=True,
        )
    except Exception as exc:
        raise service_http_error("API /binance/spot/ui_klines 错误", exc)
