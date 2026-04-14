from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class TradeSetupRequest:
    symbol: str
    timeframe: str
    account_size: float
    style: str
    strategy: str
    mode: str = "rules"


class TradeSetupEngine:
    STYLE_PROFILES = {
        "Scalping": {"stop_multiplier": 0.85, "min_stop_pct": 0.008, "risk_pct": 0.006},
        "Intraday": {"stop_multiplier": 1.0, "min_stop_pct": 0.012, "risk_pct": 0.01},
        "Swing": {"stop_multiplier": 1.35, "min_stop_pct": 0.018, "risk_pct": 0.012},
    }
    STRATEGY_PROFILES = {
        "最大收益": {"reward_multiplier": 2.4},
        "稳健突破": {"reward_multiplier": 1.8},
        "回撤反转": {"reward_multiplier": 2.0},
    }

    def build_rules(
        self,
        request: TradeSetupRequest,
        kline_data: list[list[float]],
        indicators: dict[str, Any],
    ) -> dict[str, Any]:
        if len(kline_data) < 30:
            return self._empty(request, "K线数量不足，暂时不生成开单方案")

        current_price = float(kline_data[-1][4])
        atr = self._positive_float(indicators.get("atr"))
        ema = self._positive_float(indicators.get("ema"))
        rsi = self._positive_float(indicators.get("rsi"))
        macd = indicators.get("macd") or (None, None, None)
        macd_hist = self._positive_or_negative_float(macd[2] if isinstance(macd, tuple) else macd.get("histogram"))

        if current_price <= 0 or atr is None or ema is None or rsi is None or macd_hist is None:
            return self._empty(request, "指标还不完整，暂时不生成开单方案")

        side = self._resolve_side(current_price=current_price, ema=ema, rsi=rsi, macd_hist=macd_hist)
        if not side:
            return self._empty(request, "多空条件不清晰，先等待下一根K线")

        style_profile = self._style_profile(request.style)
        strategy_profile = self._strategy_profile(request.strategy)
        stop_distance = max(
            atr * style_profile["stop_multiplier"],
            current_price * style_profile["min_stop_pct"],
        )
        if side == "long":
            recent_floor = min(float(kline[3]) for kline in kline_data[-20:])
            stop = min(current_price - stop_distance, recent_floor)
            target = current_price + abs(current_price - stop) * strategy_profile["reward_multiplier"]
        else:
            recent_ceiling = max(float(kline[2]) for kline in kline_data[-20:])
            stop = max(current_price + stop_distance, recent_ceiling)
            target = current_price - abs(current_price - stop) * strategy_profile["reward_multiplier"]

        risk_amount = max(request.account_size, 0) * style_profile["risk_pct"]
        setup = {
            "side": side,
            "entry": current_price,
            "target": target,
            "stop": stop,
            "risk_reward": abs(target - current_price) / abs(current_price - stop),
            "confidence": self._confidence(current_price=current_price, ema=ema, rsi=rsi, macd_hist=macd_hist, side=side),
            "risk_amount": risk_amount,
            "entry_time": int(kline_data[-1][0]),
            "style": request.style,
            "strategy": request.strategy,
            "source": "rules",
        }
        return {
            "symbol": request.symbol,
            "timeframe": request.timeframe,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "current_price": current_price,
            "setup": setup,
            "reason": self._reason(side=side, current_price=current_price, ema=ema, rsi=rsi, macd_hist=macd_hist),
            "source": "rules",
        }

    def build_ai(
        self,
        request: TradeSetupRequest,
        kline_data: list[list[float]],
        ai_payload: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if not ai_payload:
            return self._empty(request, "AI暂时没有返回可用方案", source="ai")
        if not kline_data:
            return self._empty(request, "K线数量不足，暂时不生成开单方案", source="ai")

        current_price = float(kline_data[-1][4])
        side = self._normalize_side(ai_payload.get("side") or ai_payload.get("signal"))
        if not side:
            return self._empty(request, str(ai_payload.get("reason") or "AI建议等待"), source="ai")

        entry = self._positive_float(ai_payload.get("entry")) or current_price
        target = self._positive_float(ai_payload.get("target") or ai_payload.get("take_profit"))
        stop = self._positive_float(ai_payload.get("stop") or ai_payload.get("stop_loss"))
        if target is None or stop is None:
            return self._empty(request, "AI没有给出完整的目标和止损", source="ai")
        if not self._levels_match_side(side=side, entry=entry, target=target, stop=stop):
            return self._empty(request, "AI返回的价格结构不成立，已拒绝显示", source="ai")

        risk_reward = abs(target - entry) / abs(entry - stop)
        setup = {
            "side": side,
            "entry": entry,
            "target": target,
            "stop": stop,
            "risk_reward": risk_reward,
            "confidence": self._clamp_int(ai_payload.get("confidence"), minimum=0, maximum=100, default=50),
            "risk_amount": max(request.account_size, 0) * self._style_profile(request.style)["risk_pct"],
            "entry_time": int(kline_data[-1][0]),
            "style": request.style,
            "strategy": request.strategy,
            "source": "ai",
        }
        return {
            "symbol": request.symbol,
            "timeframe": request.timeframe,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "current_price": current_price,
            "setup": setup,
            "reason": str(ai_payload.get("reason") or ai_payload.get("reasoning") or "AI已生成交易方案"),
            "source": "ai",
        }

    def _resolve_side(self, *, current_price: float, ema: float, rsi: float, macd_hist: float) -> str | None:
        if current_price > ema and macd_hist >= 0 and 42 <= rsi <= 74:
            return "long"
        if current_price < ema and macd_hist <= 0 and 26 <= rsi <= 58:
            return "short"
        return None

    def _confidence(self, *, current_price: float, ema: float, rsi: float, macd_hist: float, side: str) -> int:
        score = 55
        if side == "long" and current_price > ema:
            score += 12
        if side == "short" and current_price < ema:
            score += 12
        if abs(macd_hist) > 0:
            score += 8
        if 45 <= rsi <= 65:
            score += 10
        return min(score, 88)

    def _reason(self, *, side: str, current_price: float, ema: float, rsi: float, macd_hist: float) -> str:
        direction = "做多" if side == "long" else "做空"
        ema_state = "站上" if current_price > ema else "跌破"
        macd_state = "偏强" if macd_hist >= 0 else "偏弱"
        return f"{direction}：价格{ema_state}EMA，MACD {macd_state}，RSI {rsi:.1f}"

    def _empty(self, request: TradeSetupRequest, reason: str, *, source: str | None = None) -> dict[str, Any]:
        return {
            "symbol": request.symbol,
            "timeframe": request.timeframe,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "current_price": None,
            "setup": None,
            "reason": reason,
            "source": source or request.mode,
        }

    def _style_profile(self, style: str) -> dict[str, float]:
        return self.STYLE_PROFILES.get(style, self.STYLE_PROFILES["Intraday"])

    def _strategy_profile(self, strategy: str) -> dict[str, float]:
        return self.STRATEGY_PROFILES.get(strategy, self.STRATEGY_PROFILES["最大收益"])

    def _normalize_side(self, value: Any) -> str | None:
        text = str(value or "").strip().lower()
        if text in {"long", "buy", "做多", "多"}:
            return "long"
        if text in {"short", "sell", "做空", "空"}:
            return "short"
        return None

    def _levels_match_side(self, *, side: str, entry: float, target: float, stop: float) -> bool:
        if entry <= 0 or target <= 0 or stop <= 0 or entry == stop:
            return False
        if side == "long":
            return stop < entry < target
        return target < entry < stop

    def _clamp_int(self, value: Any, *, minimum: int, maximum: int, default: int) -> int:
        try:
            result = int(float(value))
        except (TypeError, ValueError):
            return default
        return max(minimum, min(maximum, result))

    def _positive_float(self, value: Any) -> float | None:
        try:
            result = float(value)
        except (TypeError, ValueError):
            return None
        return result if result > 0 else None

    def _positive_or_negative_float(self, value: Any) -> float | None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
