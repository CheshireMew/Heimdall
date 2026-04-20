from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Query, Request

from app.dependencies import runtime_dependency
from app.rate_limit import limiter
from app.routers.errors import service_http_error
from app.schemas.binance_market import (
    BinanceBreakoutMonitorResponse,
    BinanceBasisResponse,
    BinanceBookTickerResponse,
    BinanceExchangeInfoResponse,
    BinanceFundingHistoryListResponse,
    BinanceFundingInfoResponse,
    BinanceKlineResponse,
    BinanceMarkPriceResponse,
    BinanceMarketPageResponse,
    BinanceOpenInterestSnapshotResponse,
    BinanceOpenInterestStatsResponse,
    BinanceOrderBookResponse,
    BinancePriceTickerResponse,
    BinanceRatioSeriesResponse,
    BinanceTakerVolumeResponse,
    BinanceTickerStatsResponse,
    BinanceTradeListResponse,
)
from config import settings

if TYPE_CHECKING:
    from app.services.market.binance_market_intel_service import BinanceMarketIntelService


router = APIRouter(tags=["Market Data"])
binance_market_dependency = runtime_dependency("market.binance_market_intel")


@router.get("/binance/market/page", response_model=BinanceMarketPageResponse)
async def get_binance_market_page(
    min_rise_pct: float = Query(5.0, ge=0.5, le=50.0),
    limit: int = Query(24, ge=1, le=30),
    quote_asset: str = Query("USDT", min_length=2, max_length=10),
    service: BinanceMarketIntelService = Depends(binance_market_dependency),
):
    try:
        return await service.page.get_page_payload(
            min_rise_pct=min_rise_pct,
            limit=limit,
            quote_asset=quote_asset,
        )
    except Exception as exc:
        raise service_http_error("API /binance/market/page 错误", exc)


@router.get("/binance/market/breakout_monitor", response_model=BinanceBreakoutMonitorResponse)
async def get_binance_market_breakout_monitor(
    min_rise_pct: float = Query(5.0, ge=0.5, le=50.0),
    limit: int = Query(18, ge=1, le=30),
    quote_asset: str = Query("USDT", min_length=2, max_length=10),
    service: BinanceMarketIntelService = Depends(binance_market_dependency),
):
    try:
        return await service.page.get_breakout_monitor(
            min_rise_pct=min_rise_pct,
            limit=limit,
            quote_asset=quote_asset,
        )
    except Exception as exc:
        raise service_http_error("API /binance/market/breakout_monitor 错误", exc)


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


@router.get("/binance/futures/usdm/exchange_info", response_model=BinanceExchangeInfoResponse)
@limiter.limit(settings.RATE_LIMIT_HEAVY)
async def get_binance_usdm_exchange_info(
    request: Request,
    service: BinanceMarketIntelService = Depends(binance_market_dependency),
):
    try:
        return await service.usdm.get_exchange_info()
    except Exception as exc:
        raise service_http_error("API /binance/futures/usdm/exchange_info 错误", exc)


@router.get("/binance/futures/usdm/ticker_24hr", response_model=BinanceTickerStatsResponse)
async def get_binance_usdm_ticker_24hr(
    symbol: str | None = Query(None),
    service: BinanceMarketIntelService = Depends(binance_market_dependency),
):
    try:
        return await service.usdm.get_ticker_24hr(symbol=symbol)
    except Exception as exc:
        raise service_http_error("API /binance/futures/usdm/ticker_24hr 错误", exc)


@router.get("/binance/futures/usdm/mark_price", response_model=BinanceMarkPriceResponse)
async def get_binance_usdm_mark_price(
    symbol: str | None = Query(None),
    service: BinanceMarketIntelService = Depends(binance_market_dependency),
):
    try:
        return await service.usdm.get_mark_price(symbol=symbol)
    except Exception as exc:
        raise service_http_error("API /binance/futures/usdm/mark_price 错误", exc)


@router.get("/binance/futures/usdm/funding_info", response_model=BinanceFundingInfoResponse)
async def get_binance_usdm_funding_info(
    service: BinanceMarketIntelService = Depends(binance_market_dependency),
):
    try:
        return await service.usdm.get_funding_info()
    except Exception as exc:
        raise service_http_error("API /binance/futures/usdm/funding_info 错误", exc)


@router.get("/binance/futures/usdm/funding_history", response_model=BinanceFundingHistoryListResponse)
async def get_binance_usdm_funding_history(
    symbol: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    start_time: int | None = Query(None),
    end_time: int | None = Query(None),
    service: BinanceMarketIntelService = Depends(binance_market_dependency),
):
    try:
        return await service.usdm.get_funding_history(
            symbol=symbol,
            limit=limit,
            start_time=start_time,
            end_time=end_time,
        )
    except Exception as exc:
        raise service_http_error("API /binance/futures/usdm/funding_history 错误", exc)


@router.get("/binance/futures/usdm/open_interest", response_model=BinanceOpenInterestSnapshotResponse)
async def get_binance_usdm_open_interest(
    symbol: str = Query(...),
    service: BinanceMarketIntelService = Depends(binance_market_dependency),
):
    try:
        return await service.usdm.get_open_interest(symbol=symbol)
    except Exception as exc:
        raise service_http_error("API /binance/futures/usdm/open_interest 错误", exc)


@router.get("/binance/futures/usdm/open_interest_stats", response_model=BinanceOpenInterestStatsResponse)
async def get_binance_usdm_open_interest_stats(
    symbol: str = Query(...),
    period: str = Query(...),
    limit: int = Query(30, ge=1, le=500),
    service: BinanceMarketIntelService = Depends(binance_market_dependency),
):
    try:
        return await service.usdm.get_open_interest_stats(symbol=symbol, period=period, limit=limit)
    except Exception as exc:
        raise service_http_error("API /binance/futures/usdm/open_interest_stats 错误", exc)


@router.get("/binance/futures/usdm/long_short_ratio", response_model=BinanceRatioSeriesResponse)
async def get_binance_usdm_long_short_ratio(
    symbol: str = Query(...),
    period: str = Query(...),
    limit: int = Query(30, ge=1, le=500),
    service: BinanceMarketIntelService = Depends(binance_market_dependency),
):
    try:
        return await service.usdm.get_long_short_ratio(symbol=symbol, period=period, limit=limit)
    except Exception as exc:
        raise service_http_error("API /binance/futures/usdm/long_short_ratio 错误", exc)


@router.get("/binance/futures/usdm/top_trader_accounts", response_model=BinanceRatioSeriesResponse)
async def get_binance_usdm_top_trader_accounts(
    symbol: str = Query(...),
    period: str = Query(...),
    limit: int = Query(30, ge=1, le=500),
    service: BinanceMarketIntelService = Depends(binance_market_dependency),
):
    try:
        return await service.usdm.get_top_trader_accounts(symbol=symbol, period=period, limit=limit)
    except Exception as exc:
        raise service_http_error("API /binance/futures/usdm/top_trader_accounts 错误", exc)


@router.get("/binance/futures/usdm/top_trader_positions", response_model=BinanceRatioSeriesResponse)
async def get_binance_usdm_top_trader_positions(
    symbol: str = Query(...),
    period: str = Query(...),
    limit: int = Query(30, ge=1, le=500),
    service: BinanceMarketIntelService = Depends(binance_market_dependency),
):
    try:
        return await service.usdm.get_top_trader_positions(symbol=symbol, period=period, limit=limit)
    except Exception as exc:
        raise service_http_error("API /binance/futures/usdm/top_trader_positions 错误", exc)


@router.get("/binance/futures/usdm/taker_volume", response_model=BinanceTakerVolumeResponse)
async def get_binance_usdm_taker_volume(
    symbol: str = Query(...),
    period: str = Query(...),
    limit: int = Query(30, ge=1, le=500),
    service: BinanceMarketIntelService = Depends(binance_market_dependency),
):
    try:
        return await service.usdm.get_taker_volume(symbol=symbol, period=period, limit=limit)
    except Exception as exc:
        raise service_http_error("API /binance/futures/usdm/taker_volume 错误", exc)


@router.get("/binance/futures/usdm/basis", response_model=BinanceBasisResponse)
async def get_binance_usdm_basis(
    pair: str = Query(...),
    contract_type: str = Query(...),
    period: str = Query(...),
    limit: int = Query(30, ge=1, le=500),
    service: BinanceMarketIntelService = Depends(binance_market_dependency),
):
    try:
        return await service.usdm.get_basis(pair=pair, contract_type=contract_type, period=period, limit=limit)
    except Exception as exc:
        raise service_http_error("API /binance/futures/usdm/basis 错误", exc)
