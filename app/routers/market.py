"""
市场数据相关 API 路由
"""
from __future__ import annotations

import asyncio
from datetime import datetime
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Query, Request, WebSocket, WebSocketDisconnect

from app.dependencies import get_index_data_service, get_market_app_service, get_market_data_service
from app.domain.market.symbol_catalog import MARKET_SYMBOL_CATALOG, get_usd_equivalent_symbols
from app.rate_limit import limiter
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
    BinanceReservedFeatureResponse,
    BinanceRwaDynamicResponse,
    BinanceRwaKlineResponse,
    BinanceRwaMarketStatusResponse,
    BinanceRwaMetaResponse,
    BinanceRwaSymbolListResponse,
    BinanceTakerVolumeResponse,
    BinanceTickerStatsResponse,
    BinanceTradeListResponse,
    BinanceWeb3AddressPnlResponse,
    BinanceWeb3MemeRankResponse,
    BinanceWeb3SmartMoneyInflowResponse,
    BinanceWeb3SocialHypeResponse,
    BinanceWeb3UnifiedTokenRankResponse,
)
from app.schemas.market import (
    ApiStatusResponse,
    CryptoIndexResponse,
    FundingRateHistoryResponse,
    FundingRateSnapshotResponse,
    FundingRateSyncResponse,
    MarketIndexHistoryResponse,
    MarketIndexResponse,
    MarketSymbolSearchResponse,
    MarketIndicatorResponse,
    RealtimeResponse,
    TechnicalMetricsResponse,
    TradeSetupResponse,
)
from app.services.market.websocket_service import MarketWebSocketService
from config import settings
from utils.logger import logger

if TYPE_CHECKING:
    from app.services.market.app_service import MarketAppService
    from app.services.market.index_data_service import IndexDataService
    from app.services.market.market_data_service import MarketDataService


router = APIRouter(tags=["Market Data"])
websocket_service = MarketWebSocketService()


def _internal_error(detail: str, exc: Exception) -> HTTPException:
    logger.error(f"{detail}: {exc}")
    return HTTPException(status_code=500, detail="Internal server error")


@router.get("/symbols", response_model=list[MarketSymbolSearchResponse])
async def list_market_symbols(
    index_service: IndexDataService = Depends(get_index_data_service),
):
    crypto_symbols = [
        {
            "symbol": source.symbol,
            "name": source.symbol,
            "asset_class": "crypto",
            "market": "CRYPTO",
            "currency": "USDT",
            "exchange": source.exchange_id.upper(),
            "aliases": [source.symbol.split("/")[0]],
            "pricing_symbol": None,
            "pricing_name": None,
            "pricing_currency": "USDT",
        }
        for source in MARKET_SYMBOL_CATALOG.values()
    ]
    cash_symbols = [
        {
            "symbol": symbol,
            "name": "US Dollar" if symbol == "USD" else f"{symbol} USD equivalent",
            "asset_class": "cash",
            "market": "USD",
            "currency": "USD",
            "exchange": "USD",
            "aliases": ["美元", "现金", "stablecoin", "稳定币", "usd equivalent"],
            "pricing_symbol": None,
            "pricing_name": None,
            "pricing_currency": "USD",
        }
        for symbol in get_usd_equivalent_symbols()
    ]
    index_symbols = [
        {
            "symbol": item["symbol"],
            "name": item["name"],
            "asset_class": "index",
            "market": item["market"],
            "currency": item["currency"],
            "exchange": item["market"],
            "aliases": list(getattr(index_service.get_instrument(item["symbol"]), "aliases", ())),
            "pricing_symbol": item.get("pricing_symbol"),
            "pricing_name": item.get("pricing_name"),
            "pricing_currency": item.get("pricing_currency"),
        }
        for item in index_service.list_indexes()
    ]
    return cash_symbols + crypto_symbols + index_symbols


@router.get("/realtime", response_model=RealtimeResponse)
async def get_realtime_analysis(
    symbol: str = Query(..., description="交易对，如 BTC/USDT"),
    timeframe: str | None = Query(default=None),
    limit: int | None = Query(default=None, ge=1, le=settings.API_MAX_LIMIT),
    market_data_service: MarketDataService = Depends(get_market_data_service),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_realtime(
            market_data_service=market_data_service,
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"API /realtime 错误: {exc}")
        err_str = str(exc).lower()
        if "network" in err_str or "connection" in err_str or "timeout" in err_str:
            raise HTTPException(status_code=503, detail="无法连接到交易所 (Network Error)")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.websocket("/ws/realtime")
async def websocket_realtime(
    websocket: WebSocket,
    market_data_service: MarketDataService = Depends(get_market_data_service),
    service: MarketAppService = Depends(get_market_app_service),
):
    await websocket.accept()
    try:
        try:
            params = websocket_service.parse_params(websocket, service.valid_symbols, service.valid_timeframes)
        except ValueError as exc:
            await websocket_service.reject(websocket, str(exc))
            return

        while True:
            payload = await service.get_realtime_ws_payload(
                market_data_service=market_data_service,
                symbol=params["symbol"],
                timeframe=params["timeframe"],
                limit=params["limit"],
                use_ai=params["use_ai"],
            )
            if not payload:
                await websocket.send_json({"type": "error", "message": "no data"})
                await asyncio.sleep(settings.WS_UPDATE_INTERVAL)
                continue
            await websocket.send_json(payload)
            await asyncio.sleep(settings.WS_UPDATE_INTERVAL)
    except WebSocketDisconnect:
        logger.info("客户端断开实时推送")
    except Exception as exc:
        logger.error(f"WS /ws/realtime 错误: {exc}")
        try:
            await websocket.send_json({"type": "error", "message": str(exc)})
        except Exception:
            pass


@router.get("/history", response_model=list[list[float]])
async def get_market_history(
    symbol: str = Query(..., description="Symbol eg BTC/USDT"),
    timeframe: str = Query(..., description="Timeframe eg 5m"),
    end_ts: int = Query(..., description="End Timestamp (ms)", gt=0),
    limit: int = Query(settings.HISTORY_DEFAULT_LIMIT, description="Limit", ge=1, le=settings.API_MAX_LIMIT),
    market_data_service: MarketDataService = Depends(get_market_data_service),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return service.get_history(
            market_data_service=market_data_service,
            symbol=symbol,
            timeframe=timeframe,
            end_ts=end_ts,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"History API Error: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/klines/latest", response_model=list[list[float]])
async def get_latest_klines(
    symbol: str = Query(..., description="Symbol eg BTC/USDT"),
    timeframe: str = Query(..., description="Timeframe eg 5m"),
    limit: int = Query(settings.LIMIT, description="Limit", ge=1, le=settings.API_MAX_LIMIT),
    market_data_service: MarketDataService = Depends(get_market_data_service),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return service.get_recent_klines(
            market_data_service=market_data_service,
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"Latest klines API Error: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/full_history", response_model=list[list[float]])
@limiter.limit(settings.RATE_LIMIT_HISTORY)
async def get_market_full_history(
    request: Request,
    symbol: str = Query(..., description="Symbol eg BTC/USDT"),
    timeframe: str = Query("1d", description="Timeframe eg 1d"),
    start_date: str = Query("2010-01-01", description="Start Date YYYY-MM-DD"),
    market_data_service: MarketDataService = Depends(get_market_data_service),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_full_history(
            market_data_service=market_data_service,
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"Full History API Error: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/full_history/batch", response_model=dict[str, list[list[float]]])
@limiter.limit(settings.RATE_LIMIT_HISTORY)
async def get_market_full_history_batch(
    request: Request,
    symbols: list[str] = Query(..., description="交易对列表，如 BTC/USDT"),
    timeframe: str = Query("1d", description="Timeframe eg 1d"),
    start_date: str = Query("2010-01-01", description="Start Date YYYY-MM-DD"),
    market_data_service: MarketDataService = Depends(get_market_data_service),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_full_history_batch(
            market_data_service=market_data_service,
            symbols=symbols,
            timeframe=timeframe,
            start_date=start_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"Batch Full History API Error: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/indicators", response_model=list[MarketIndicatorResponse])
async def get_market_indicators(
    category: str | None = Query(None, description="过滤分类, 如 Macro, Onchain, Sentiment, General"),
    days: int = Query(settings.INDICATORS_DEFAULT_DAYS, description="历史数据天数"),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return service.get_indicators(category=category, days=days)
    except Exception as exc:
        logger.error(f"API /indicators 错误: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/indexes", response_model=list[MarketIndexResponse])
async def list_market_indexes(
    service: IndexDataService = Depends(get_index_data_service),
):
    return service.list_indexes()


@router.get("/indexes/history", response_model=MarketIndexHistoryResponse)
@limiter.limit(settings.RATE_LIMIT_HISTORY)
async def get_index_history(
    request: Request,
    symbol: str = Query(..., description="指数 symbol, 如 US_SP500 或 CN_CSI300"),
    timeframe: str = Query("1d", description="第一版仅支持 1d"),
    start_date: str = Query("2010-01-01", description="Start Date YYYY-MM-DD"),
    end_date: str | None = Query(None, description="End Date YYYY-MM-DD"),
    service: IndexDataService = Depends(get_index_data_service),
):
    try:
        return service.get_history(
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"Index History API Error: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/indexes/latest", response_model=MarketIndexHistoryResponse)
@limiter.limit(settings.RATE_LIMIT_HISTORY)
async def get_latest_index(
    request: Request,
    symbol: str = Query(..., description="指数 symbol, 如 US_SP500 或 CN_CSI300"),
    service: IndexDataService = Depends(get_index_data_service),
):
    try:
        return service.get_latest(symbol=symbol)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"Latest Index API Error: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/indexes/pricing/history", response_model=MarketIndexHistoryResponse)
@limiter.limit(settings.RATE_LIMIT_HISTORY)
async def get_index_pricing_history(
    request: Request,
    symbol: str = Query(..., description="指数 symbol, 如 US_SP500 或 CN_CSI300"),
    timeframe: str = Query("1d", description="第一版仅支持 1d"),
    start_date: str = Query("2010-01-01", description="Start Date YYYY-MM-DD"),
    end_date: str | None = Query(None, description="End Date YYYY-MM-DD"),
    service: IndexDataService = Depends(get_index_data_service),
):
    try:
        return service.get_pricing_history(
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"Index Pricing History API Error: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/indexes/pricing/latest", response_model=MarketIndexHistoryResponse)
@limiter.limit(settings.RATE_LIMIT_HISTORY)
async def get_latest_index_pricing(
    request: Request,
    symbol: str = Query(..., description="指数 symbol, 如 US_SP500 或 CN_CSI300"),
    service: IndexDataService = Depends(get_index_data_service),
):
    try:
        return service.get_latest_pricing(symbol=symbol)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"Latest Index Pricing API Error: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/funding-rate/current", response_model=FundingRateSnapshotResponse)
@limiter.limit(settings.RATE_LIMIT_HEAVY)
async def get_current_funding_rate(
    request: Request,
    symbol: str = Query(..., description="合约 symbol，例如 BTCUSDT 或 BTC/USDT:USDT"),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_current_funding_rate(symbol)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"API /funding-rate/current 错误: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/funding-rate/sync", response_model=FundingRateSyncResponse)
@limiter.limit(settings.RATE_LIMIT_HEAVY)
async def sync_funding_rate_history(
    request: Request,
    symbol: str = Query(..., description="合约 symbol，例如 BTCUSDT"),
    start_date: str = Query("2019-09-01", description="开始日期 YYYY-MM-DD"),
    end_date: str | None = Query(None, description="结束日期 YYYY-MM-DD，默认当前时间"),
    service: MarketAppService = Depends(get_market_app_service),
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
        logger.error(f"API /funding-rate/sync 错误: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/funding-rate/history", response_model=FundingRateHistoryResponse)
async def get_funding_rate_history(
    symbol: str = Query(..., description="合约 symbol，例如 BTCUSDT"),
    start_date: str | None = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: str | None = Query(None, description="结束日期 YYYY-MM-DD"),
    limit: int | None = Query(None, ge=1, le=20000),
    service: MarketAppService = Depends(get_market_app_service),
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
        logger.error(f"API /funding-rate/history 错误: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/technical-metrics", response_model=TechnicalMetricsResponse)
async def get_technical_metrics(
    symbol: str = Query(..., description="交易对，如 BTC/USDT"),
    timeframe: str = Query("1d", description="时间周期，如 1d"),
    limit: int = Query(120, ge=30, le=settings.API_MAX_LIMIT),
    atr_period: int = Query(14, ge=2, le=200),
    volatility_period: int = Query(20, ge=2, le=365),
    market_data_service: MarketDataService = Depends(get_market_data_service),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_technical_metrics(
            market_data_service=market_data_service,
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            atr_period=atr_period,
            volatility_period=volatility_period,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"API /technical-metrics 错误: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/trade-setup", response_model=TradeSetupResponse)
async def get_trade_setup(
    symbol: str = Query(..., description="交易对，如 BTC/USDT"),
    timeframe: str = Query("1h", description="时间周期，如 1h"),
    limit: int = Query(120, ge=30, le=settings.API_MAX_LIMIT),
    account_size: float = Query(1000, ge=0),
    style: str = Query("Scalping"),
    strategy: str = Query("最大收益"),
    mode: str = Query("rules", pattern="^(rules|ai)$"),
    market_data_service: MarketDataService = Depends(get_market_data_service),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_trade_setup(
            market_data_service=market_data_service,
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            account_size=account_size,
            style=style,
            strategy=strategy,
            mode=mode,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"API /trade-setup 错误: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/status", response_model=ApiStatusResponse)
async def get_api_status():
    return {
        "status": "running",
        "version": "2.0.0",
        "framework": "FastAPI",
        "dependencies": "ready",
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/crypto_index", response_model=CryptoIndexResponse)
@limiter.limit(settings.RATE_LIMIT_HEAVY)
async def get_crypto_index(
    request: Request,
    top_n: int = Query(20, ge=5, le=100, description="Current top N market cap assets"),
    days: int = Query(90, ge=30, le=365, description="Historical days"),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_crypto_index(top_n=top_n, days=days)
    except Exception as exc:
        logger.error(f"Crypto index API error: {exc}")
        raise HTTPException(status_code=500, detail="Failed to build crypto index")


@router.get("/binance/spot/exchange_info", response_model=BinanceExchangeInfoResponse)
@limiter.limit(settings.RATE_LIMIT_HEAVY)
async def get_binance_spot_exchange_info(
    request: Request,
    symbols: list[str] | None = Query(None),
    permissions: list[str] | None = Query(None),
    symbol_status: str | None = Query(None),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_binance_spot_exchange_info(
            symbols=symbols,
            permissions=permissions,
            symbol_status=symbol_status,
        )
    except Exception as exc:
        raise _internal_error("API /binance/spot/exchange_info 错误", exc)


@router.get("/binance/spot/ticker_24hr", response_model=BinanceTickerStatsResponse)
async def get_binance_spot_ticker_24hr(
    symbols: list[str] | None = Query(None),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_binance_spot_ticker_24hr(symbols=symbols)
    except Exception as exc:
        raise _internal_error("API /binance/spot/ticker_24hr 错误", exc)


@router.get("/binance/spot/ticker_window", response_model=BinanceTickerStatsResponse)
async def get_binance_spot_ticker_window(
    symbols: list[str] | None = Query(None),
    window_size: str | None = Query(None),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_binance_spot_ticker_window(symbols=symbols, window_size=window_size)
    except Exception as exc:
        raise _internal_error("API /binance/spot/ticker_window 错误", exc)


@router.get("/binance/spot/price", response_model=BinancePriceTickerResponse)
async def get_binance_spot_price(
    symbols: list[str] | None = Query(None),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_binance_spot_price(symbols=symbols)
    except Exception as exc:
        raise _internal_error("API /binance/spot/price 错误", exc)


@router.get("/binance/spot/book_ticker", response_model=BinanceBookTickerResponse)
async def get_binance_spot_book_ticker(
    symbols: list[str] | None = Query(None),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_binance_spot_book_ticker(symbols=symbols)
    except Exception as exc:
        raise _internal_error("API /binance/spot/book_ticker 错误", exc)


@router.get("/binance/spot/depth", response_model=BinanceOrderBookResponse)
async def get_binance_spot_depth(
    symbol: str = Query(...),
    limit: int = Query(20, ge=5, le=5000),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_binance_spot_depth(symbol=symbol, limit=limit)
    except Exception as exc:
        raise _internal_error("API /binance/spot/depth 错误", exc)


@router.get("/binance/spot/trades", response_model=BinanceTradeListResponse)
async def get_binance_spot_trades(
    symbol: str = Query(...),
    limit: int = Query(50, ge=1, le=1000),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_binance_spot_trades(symbol=symbol, limit=limit)
    except Exception as exc:
        raise _internal_error("API /binance/spot/trades 错误", exc)


@router.get("/binance/spot/agg_trades", response_model=BinanceTradeListResponse)
async def get_binance_spot_agg_trades(
    symbol: str = Query(...),
    limit: int = Query(50, ge=1, le=1000),
    start_time: int | None = Query(None),
    end_time: int | None = Query(None),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_binance_spot_agg_trades(
            symbol=symbol,
            limit=limit,
            start_time=start_time,
            end_time=end_time,
        )
    except Exception as exc:
        raise _internal_error("API /binance/spot/agg_trades 错误", exc)


@router.get("/binance/spot/klines", response_model=BinanceKlineResponse)
async def get_binance_spot_klines(
    symbol: str = Query(...),
    interval: str = Query(...),
    limit: int = Query(200, ge=1, le=1000),
    start_time: int | None = Query(None),
    end_time: int | None = Query(None),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_binance_spot_klines(
            symbol=symbol,
            interval=interval,
            limit=limit,
            start_time=start_time,
            end_time=end_time,
            ui_mode=False,
        )
    except Exception as exc:
        raise _internal_error("API /binance/spot/klines 错误", exc)


@router.get("/binance/spot/ui_klines", response_model=BinanceKlineResponse)
async def get_binance_spot_ui_klines(
    symbol: str = Query(...),
    interval: str = Query(...),
    limit: int = Query(200, ge=1, le=1000),
    start_time: int | None = Query(None),
    end_time: int | None = Query(None),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_binance_spot_klines(
            symbol=symbol,
            interval=interval,
            limit=limit,
            start_time=start_time,
            end_time=end_time,
            ui_mode=True,
        )
    except Exception as exc:
        raise _internal_error("API /binance/spot/ui_klines 错误", exc)


@router.get("/binance/futures/usdm/exchange_info", response_model=BinanceExchangeInfoResponse)
@limiter.limit(settings.RATE_LIMIT_HEAVY)
async def get_binance_usdm_exchange_info(
    request: Request,
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_binance_usdm_exchange_info()
    except Exception as exc:
        raise _internal_error("API /binance/futures/usdm/exchange_info 错误", exc)


@router.get("/binance/futures/usdm/ticker_24hr", response_model=BinanceTickerStatsResponse)
async def get_binance_usdm_ticker_24hr(
    symbol: str | None = Query(None),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_binance_usdm_ticker_24hr(symbol=symbol)
    except Exception as exc:
        raise _internal_error("API /binance/futures/usdm/ticker_24hr 错误", exc)


@router.get("/binance/futures/usdm/mark_price", response_model=BinanceMarkPriceResponse)
async def get_binance_usdm_mark_price(
    symbol: str | None = Query(None),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_binance_usdm_mark_price(symbol=symbol)
    except Exception as exc:
        raise _internal_error("API /binance/futures/usdm/mark_price 错误", exc)


@router.get("/binance/futures/usdm/funding_info", response_model=BinanceFundingInfoResponse)
async def get_binance_usdm_funding_info(
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_binance_usdm_funding_info()
    except Exception as exc:
        raise _internal_error("API /binance/futures/usdm/funding_info 错误", exc)


@router.get("/binance/futures/usdm/funding_history", response_model=BinanceFundingHistoryListResponse)
async def get_binance_usdm_funding_history(
    symbol: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    start_time: int | None = Query(None),
    end_time: int | None = Query(None),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_binance_usdm_funding_history(
            symbol=symbol,
            limit=limit,
            start_time=start_time,
            end_time=end_time,
        )
    except Exception as exc:
        raise _internal_error("API /binance/futures/usdm/funding_history 错误", exc)


@router.get("/binance/futures/usdm/open_interest", response_model=BinanceOpenInterestSnapshotResponse)
async def get_binance_usdm_open_interest(
    symbol: str = Query(...),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_binance_usdm_open_interest(symbol=symbol)
    except Exception as exc:
        raise _internal_error("API /binance/futures/usdm/open_interest 错误", exc)


@router.get("/binance/futures/usdm/open_interest_stats", response_model=BinanceOpenInterestStatsResponse)
async def get_binance_usdm_open_interest_stats(
    symbol: str = Query(...),
    period: str = Query(...),
    limit: int = Query(30, ge=1, le=500),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_binance_usdm_open_interest_stats(symbol=symbol, period=period, limit=limit)
    except Exception as exc:
        raise _internal_error("API /binance/futures/usdm/open_interest_stats 错误", exc)


@router.get("/binance/futures/usdm/long_short_ratio", response_model=BinanceRatioSeriesResponse)
async def get_binance_usdm_long_short_ratio(
    symbol: str = Query(...),
    period: str = Query(...),
    limit: int = Query(30, ge=1, le=500),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_binance_usdm_long_short_ratio(symbol=symbol, period=period, limit=limit)
    except Exception as exc:
        raise _internal_error("API /binance/futures/usdm/long_short_ratio 错误", exc)


@router.get("/binance/futures/usdm/top_trader_accounts", response_model=BinanceRatioSeriesResponse)
async def get_binance_usdm_top_trader_accounts(
    symbol: str = Query(...),
    period: str = Query(...),
    limit: int = Query(30, ge=1, le=500),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_binance_usdm_top_trader_accounts(symbol=symbol, period=period, limit=limit)
    except Exception as exc:
        raise _internal_error("API /binance/futures/usdm/top_trader_accounts 错误", exc)


@router.get("/binance/futures/usdm/top_trader_positions", response_model=BinanceRatioSeriesResponse)
async def get_binance_usdm_top_trader_positions(
    symbol: str = Query(...),
    period: str = Query(...),
    limit: int = Query(30, ge=1, le=500),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_binance_usdm_top_trader_positions(symbol=symbol, period=period, limit=limit)
    except Exception as exc:
        raise _internal_error("API /binance/futures/usdm/top_trader_positions 错误", exc)


@router.get("/binance/futures/usdm/taker_volume", response_model=BinanceTakerVolumeResponse)
async def get_binance_usdm_taker_volume(
    symbol: str = Query(...),
    period: str = Query(...),
    limit: int = Query(30, ge=1, le=500),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_binance_usdm_taker_volume(symbol=symbol, period=period, limit=limit)
    except Exception as exc:
        raise _internal_error("API /binance/futures/usdm/taker_volume 错误", exc)


@router.get("/binance/futures/usdm/basis", response_model=BinanceBasisResponse)
async def get_binance_usdm_basis(
    pair: str = Query(...),
    contract_type: str = Query(...),
    period: str = Query(...),
    limit: int = Query(30, ge=1, le=500),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_binance_usdm_basis(pair=pair, contract_type=contract_type, period=period, limit=limit)
    except Exception as exc:
        raise _internal_error("API /binance/futures/usdm/basis 错误", exc)


@router.get("/binance/futures/coinm/exchange_info", response_model=BinanceExchangeInfoResponse)
@limiter.limit(settings.RATE_LIMIT_HEAVY)
async def get_binance_coinm_exchange_info(
    request: Request,
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_binance_coinm_exchange_info()
    except Exception as exc:
        raise _internal_error("API /binance/futures/coinm/exchange_info 错误", exc)


@router.get("/binance/futures/coinm/ticker_24hr", response_model=BinanceTickerStatsResponse)
async def get_binance_coinm_ticker_24hr(
    symbol: str | None = Query(None),
    pair: str | None = Query(None),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_binance_coinm_ticker_24hr(symbol=symbol, pair=pair)
    except Exception as exc:
        raise _internal_error("API /binance/futures/coinm/ticker_24hr 错误", exc)


@router.get("/binance/futures/coinm/mark_price", response_model=BinanceMarkPriceResponse)
async def get_binance_coinm_mark_price(
    symbol: str | None = Query(None),
    pair: str | None = Query(None),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_binance_coinm_mark_price(symbol=symbol, pair=pair)
    except Exception as exc:
        raise _internal_error("API /binance/futures/coinm/mark_price 错误", exc)


@router.get("/binance/futures/coinm/funding_info", response_model=BinanceFundingInfoResponse)
async def get_binance_coinm_funding_info(
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_binance_coinm_funding_info()
    except Exception as exc:
        raise _internal_error("API /binance/futures/coinm/funding_info 错误", exc)


@router.get("/binance/futures/coinm/funding_history", response_model=BinanceFundingHistoryListResponse)
async def get_binance_coinm_funding_history(
    symbol: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    start_time: int | None = Query(None),
    end_time: int | None = Query(None),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_binance_coinm_funding_history(
            symbol=symbol,
            limit=limit,
            start_time=start_time,
            end_time=end_time,
        )
    except Exception as exc:
        raise _internal_error("API /binance/futures/coinm/funding_history 错误", exc)


@router.get("/binance/futures/coinm/open_interest", response_model=BinanceOpenInterestSnapshotResponse)
async def get_binance_coinm_open_interest(
    symbol: str = Query(...),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_binance_coinm_open_interest(symbol=symbol)
    except Exception as exc:
        raise _internal_error("API /binance/futures/coinm/open_interest 错误", exc)


@router.get("/binance/futures/coinm/open_interest_stats", response_model=BinanceOpenInterestStatsResponse)
async def get_binance_coinm_open_interest_stats(
    pair: str = Query(...),
    contract_type: str = Query(...),
    period: str = Query(...),
    limit: int = Query(30, ge=1, le=500),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_binance_coinm_open_interest_stats(
            pair=pair,
            contract_type=contract_type,
            period=period,
            limit=limit,
        )
    except Exception as exc:
        raise _internal_error("API /binance/futures/coinm/open_interest_stats 错误", exc)


@router.get("/binance/futures/coinm/long_short_ratio", response_model=BinanceRatioSeriesResponse)
async def get_binance_coinm_long_short_ratio(
    pair: str = Query(...),
    period: str = Query(...),
    limit: int = Query(30, ge=1, le=500),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_binance_coinm_long_short_ratio(pair=pair, period=period, limit=limit)
    except Exception as exc:
        raise _internal_error("API /binance/futures/coinm/long_short_ratio 错误", exc)


@router.get("/binance/futures/coinm/top_trader_accounts", response_model=BinanceRatioSeriesResponse)
async def get_binance_coinm_top_trader_accounts(
    symbol: str = Query(...),
    period: str = Query(...),
    limit: int = Query(30, ge=1, le=500),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_binance_coinm_top_trader_accounts(symbol=symbol, period=period, limit=limit)
    except Exception as exc:
        raise _internal_error("API /binance/futures/coinm/top_trader_accounts 错误", exc)


@router.get("/binance/futures/coinm/top_trader_positions", response_model=BinanceRatioSeriesResponse)
async def get_binance_coinm_top_trader_positions(
    pair: str = Query(...),
    period: str = Query(...),
    limit: int = Query(30, ge=1, le=500),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_binance_coinm_top_trader_positions(pair=pair, period=period, limit=limit)
    except Exception as exc:
        raise _internal_error("API /binance/futures/coinm/top_trader_positions 错误", exc)


@router.get("/binance/futures/coinm/taker_volume", response_model=BinanceTakerVolumeResponse)
async def get_binance_coinm_taker_volume(
    pair: str = Query(...),
    contract_type: str = Query(...),
    period: str = Query(...),
    limit: int = Query(30, ge=1, le=500),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_binance_coinm_taker_volume(
            pair=pair,
            contract_type=contract_type,
            period=period,
            limit=limit,
        )
    except Exception as exc:
        raise _internal_error("API /binance/futures/coinm/taker_volume 错误", exc)


@router.get("/binance/futures/coinm/basis", response_model=BinanceBasisResponse)
async def get_binance_coinm_basis(
    pair: str = Query(...),
    contract_type: str = Query(...),
    period: str = Query(...),
    limit: int = Query(30, ge=1, le=500),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_binance_coinm_basis(pair=pair, contract_type=contract_type, period=period, limit=limit)
    except Exception as exc:
        raise _internal_error("API /binance/futures/coinm/basis 错误", exc)


@router.get("/binance/web3/social_hype", response_model=BinanceWeb3SocialHypeResponse)
async def get_binance_web3_social_hype(
    chain_id: str = Query(...),
    target_language: str = Query("zh"),
    time_range: int = Query(1, ge=1, le=30),
    sentiment: str = Query("All"),
    social_language: str = Query("ALL"),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_binance_web3_social_hype(
            chain_id=chain_id,
            target_language=target_language,
            time_range=time_range,
            sentiment=sentiment,
            social_language=social_language,
        )
    except Exception as exc:
        raise _internal_error("API /binance/web3/social_hype 错误", exc)


@router.get("/binance/web3/unified_token_rank", response_model=BinanceWeb3UnifiedTokenRankResponse)
async def get_binance_web3_unified_token_rank(
    rank_type: int = Query(10),
    chain_id: str | None = Query(None),
    period: int = Query(50),
    sort_by: int = Query(0),
    order_asc: bool = Query(False),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_binance_web3_unified_token_rank(
            rank_type=rank_type,
            chain_id=chain_id,
            period=period,
            sort_by=sort_by,
            order_asc=order_asc,
            page=page,
            size=size,
        )
    except Exception as exc:
        raise _internal_error("API /binance/web3/unified_token_rank 错误", exc)


@router.get("/binance/web3/smart_money_inflow", response_model=BinanceWeb3SmartMoneyInflowResponse)
async def get_binance_web3_smart_money_inflow(
    chain_id: str = Query(...),
    period: str = Query("24h"),
    tag_type: int = Query(2),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_binance_web3_smart_money_inflow(chain_id=chain_id, period=period, tag_type=tag_type)
    except Exception as exc:
        raise _internal_error("API /binance/web3/smart_money_inflow 错误", exc)


@router.get("/binance/web3/meme_rank", response_model=BinanceWeb3MemeRankResponse)
async def get_binance_web3_meme_rank(
    chain_id: str = Query("56"),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_binance_web3_meme_rank(chain_id=chain_id)
    except Exception as exc:
        raise _internal_error("API /binance/web3/meme_rank 错误", exc)


@router.get("/binance/web3/address_pnl_rank", response_model=BinanceWeb3AddressPnlResponse)
async def get_binance_web3_address_pnl_rank(
    chain_id: str = Query(...),
    period: str = Query("30d"),
    tag: str = Query("ALL"),
    page_no: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=25),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_binance_web3_address_pnl_rank(
            chain_id=chain_id,
            period=period,
            tag=tag,
            page_no=page_no,
            page_size=page_size,
        )
    except Exception as exc:
        raise _internal_error("API /binance/web3/address_pnl_rank 错误", exc)


@router.get("/binance/rwa/symbols", response_model=BinanceRwaSymbolListResponse)
async def get_binance_rwa_symbols(
    platform_type: int | None = Query(1),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_binance_rwa_symbols(platform_type=platform_type)
    except Exception as exc:
        raise _internal_error("API /binance/rwa/symbols 错误", exc)


@router.get("/binance/rwa/meta", response_model=BinanceRwaMetaResponse)
async def get_binance_rwa_meta(
    chain_id: str = Query(...),
    contract_address: str = Query(...),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_binance_rwa_meta(chain_id=chain_id, contract_address=contract_address)
    except Exception as exc:
        raise _internal_error("API /binance/rwa/meta 错误", exc)


@router.get("/binance/rwa/market_status", response_model=BinanceRwaMarketStatusResponse)
async def get_binance_rwa_market_status(
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_binance_rwa_market_status()
    except Exception as exc:
        raise _internal_error("API /binance/rwa/market_status 错误", exc)


@router.get("/binance/rwa/asset_market_status", response_model=BinanceRwaMarketStatusResponse)
async def get_binance_rwa_asset_market_status(
    chain_id: str = Query(...),
    contract_address: str = Query(...),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_binance_rwa_asset_market_status(chain_id=chain_id, contract_address=contract_address)
    except Exception as exc:
        raise _internal_error("API /binance/rwa/asset_market_status 错误", exc)


@router.get("/binance/rwa/dynamic", response_model=BinanceRwaDynamicResponse)
async def get_binance_rwa_dynamic(
    chain_id: str = Query(...),
    contract_address: str = Query(...),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_binance_rwa_dynamic(chain_id=chain_id, contract_address=contract_address)
    except Exception as exc:
        raise _internal_error("API /binance/rwa/dynamic 错误", exc)


@router.get("/binance/rwa/kline", response_model=BinanceRwaKlineResponse)
async def get_binance_rwa_kline(
    chain_id: str = Query(...),
    contract_address: str = Query(...),
    interval: str = Query("1d"),
    limit: int = Query(120, ge=1, le=300),
    start_time: int | None = Query(None),
    end_time: int | None = Query(None),
    service: MarketAppService = Depends(get_market_app_service),
):
    try:
        return await service.get_binance_rwa_kline(
            chain_id=chain_id,
            contract_address=contract_address,
            interval=interval,
            limit=limit,
            start_time=start_time,
            end_time=end_time,
        )
    except Exception as exc:
        raise _internal_error("API /binance/rwa/kline 错误", exc)


@router.get("/binance/web3/token_info/search", response_model=BinanceReservedFeatureResponse)
async def get_reserved_binance_web3_token_search(
    keyword: str | None = Query(None),
    chain_ids: str | None = Query(None, alias="chainIds"),
    order_by: str | None = Query(None, alias="orderBy"),
    service: MarketAppService = Depends(get_market_app_service),
):
    return await service.get_reserved_token_search(keyword=keyword, chain_ids=chain_ids, order_by=order_by)


@router.get("/binance/web3/token_info/metadata", response_model=BinanceReservedFeatureResponse)
async def get_reserved_binance_web3_token_metadata(
    chain_id: str | None = Query(None, alias="chainId"),
    contract_address: str | None = Query(None, alias="contractAddress"),
    service: MarketAppService = Depends(get_market_app_service),
):
    return await service.get_reserved_token_metadata(chain_id=chain_id, contract_address=contract_address)


@router.get("/binance/web3/token_info/dynamic", response_model=BinanceReservedFeatureResponse)
async def get_reserved_binance_web3_token_dynamic(
    chain_id: str | None = Query(None, alias="chainId"),
    contract_address: str | None = Query(None, alias="contractAddress"),
    service: MarketAppService = Depends(get_market_app_service),
):
    return await service.get_reserved_token_dynamic(chain_id=chain_id, contract_address=contract_address)


@router.get("/binance/web3/token_info/kline", response_model=BinanceReservedFeatureResponse)
async def get_reserved_binance_web3_token_kline(
    address: str | None = Query(None),
    platform: str | None = Query(None),
    interval: str | None = Query(None),
    limit: int | None = Query(None, ge=1, le=1000),
    from_time: int | None = Query(None, alias="from"),
    to_time: int | None = Query(None, alias="to"),
    pm: str | None = Query(None),
    service: MarketAppService = Depends(get_market_app_service),
):
    return await service.get_reserved_token_kline(
        address=address,
        platform=platform,
        interval=interval,
        limit=limit,
        from_time=from_time,
        to_time=to_time,
        pm=pm,
    )


@router.get("/binance/web3/token_audit", response_model=BinanceReservedFeatureResponse)
async def get_reserved_binance_web3_token_audit(
    binance_chain_id: str | None = Query(None, alias="binanceChainId"),
    contract_address: str | None = Query(None, alias="contractAddress"),
    service: MarketAppService = Depends(get_market_app_service),
):
    return await service.get_reserved_token_audit(
        binance_chain_id=binance_chain_id,
        contract_address=contract_address,
    )
