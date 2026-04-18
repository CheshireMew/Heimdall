from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Query, Request

from app.dependencies import get_binance_market_intel_service
from app.rate_limit import limiter
from app.routers.market.common import internal_error
from app.schemas.binance_market import (
    BinanceBasisResponse,
    BinanceBookTickerResponse,
    BinanceExchangeInfoResponse,
    BinanceFundingHistoryListResponse,
    BinanceFundingInfoResponse,
    BinanceKlineResponse,
    BinanceMarkPriceResponse,
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


@router.get("/binance/spot/exchange_info", response_model=BinanceExchangeInfoResponse)
@limiter.limit(settings.RATE_LIMIT_HEAVY)
async def get_binance_spot_exchange_info(
    request: Request,
    symbols: list[str] | None = Query(None),
    permissions: list[str] | None = Query(None),
    symbol_status: str | None = Query(None),
    service: BinanceMarketIntelService = Depends(get_binance_market_intel_service),
):
    try:
        return await service.get_spot_exchange_info(
            symbols=symbols,
            permissions=permissions,
            symbol_status=symbol_status,
        )
    except Exception as exc:
        raise internal_error("API /binance/spot/exchange_info 错误", exc)


@router.get("/binance/spot/ticker_24hr", response_model=BinanceTickerStatsResponse)
async def get_binance_spot_ticker_24hr(
    symbols: list[str] | None = Query(None),
    service: BinanceMarketIntelService = Depends(get_binance_market_intel_service),
):
    try:
        return await service.get_spot_ticker_24hr(symbols=symbols)
    except Exception as exc:
        raise internal_error("API /binance/spot/ticker_24hr 错误", exc)


@router.get("/binance/spot/ticker_window", response_model=BinanceTickerStatsResponse)
async def get_binance_spot_ticker_window(
    symbols: list[str] | None = Query(None),
    window_size: str | None = Query(None),
    service: BinanceMarketIntelService = Depends(get_binance_market_intel_service),
):
    try:
        return await service.get_spot_ticker_window(symbols=symbols, window_size=window_size)
    except Exception as exc:
        raise internal_error("API /binance/spot/ticker_window 错误", exc)


@router.get("/binance/spot/price", response_model=BinancePriceTickerResponse)
async def get_binance_spot_price(
    symbols: list[str] | None = Query(None),
    service: BinanceMarketIntelService = Depends(get_binance_market_intel_service),
):
    try:
        return await service.get_spot_price(symbols=symbols)
    except Exception as exc:
        raise internal_error("API /binance/spot/price 错误", exc)


@router.get("/binance/spot/book_ticker", response_model=BinanceBookTickerResponse)
async def get_binance_spot_book_ticker(
    symbols: list[str] | None = Query(None),
    service: BinanceMarketIntelService = Depends(get_binance_market_intel_service),
):
    try:
        return await service.get_spot_book_ticker(symbols=symbols)
    except Exception as exc:
        raise internal_error("API /binance/spot/book_ticker 错误", exc)


@router.get("/binance/spot/depth", response_model=BinanceOrderBookResponse)
async def get_binance_spot_depth(
    symbol: str = Query(...),
    limit: int = Query(20, ge=5, le=5000),
    service: BinanceMarketIntelService = Depends(get_binance_market_intel_service),
):
    try:
        return await service.get_spot_depth(symbol=symbol, limit=limit)
    except Exception as exc:
        raise internal_error("API /binance/spot/depth 错误", exc)


@router.get("/binance/spot/trades", response_model=BinanceTradeListResponse)
async def get_binance_spot_trades(
    symbol: str = Query(...),
    limit: int = Query(50, ge=1, le=1000),
    service: BinanceMarketIntelService = Depends(get_binance_market_intel_service),
):
    try:
        return await service.get_spot_trades(symbol=symbol, limit=limit)
    except Exception as exc:
        raise internal_error("API /binance/spot/trades 错误", exc)


@router.get("/binance/spot/agg_trades", response_model=BinanceTradeListResponse)
async def get_binance_spot_agg_trades(
    symbol: str = Query(...),
    limit: int = Query(50, ge=1, le=1000),
    start_time: int | None = Query(None),
    end_time: int | None = Query(None),
    service: BinanceMarketIntelService = Depends(get_binance_market_intel_service),
):
    try:
        return await service.get_spot_agg_trades(
            symbol=symbol,
            limit=limit,
            start_time=start_time,
            end_time=end_time,
        )
    except Exception as exc:
        raise internal_error("API /binance/spot/agg_trades 错误", exc)


@router.get("/binance/spot/klines", response_model=BinanceKlineResponse)
async def get_binance_spot_klines(
    symbol: str = Query(...),
    interval: str = Query(...),
    limit: int = Query(200, ge=1, le=1000),
    start_time: int | None = Query(None),
    end_time: int | None = Query(None),
    service: BinanceMarketIntelService = Depends(get_binance_market_intel_service),
):
    try:
        return await service.get_spot_klines(
            symbol=symbol,
            interval=interval,
            limit=limit,
            start_time=start_time,
            end_time=end_time,
            ui_mode=False,
        )
    except Exception as exc:
        raise internal_error("API /binance/spot/klines 错误", exc)


@router.get("/binance/spot/ui_klines", response_model=BinanceKlineResponse)
async def get_binance_spot_ui_klines(
    symbol: str = Query(...),
    interval: str = Query(...),
    limit: int = Query(200, ge=1, le=1000),
    start_time: int | None = Query(None),
    end_time: int | None = Query(None),
    service: BinanceMarketIntelService = Depends(get_binance_market_intel_service),
):
    try:
        return await service.get_spot_klines(
            symbol=symbol,
            interval=interval,
            limit=limit,
            start_time=start_time,
            end_time=end_time,
            ui_mode=True,
        )
    except Exception as exc:
        raise internal_error("API /binance/spot/ui_klines 错误", exc)


@router.get("/binance/futures/usdm/exchange_info", response_model=BinanceExchangeInfoResponse)
@limiter.limit(settings.RATE_LIMIT_HEAVY)
async def get_binance_usdm_exchange_info(
    request: Request,
    service: BinanceMarketIntelService = Depends(get_binance_market_intel_service),
):
    try:
        return await service.get_usdm_exchange_info()
    except Exception as exc:
        raise internal_error("API /binance/futures/usdm/exchange_info 错误", exc)


@router.get("/binance/futures/usdm/ticker_24hr", response_model=BinanceTickerStatsResponse)
async def get_binance_usdm_ticker_24hr(
    symbol: str | None = Query(None),
    service: BinanceMarketIntelService = Depends(get_binance_market_intel_service),
):
    try:
        return await service.get_usdm_ticker_24hr(symbol=symbol)
    except Exception as exc:
        raise internal_error("API /binance/futures/usdm/ticker_24hr 错误", exc)


@router.get("/binance/futures/usdm/mark_price", response_model=BinanceMarkPriceResponse)
async def get_binance_usdm_mark_price(
    symbol: str | None = Query(None),
    service: BinanceMarketIntelService = Depends(get_binance_market_intel_service),
):
    try:
        return await service.get_usdm_mark_price(symbol=symbol)
    except Exception as exc:
        raise internal_error("API /binance/futures/usdm/mark_price 错误", exc)


@router.get("/binance/futures/usdm/funding_info", response_model=BinanceFundingInfoResponse)
async def get_binance_usdm_funding_info(
    service: BinanceMarketIntelService = Depends(get_binance_market_intel_service),
):
    try:
        return await service.get_usdm_funding_info()
    except Exception as exc:
        raise internal_error("API /binance/futures/usdm/funding_info 错误", exc)


@router.get("/binance/futures/usdm/funding_history", response_model=BinanceFundingHistoryListResponse)
async def get_binance_usdm_funding_history(
    symbol: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    start_time: int | None = Query(None),
    end_time: int | None = Query(None),
    service: BinanceMarketIntelService = Depends(get_binance_market_intel_service),
):
    try:
        return await service.get_usdm_funding_history(
            symbol=symbol,
            limit=limit,
            start_time=start_time,
            end_time=end_time,
        )
    except Exception as exc:
        raise internal_error("API /binance/futures/usdm/funding_history 错误", exc)


@router.get("/binance/futures/usdm/open_interest", response_model=BinanceOpenInterestSnapshotResponse)
async def get_binance_usdm_open_interest(
    symbol: str = Query(...),
    service: BinanceMarketIntelService = Depends(get_binance_market_intel_service),
):
    try:
        return await service.get_usdm_open_interest(symbol=symbol)
    except Exception as exc:
        raise internal_error("API /binance/futures/usdm/open_interest 错误", exc)


@router.get("/binance/futures/usdm/open_interest_stats", response_model=BinanceOpenInterestStatsResponse)
async def get_binance_usdm_open_interest_stats(
    symbol: str = Query(...),
    period: str = Query(...),
    limit: int = Query(30, ge=1, le=500),
    service: BinanceMarketIntelService = Depends(get_binance_market_intel_service),
):
    try:
        return await service.get_usdm_open_interest_stats(symbol=symbol, period=period, limit=limit)
    except Exception as exc:
        raise internal_error("API /binance/futures/usdm/open_interest_stats 错误", exc)


@router.get("/binance/futures/usdm/long_short_ratio", response_model=BinanceRatioSeriesResponse)
async def get_binance_usdm_long_short_ratio(
    symbol: str = Query(...),
    period: str = Query(...),
    limit: int = Query(30, ge=1, le=500),
    service: BinanceMarketIntelService = Depends(get_binance_market_intel_service),
):
    try:
        return await service.get_usdm_long_short_ratio(symbol=symbol, period=period, limit=limit)
    except Exception as exc:
        raise internal_error("API /binance/futures/usdm/long_short_ratio 错误", exc)


@router.get("/binance/futures/usdm/top_trader_accounts", response_model=BinanceRatioSeriesResponse)
async def get_binance_usdm_top_trader_accounts(
    symbol: str = Query(...),
    period: str = Query(...),
    limit: int = Query(30, ge=1, le=500),
    service: BinanceMarketIntelService = Depends(get_binance_market_intel_service),
):
    try:
        return await service.get_usdm_top_trader_accounts(symbol=symbol, period=period, limit=limit)
    except Exception as exc:
        raise internal_error("API /binance/futures/usdm/top_trader_accounts 错误", exc)


@router.get("/binance/futures/usdm/top_trader_positions", response_model=BinanceRatioSeriesResponse)
async def get_binance_usdm_top_trader_positions(
    symbol: str = Query(...),
    period: str = Query(...),
    limit: int = Query(30, ge=1, le=500),
    service: BinanceMarketIntelService = Depends(get_binance_market_intel_service),
):
    try:
        return await service.get_usdm_top_trader_positions(symbol=symbol, period=period, limit=limit)
    except Exception as exc:
        raise internal_error("API /binance/futures/usdm/top_trader_positions 错误", exc)


@router.get("/binance/futures/usdm/taker_volume", response_model=BinanceTakerVolumeResponse)
async def get_binance_usdm_taker_volume(
    symbol: str = Query(...),
    period: str = Query(...),
    limit: int = Query(30, ge=1, le=500),
    service: BinanceMarketIntelService = Depends(get_binance_market_intel_service),
):
    try:
        return await service.get_usdm_taker_volume(symbol=symbol, period=period, limit=limit)
    except Exception as exc:
        raise internal_error("API /binance/futures/usdm/taker_volume 错误", exc)


@router.get("/binance/futures/usdm/basis", response_model=BinanceBasisResponse)
async def get_binance_usdm_basis(
    pair: str = Query(...),
    contract_type: str = Query(...),
    period: str = Query(...),
    limit: int = Query(30, ge=1, le=500),
    service: BinanceMarketIntelService = Depends(get_binance_market_intel_service),
):
    try:
        return await service.get_usdm_basis(pair=pair, contract_type=contract_type, period=period, limit=limit)
    except Exception as exc:
        raise internal_error("API /binance/futures/usdm/basis 错误", exc)


@router.get("/binance/futures/coinm/exchange_info", response_model=BinanceExchangeInfoResponse)
@limiter.limit(settings.RATE_LIMIT_HEAVY)
async def get_binance_coinm_exchange_info(
    request: Request,
    service: BinanceMarketIntelService = Depends(get_binance_market_intel_service),
):
    try:
        return await service.get_coinm_exchange_info()
    except Exception as exc:
        raise internal_error("API /binance/futures/coinm/exchange_info 错误", exc)


@router.get("/binance/futures/coinm/ticker_24hr", response_model=BinanceTickerStatsResponse)
async def get_binance_coinm_ticker_24hr(
    symbol: str | None = Query(None),
    pair: str | None = Query(None),
    service: BinanceMarketIntelService = Depends(get_binance_market_intel_service),
):
    try:
        return await service.get_coinm_ticker_24hr(symbol=symbol, pair=pair)
    except Exception as exc:
        raise internal_error("API /binance/futures/coinm/ticker_24hr 错误", exc)


@router.get("/binance/futures/coinm/mark_price", response_model=BinanceMarkPriceResponse)
async def get_binance_coinm_mark_price(
    symbol: str | None = Query(None),
    pair: str | None = Query(None),
    service: BinanceMarketIntelService = Depends(get_binance_market_intel_service),
):
    try:
        return await service.get_coinm_mark_price(symbol=symbol, pair=pair)
    except Exception as exc:
        raise internal_error("API /binance/futures/coinm/mark_price 错误", exc)


@router.get("/binance/futures/coinm/funding_info", response_model=BinanceFundingInfoResponse)
async def get_binance_coinm_funding_info(
    service: BinanceMarketIntelService = Depends(get_binance_market_intel_service),
):
    try:
        return await service.get_coinm_funding_info()
    except Exception as exc:
        raise internal_error("API /binance/futures/coinm/funding_info 错误", exc)


@router.get("/binance/futures/coinm/funding_history", response_model=BinanceFundingHistoryListResponse)
async def get_binance_coinm_funding_history(
    symbol: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    start_time: int | None = Query(None),
    end_time: int | None = Query(None),
    service: BinanceMarketIntelService = Depends(get_binance_market_intel_service),
):
    try:
        return await service.get_coinm_funding_history(
            symbol=symbol,
            limit=limit,
            start_time=start_time,
            end_time=end_time,
        )
    except Exception as exc:
        raise internal_error("API /binance/futures/coinm/funding_history 错误", exc)


@router.get("/binance/futures/coinm/open_interest", response_model=BinanceOpenInterestSnapshotResponse)
async def get_binance_coinm_open_interest(
    symbol: str = Query(...),
    service: BinanceMarketIntelService = Depends(get_binance_market_intel_service),
):
    try:
        return await service.get_coinm_open_interest(symbol=symbol)
    except Exception as exc:
        raise internal_error("API /binance/futures/coinm/open_interest 错误", exc)


@router.get("/binance/futures/coinm/open_interest_stats", response_model=BinanceOpenInterestStatsResponse)
async def get_binance_coinm_open_interest_stats(
    pair: str = Query(...),
    contract_type: str = Query(...),
    period: str = Query(...),
    limit: int = Query(30, ge=1, le=500),
    service: BinanceMarketIntelService = Depends(get_binance_market_intel_service),
):
    try:
        return await service.get_coinm_open_interest_stats(
            pair=pair,
            contract_type=contract_type,
            period=period,
            limit=limit,
        )
    except Exception as exc:
        raise internal_error("API /binance/futures/coinm/open_interest_stats 错误", exc)


@router.get("/binance/futures/coinm/long_short_ratio", response_model=BinanceRatioSeriesResponse)
async def get_binance_coinm_long_short_ratio(
    pair: str = Query(...),
    period: str = Query(...),
    limit: int = Query(30, ge=1, le=500),
    service: BinanceMarketIntelService = Depends(get_binance_market_intel_service),
):
    try:
        return await service.get_coinm_long_short_ratio(pair=pair, period=period, limit=limit)
    except Exception as exc:
        raise internal_error("API /binance/futures/coinm/long_short_ratio 错误", exc)


@router.get("/binance/futures/coinm/top_trader_accounts", response_model=BinanceRatioSeriesResponse)
async def get_binance_coinm_top_trader_accounts(
    symbol: str = Query(...),
    period: str = Query(...),
    limit: int = Query(30, ge=1, le=500),
    service: BinanceMarketIntelService = Depends(get_binance_market_intel_service),
):
    try:
        return await service.get_coinm_top_trader_accounts(symbol=symbol, period=period, limit=limit)
    except Exception as exc:
        raise internal_error("API /binance/futures/coinm/top_trader_accounts 错误", exc)


@router.get("/binance/futures/coinm/top_trader_positions", response_model=BinanceRatioSeriesResponse)
async def get_binance_coinm_top_trader_positions(
    pair: str = Query(...),
    period: str = Query(...),
    limit: int = Query(30, ge=1, le=500),
    service: BinanceMarketIntelService = Depends(get_binance_market_intel_service),
):
    try:
        return await service.get_coinm_top_trader_positions(pair=pair, period=period, limit=limit)
    except Exception as exc:
        raise internal_error("API /binance/futures/coinm/top_trader_positions 错误", exc)


@router.get("/binance/futures/coinm/taker_volume", response_model=BinanceTakerVolumeResponse)
async def get_binance_coinm_taker_volume(
    pair: str = Query(...),
    contract_type: str = Query(...),
    period: str = Query(...),
    limit: int = Query(30, ge=1, le=500),
    service: BinanceMarketIntelService = Depends(get_binance_market_intel_service),
):
    try:
        return await service.get_coinm_taker_volume(
            pair=pair,
            contract_type=contract_type,
            period=period,
            limit=limit,
        )
    except Exception as exc:
        raise internal_error("API /binance/futures/coinm/taker_volume 错误", exc)


@router.get("/binance/futures/coinm/basis", response_model=BinanceBasisResponse)
async def get_binance_coinm_basis(
    pair: str = Query(...),
    contract_type: str = Query(...),
    period: str = Query(...),
    limit: int = Query(30, ge=1, le=500),
    service: BinanceMarketIntelService = Depends(get_binance_market_intel_service),
):
    try:
        return await service.get_coinm_basis(pair=pair, contract_type=contract_type, period=period, limit=limit)
    except Exception as exc:
        raise internal_error("API /binance/futures/coinm/basis 错误", exc)
