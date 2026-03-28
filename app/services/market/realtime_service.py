from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from config import settings
from app.domain.market.prompt_engine import PromptEngine
from app.domain.market.technical_analysis import TechnicalAnalysis
from app.services.market.market_data_service import MarketDataService


class RealtimeService:
    def compute_market_snapshot(
        self,
        market_data_service: MarketDataService,
        symbol: str,
        timeframe: str,
        limit: int,
        *,
        atr_period: int = 14,
        volatility_period: int = 20,
    ) -> Optional[Tuple[list[list[float]], Dict[str, Any]]]:
        kline_data = market_data_service.get_recent_candles(symbol, timeframe, limit=limit)
        if not kline_data:
            return None

        closes = [x[4] for x in kline_data]
        highs = [x[2] for x in kline_data]
        lows = [x[3] for x in kline_data]
        atr = TechnicalAnalysis.calculate_atr(highs, lows, closes, atr_period)
        atr_pct = TechnicalAnalysis.calculate_atr_pct(highs, lows, closes, atr_period)
        realized_volatility = TechnicalAnalysis.calculate_realized_volatility(closes, period=volatility_period)
        annualized_volatility = TechnicalAnalysis.calculate_annualized_volatility(
            closes,
            period=volatility_period,
            periods_per_year=TechnicalAnalysis.periods_per_year_for_timeframe(timeframe),
        )
        indicators = {
            "ema": TechnicalAnalysis.calculate_ema(closes, settings.EMA_PERIOD),
            "rsi": TechnicalAnalysis.calculate_rsi(closes, settings.RSI_PERIOD),
            "macd": TechnicalAnalysis.calculate_macd(
                closes, settings.MACD_FAST, settings.MACD_SLOW, settings.MACD_SIGNAL
            ),
            "atr": atr,
            "atr_pct": atr_pct,
            "realized_volatility": realized_volatility,
            "annualized_volatility": annualized_volatility,
        }
        return kline_data, indicators

    def build_response_payload(
        self,
        symbol: str,
        timeframe: Optional[str],
        kline_data: list[list[float]],
        indicators: Dict[str, Any],
        ai_analysis: Any = None,
        include_type: bool = False,
    ) -> Dict[str, Any]:
        closes = [x[4] for x in kline_data]
        payload = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "current_price": closes[-1],
            "indicators": {
                "ema": indicators["ema"],
                "rsi": indicators["rsi"],
                "macd": {
                    "dif": indicators["macd"][0] if indicators["macd"] and indicators["macd"][0] is not None else None,
                    "dea": indicators["macd"][1] if indicators["macd"] and indicators["macd"][1] is not None else None,
                    "histogram": indicators["macd"][2] if indicators["macd"] and indicators["macd"][2] is not None else None,
                }
                if indicators["macd"]
                else None,
                "atr": indicators["atr"],
                "atr_pct": indicators.get("atr_pct"),
                "realized_volatility_pct": indicators["realized_volatility"] * 100.0
                if indicators.get("realized_volatility") is not None
                else None,
                "annualized_volatility_pct": indicators["annualized_volatility"] * 100.0
                if indicators.get("annualized_volatility") is not None
                else None,
            },
            "ai_analysis": ai_analysis,
            "kline_data": kline_data,
        }
        if timeframe:
            payload["timeframe"] = timeframe
        if include_type:
            payload["type"] = "realtime"
        return payload

    async def maybe_run_ai(
        self,
        llm_client: Any,
        symbol: str,
        kline_data: list[list[float]],
        indicators: Dict[str, Any],
    ) -> Any:
        if not llm_client:
            return None
        prompt = PromptEngine.build_analysis_prompt(symbol, kline_data, indicators)
        return await llm_client.analyze(prompt)
