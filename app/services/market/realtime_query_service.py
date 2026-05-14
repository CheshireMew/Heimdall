from __future__ import annotations

from typing import Any, Callable

from app.domain.market.constants import DEFAULT_ATR_PERIOD, DEFAULT_VOLATILITY_PERIOD
from app.exceptions import ServiceUnavailableError
from app.infra.executor import run_external_io
from app.services.market.app_service_support import validate_market_request
from app.services.market.market_data_service import MarketDataService
from app.services.market.realtime_service import MarketSnapshot, RealtimeService
from config import settings
from utils.logger import logger


class MarketRealtimeQueryService:
    def __init__(
        self,
        *,
        market_data_service: MarketDataService,
        realtime_service: RealtimeService,
        llm_client_factory: Callable[[], Any | None] | None = None,
    ) -> None:
        self.market_data_service = market_data_service
        self.realtime_service = realtime_service
        self.llm_client_factory = llm_client_factory or (lambda: None)

    async def load_snapshot(
        self,
        *,
        symbol: str,
        timeframe: str,
        limit: int,
        atr_period: int = DEFAULT_ATR_PERIOD,
        volatility_period: int = DEFAULT_VOLATILITY_PERIOD,
    ) -> MarketSnapshot:
        validate_market_request(symbol, timeframe)
        result = await run_external_io(
            lambda: self.realtime_service.compute_market_snapshot(
                self.market_data_service,
                symbol,
                timeframe,
                limit,
                atr_period=atr_period,
                volatility_period=volatility_period,
            )
        )
        if not result:
            raise RuntimeError("获取数据失败")
        return result

    async def get_realtime(
        self,
        *,
        symbol: str,
        timeframe: str | None,
        limit: int | None,
    ) -> dict[str, Any]:
        resolved_timeframe = timeframe or settings.TIMEFRAME
        resolved_limit = limit or settings.LIMIT
        try:
            snapshot = await self.load_snapshot(
                symbol=symbol,
                timeframe=resolved_timeframe,
                limit=resolved_limit,
            )
        except Exception as exc:
            err_str = str(exc).lower()
            if "network" in err_str or "connection" in err_str or "timeout" in err_str:
                logger.error(f"实时行情连接失败: {exc}")
                raise ServiceUnavailableError("无法连接到交易所 (Network Error)") from exc
            raise
        kline_data = snapshot.kline_data
        indicators = snapshot.indicators

        ai_analysis = None
        llm_client = self.llm_client_factory()
        if llm_client:
            try:
                ai_analysis = await self.realtime_service.maybe_run_ai(llm_client, symbol, kline_data, indicators)
            except Exception as exc:
                logger.warning(f"AI 分析失败: {exc}")
        return self.realtime_service.build_response_payload(
            symbol,
            resolved_timeframe,
            kline_data,
            indicators,
            ai_analysis=ai_analysis,
        )

    async def get_realtime_ws_payload(
        self,
        *,
        symbol: str,
        timeframe: str,
        limit: int,
        use_ai: bool,
    ) -> dict[str, Any]:
        snapshot = await self.load_snapshot(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )
        kline_data = snapshot.kline_data
        indicators = snapshot.indicators

        ai_analysis = None
        if use_ai:
            llm_client = self.llm_client_factory()
            if llm_client:
                try:
                    ai_analysis = await self.realtime_service.maybe_run_ai(llm_client, symbol, kline_data, indicators)
                except Exception as exc:
                    logger.warning(f"WS AI 分析失败: {exc}")
        return self.realtime_service.build_response_payload(
            symbol,
            timeframe,
            kline_data,
            indicators,
            ai_analysis=ai_analysis,
            include_type=True,
        )

    async def get_technical_metrics(
        self,
        *,
        symbol: str,
        timeframe: str,
        limit: int,
        atr_period: int,
        volatility_period: int,
    ) -> dict[str, Any]:
        snapshot = await self.load_snapshot(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            atr_period=atr_period,
            volatility_period=volatility_period,
        )
        kline_data = snapshot.kline_data
        indicators = snapshot.indicators
        current_price = kline_data[-1][4]
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "sample_size": len(kline_data),
            "current_price": current_price,
            "atr": indicators["atr"],
            "atr_pct": indicators["atr_pct"],
            "realized_volatility_pct": indicators["realized_volatility_pct"],
            "annualized_volatility_pct": indicators["annualized_volatility_pct"],
        }
