from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Any

from app.domain.market.technical_analysis import TechnicalAnalysis

from .binance_numbers import to_float


KlineLoader = Callable[[str, str, str, int], Awaitable[dict[str, Any]]]


class BinanceBreakoutMonitor:
    def __init__(self, kline_loader: KlineLoader) -> None:
        self._kline_loader = kline_loader

    async def build(
        self,
        *,
        market_snapshot: dict[str, Any],
        min_rise_pct: float,
        limit: int,
        quote_asset: str,
    ) -> dict[str, Any]:
        spot_response = market_snapshot["spot_ticker"]
        usdm_ticker_response = market_snapshot["usdm_ticker"]
        usdm_mark_response = market_snapshot["usdm_mark"]
        candidates = [
            *self._collect_spot_candidates(
                spot_response.get("items", []),
                min_rise_pct=min_rise_pct,
                quote_asset=quote_asset,
            ),
            *self._collect_derivatives_candidates(
                "usdm",
                usdm_ticker_response.get("items", []),
                usdm_mark_response.get("items", []),
                min_rise_pct=min_rise_pct,
                quote_asset=quote_asset,
            ),
        ]
        ranked = sorted(
            candidates,
            key=lambda item: ((item.get("price_change_pct") or -999.0), (item.get("quote_volume") or 0.0)),
            reverse=True,
        )[:limit]
        await asyncio.gather(*(self._enrich_candidate(item) for item in ranked))
        ranked.sort(
            key=lambda item: (
                item.get("verdict") == "优先关注",
                item.get("momentum_score", 0),
                item.get("natural_score", 0),
                item.get("price_change_pct") or -999.0,
            ),
            reverse=True,
        )
        summary = {
            "monitored_count": len(ranked),
            "natural_count": sum(1 for item in ranked if item.get("structure_ok")),
            "momentum_count": sum(1 for item in ranked if item.get("momentum_ok")),
            "focus_count": sum(1 for item in ranked if item.get("verdict") == "优先关注"),
            "advancing_count": sum(1 for item in ranked if item.get("follow_status") in {"继续上行", "高位蓄势"}),
            "spot_count": sum(1 for item in ranked if item.get("market") == "spot"),
            "contract_count": sum(1 for item in ranked if item.get("market") == "usdm"),
        }
        return {
            "exchange": "binance",
            "min_rise_pct": float(min_rise_pct),
            "quote_asset": quote_asset,
            "updated_at": int(time.time() * 1000),
            "summary": summary,
            "items": ranked,
        }

    def normalize_quote_asset(self, quote_asset: str | None) -> str:
        return str(quote_asset or "USDT").strip().upper()

    def empty_ticker_response(self, market: str) -> dict[str, Any]:
        return {"exchange": "binance", "market": market, "items": []}

    def empty_mark_price_response(self, market: str) -> dict[str, Any]:
        return {"exchange": "binance", "market": market, "items": []}

    def _collect_spot_candidates(
        self,
        rows: list[dict[str, Any]],
        *,
        min_rise_pct: float,
        quote_asset: str,
    ) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []
        for item in rows:
            symbol = str(item.get("symbol") or "").upper()
            change_pct = to_float(item.get("price_change_pct"))
            if not symbol.endswith(quote_asset) or not self._is_watchable_symbol("spot", symbol, quote_asset):
                continue
            if change_pct is None or change_pct < min_rise_pct:
                continue
            candidates.append(
                {
                    "market": "spot",
                    "market_label": "现货",
                    "symbol": symbol,
                    "last_price": to_float(item.get("last_price")),
                    "mark_price": None,
                    "price_change_pct": change_pct,
                    "quote_volume": to_float(item.get("quote_volume")),
                    "funding_rate_pct": None,
                }
            )
        return candidates

    def _collect_derivatives_candidates(
        self,
        market: str,
        ticker_rows: list[dict[str, Any]],
        mark_rows: list[dict[str, Any]],
        *,
        min_rise_pct: float,
        quote_asset: str,
    ) -> list[dict[str, Any]]:
        mark_map = {str(item.get("symbol") or "").upper(): item for item in mark_rows}
        candidates: list[dict[str, Any]] = []
        for item in ticker_rows:
            symbol = str(item.get("symbol") or "").upper()
            change_pct = to_float(item.get("price_change_pct"))
            if not self._is_watchable_symbol(market, symbol, quote_asset) or change_pct is None or change_pct < min_rise_pct:
                continue
            mark = mark_map.get(symbol, {})
            candidates.append(
                {
                    "market": market,
                    "market_label": "U 本位" if market == "usdm" else "币本位",
                    "symbol": symbol,
                    "last_price": to_float(item.get("last_price")),
                    "mark_price": to_float(mark.get("mark_price")),
                    "price_change_pct": change_pct,
                    "quote_volume": to_float(item.get("quote_volume")),
                    "funding_rate_pct": self._percent_from_ratio(mark.get("last_funding_rate")),
                }
            )
        return candidates

    async def _enrich_candidate(self, item: dict[str, Any]) -> None:
        try:
            kline_15m, kline_1h = await asyncio.gather(
                self._kline_loader(item["market"], item["symbol"], "15m", 80),
                self._kline_loader(item["market"], item["symbol"], "1h", 80),
            )
        except Exception:
            item.setdefault("follow_status", "数据不足")
            item.setdefault("verdict", "只做观察")
            item.setdefault("reasons", ["短周期数据暂时不足"])
            return

        snapshot_15m = self._build_snapshot(kline_15m.get("items", []), recent_window=16, green_window=12, window_bars=4)
        snapshot_1h = self._build_snapshot(kline_1h.get("items", []), recent_window=12, green_window=8, window_bars=4)
        natural_score, momentum_score, reasons = self._score_candidate(item, snapshot_15m, snapshot_1h)
        item["change_15m_pct"] = snapshot_15m.get("bar_change_pct")
        item["change_1h_pct"] = snapshot_1h.get("bar_change_pct")
        item["change_4h_pct"] = snapshot_1h.get("window_change_pct")
        item["pullback_from_high_pct"] = snapshot_15m.get("pullback_from_high_pct")
        item["range_position_pct"] = snapshot_15m.get("range_position_pct")
        item["ema20_gap_15m_pct"] = snapshot_15m.get("ema20_gap_pct")
        item["ema20_gap_1h_pct"] = snapshot_1h.get("ema20_gap_pct")
        item["rsi_15m"] = snapshot_15m.get("rsi")
        item["rsi_1h"] = snapshot_1h.get("rsi")
        item["macd_hist_15m"] = snapshot_15m.get("macd_hist")
        item["green_ratio_15m_pct"] = snapshot_15m.get("green_ratio_pct")
        item["natural_score"] = natural_score
        item["momentum_score"] = momentum_score
        item["structure_ok"] = natural_score >= 65
        item["momentum_ok"] = momentum_score >= 65
        item["follow_status"] = self._resolve_follow_status(snapshot_15m, snapshot_1h)
        item["verdict"] = self._resolve_verdict(item)
        item["reasons"] = reasons[:4]

    def _build_snapshot(
        self,
        rows: list[dict[str, Any]],
        *,
        recent_window: int,
        green_window: int,
        window_bars: int,
    ) -> dict[str, float | None]:
        closes = [to_float(row.get("close")) for row in rows]
        opens = [to_float(row.get("open")) for row in rows]
        highs = [to_float(row.get("high")) for row in rows]
        lows = [to_float(row.get("low")) for row in rows]
        if len(closes) < 30 or any(value is None for value in closes[-30:]):
            return {}

        close_values = [value for value in closes if value is not None]
        open_values = [value for value in opens if value is not None]
        high_values = [value for value in highs if value is not None]
        low_values = [value for value in lows if value is not None]
        last_price = close_values[-1]
        ema20 = TechnicalAnalysis.calculate_ema(close_values, 20)
        rsi14 = TechnicalAnalysis.calculate_rsi(close_values, 14)
        _, _, macd_hist = TechnicalAnalysis.calculate_macd(close_values)
        recent_high = max(high_values[-recent_window:]) if len(high_values) >= recent_window else max(high_values)
        recent_low = min(low_values[-recent_window:]) if len(low_values) >= recent_window else min(low_values)
        recent_range = recent_high - recent_low
        green_pairs = list(zip(open_values[-green_window:], close_values[-green_window:]))
        max_bar_change_pct = max(
            (abs(self._percentage_change(close_price, open_price)) for open_price, close_price in green_pairs if open_price),
            default=None,
        )
        return {
            "bar_change_pct": self._percentage_change(last_price, close_values[-2]) if len(close_values) >= 2 else None,
            "window_change_pct": self._percentage_change(last_price, close_values[-(window_bars + 1)]) if len(close_values) > window_bars else None,
            "pullback_from_high_pct": self._percentage_change(last_price, recent_high),
            "range_position_pct": ((last_price - recent_low) / recent_range * 100.0) if recent_range > 0 else None,
            "ema20_gap_pct": self._percentage_change(last_price, ema20),
            "rsi": rsi14,
            "macd_hist": macd_hist,
            "green_ratio_pct": (sum(1 for open_price, close_price in green_pairs if close_price > open_price) / len(green_pairs) * 100.0) if green_pairs else None,
            "max_bar_change_pct": max_bar_change_pct,
        }

    def _score_candidate(
        self,
        item: dict[str, Any],
        snapshot_15m: dict[str, float | None],
        snapshot_1h: dict[str, float | None],
    ) -> tuple[int, int, list[str]]:
        natural_score = 0
        momentum_score = 0
        reasons: list[str] = []
        pullback_from_high_pct = snapshot_15m.get("pullback_from_high_pct")
        if pullback_from_high_pct is not None:
            if pullback_from_high_pct >= -2.5:
                natural_score += 30
                reasons.append("离高点不远，回撤不深")
            elif pullback_from_high_pct >= -5.0:
                natural_score += 16
        range_position_pct = snapshot_15m.get("range_position_pct")
        if range_position_pct is not None:
            if range_position_pct >= 70.0:
                natural_score += 24
                reasons.append("价格仍压在强势区间上沿")
            elif range_position_pct >= 55.0:
                natural_score += 12
        green_ratio_pct = snapshot_15m.get("green_ratio_pct")
        if green_ratio_pct is not None:
            if 45.0 <= green_ratio_pct <= 82.0:
                natural_score += 20
                reasons.append("短线节奏均匀，不是单根硬拉")
            elif 35.0 <= green_ratio_pct <= 90.0:
                natural_score += 10
        max_bar_change_pct = snapshot_15m.get("max_bar_change_pct")
        spike_limit = min(8.0, max(3.0, (item.get("price_change_pct") or 0.0) * 0.45))
        if max_bar_change_pct is not None:
            if max_bar_change_pct <= spike_limit:
                natural_score += 26
            elif max_bar_change_pct <= spike_limit * 1.5:
                natural_score += 10
        ema20_gap_15m = snapshot_15m.get("ema20_gap_pct")
        ema20_gap_1h = snapshot_1h.get("ema20_gap_pct")
        if ema20_gap_15m is not None and ema20_gap_15m > 0:
            momentum_score += 20
            reasons.append("15 分钟仍站在均线之上")
        if ema20_gap_1h is not None and ema20_gap_1h > 0:
            momentum_score += 20
            reasons.append("1 小时趋势还没掉头")
        rsi_15m = snapshot_15m.get("rsi")
        if rsi_15m is not None:
            if 55.0 <= rsi_15m <= 78.0:
                momentum_score += 15
            elif 50.0 <= rsi_15m <= 82.0:
                momentum_score += 8
        rsi_1h = snapshot_1h.get("rsi")
        if rsi_1h is not None:
            if 55.0 <= rsi_1h <= 75.0:
                momentum_score += 15
            elif 50.0 <= rsi_1h <= 80.0:
                momentum_score += 8
        macd_hist_15m = snapshot_15m.get("macd_hist")
        if macd_hist_15m is not None and macd_hist_15m > 0:
            momentum_score += 15
        change_15m_pct = snapshot_15m.get("bar_change_pct")
        if change_15m_pct is not None and change_15m_pct > 0:
            momentum_score += 8
        change_1h_pct = snapshot_1h.get("bar_change_pct")
        if change_1h_pct is not None and change_1h_pct > 0:
            momentum_score += 14
            reasons.append("最近 1 小时还在续涨")
        if pullback_from_high_pct is not None and pullback_from_high_pct >= -1.5:
            momentum_score += 8
        return min(int(round(natural_score)), 100), min(int(round(momentum_score)), 100), list(dict.fromkeys(reasons))

    def _resolve_follow_status(
        self,
        snapshot_15m: dict[str, float | None],
        snapshot_1h: dict[str, float | None],
    ) -> str:
        change_15m_pct = snapshot_15m.get("bar_change_pct")
        change_1h_pct = snapshot_1h.get("bar_change_pct")
        pullback_from_high_pct = snapshot_15m.get("pullback_from_high_pct")
        range_position_pct = snapshot_15m.get("range_position_pct")
        if (
            change_15m_pct is not None and change_15m_pct > 0
            and pullback_from_high_pct is not None and pullback_from_high_pct >= -1.5
            and range_position_pct is not None and range_position_pct >= 85.0
        ):
            return "继续上行"
        if (
            change_1h_pct is not None and change_1h_pct >= 0
            and pullback_from_high_pct is not None and pullback_from_high_pct >= -3.5
            and range_position_pct is not None and range_position_pct >= 65.0
        ):
            return "高位蓄势"
        return "冲高回撤"

    def _resolve_verdict(self, item: dict[str, Any]) -> str:
        if item.get("structure_ok") and item.get("momentum_ok") and item.get("follow_status") in {"继续上行", "高位蓄势"}:
            return "优先关注"
        if item.get("structure_ok") or item.get("momentum_ok"):
            return "继续跟踪"
        return "只做观察"

    def _is_watchable_symbol(self, market: str, symbol: str, quote_asset: str) -> bool:
        normalized = str(symbol or "").upper()
        if market == "spot":
            if not normalized.endswith(quote_asset):
                return False
            base_symbol = normalized[: -len(quote_asset)]
            leveraged_suffixes = ("UP", "DOWN", "BULL", "BEAR", "3L", "3S", "4L", "4S", "5L", "5S")
            return bool(base_symbol) and not base_symbol.endswith(leveraged_suffixes)
        if market == "usdm":
            return normalized.endswith(quote_asset) and "_" not in normalized
        return normalized.endswith("_PERP")

    def _percentage_change(self, current: float | None, reference: float | None) -> float | None:
        if current in (None, 0) or reference in (None, 0):
            return None
        return ((current / reference) - 1.0) * 100.0

    def _percent_from_ratio(self, value: Any) -> float | None:
        numeric = to_float(value)
        if numeric is None:
            return None
        return numeric * 100.0
