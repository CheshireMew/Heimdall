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
    ) -> Optional[Tuple[list[list[float]], Dict[str, Any]]]:
        kline_data = market_data_service.get_kline_data(symbol, timeframe, limit=limit)
        if not kline_data:
            return None

        closes = [x[4] for x in kline_data]
        highs = [x[2] for x in kline_data]
        lows = [x[3] for x in kline_data]
        indicators = {
            "ema": TechnicalAnalysis.calculate_ema(closes, settings.EMA_PERIOD),
            "rsi": TechnicalAnalysis.calculate_rsi(closes, settings.RSI_PERIOD),
            "macd": TechnicalAnalysis.calculate_macd(
                closes, settings.MACD_FAST, settings.MACD_SLOW, settings.MACD_SIGNAL
            ),
            "atr": TechnicalAnalysis.calculate_atr(highs, lows, closes, 14),
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
                    "dif": indicators["macd"][0] if indicators["macd"] and indicators["macd"][0] else None,
                    "dea": indicators["macd"][1] if indicators["macd"] and indicators["macd"][1] else None,
                    "histogram": indicators["macd"][2] if indicators["macd"] and indicators["macd"][2] else None,
                }
                if indicators["macd"]
                else None,
                "atr": indicators["atr"],
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
