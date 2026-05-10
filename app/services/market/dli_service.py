from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from statistics import median, pstdev
from typing import Any

from app.infra.persistence.market.indicator_repository import MarketIndicatorRepository


@dataclass(frozen=True)
class DliIndicatorDefinition:
    id: str
    label: str
    short_label: str
    group: str
    group_label: str
    weight: float
    polarity: str
    description: str


GROUP_WEIGHTS = {
    "policy": 65.0,
    "funding": 10.0,
    "credit": 5.0,
    "risk": 20.0,
}

DLI_INDICATORS: tuple[DliIndicatorDefinition, ...] = (
    DliIndicatorDefinition("FED_BALANCE", "美联储资产负债表", "Fed Balance", "policy", "政策与准备金池", 30.0, "higher_supports", "联储资产端扩张通常代表基础流动性改善。"),
    DliIndicatorDefinition("TGA", "美国财政部现金账户", "TGA", "policy", "政策与准备金池", 20.0, "lower_supports", "TGA 上升会从银行体系抽走准备金，下降则释放流动性。"),
    DliIndicatorDefinition("ONRRP", "隔夜逆回购", "ON RRP", "policy", "政策与准备金池", 15.0, "lower_supports", "ON RRP 余额下降代表闲置现金回流市场体系。"),
    DliIndicatorDefinition("FED_RATE", "联邦基金利率", "Fed Funds", "funding", "融资与利率", 4.0, "lower_supports", "政策利率越高，风险资产折现和融资压力越强。"),
    DliIndicatorDefinition("SOFR", "SOFR 隔夜融资利率", "SOFR", "funding", "融资与利率", 3.0, "lower_supports", "美元短端融资成本，快速上行通常压制风险偏好。"),
    DliIndicatorDefinition("US10Y", "美国 10 年期国债收益率", "10Y Yield", "funding", "融资与利率", 3.0, "lower_supports", "长端无风险收益率，影响估值锚和美元资产吸引力。"),
    DliIndicatorDefinition("HY_SPREAD", "高收益债利差", "HY Spread", "credit", "信用与中介", 5.0, "lower_supports", "信用风险溢价扩张时代表风险融资环境转差。"),
    DliIndicatorDefinition("VIX", "VIX 波动率指数", "VIX", "risk", "风险与价格", 6.0, "lower_supports", "美股隐含波动率，越高代表避险需求越强。"),
    DliIndicatorDefinition("DXY", "贸易加权美元指数", "Dollar", "risk", "风险与价格", 5.0, "lower_supports", "美元强势通常压制全球美元流动性和风险资产。"),
    DliIndicatorDefinition("NASDAQ", "纳斯达克综合指数", "NASDAQ", "risk", "风险与价格", 5.0, "higher_supports", "高久期成长资产的风险偏好代理。"),
    DliIndicatorDefinition("M2", "美国 M2 货币供应", "M2", "risk", "风险与价格", 4.0, "higher_supports", "广义货币环境，扩张时更利于风险资产估值。"),
)

DISPLAY_INDICATORS = DLI_INDICATORS + (
    DliIndicatorDefinition("US02Y", "美国 2 年期国债收益率", "2Y Yield", "funding", "融资与利率", 0.0, "lower_supports", "更贴近政策路径预期的短中端收益率。"),
    DliIndicatorDefinition("WTI", "WTI 原油价格", "WTI Oil", "risk", "风险与价格", 0.0, "lower_supports", "能源价格上行会推升通胀约束和政策压力。"),
    DliIndicatorDefinition("GOLD", "黄金现货价格", "Gold", "risk", "风险与价格", 0.0, "higher_supports", "真实利率和避险需求的综合映射。"),
)

SCORED_IDS = tuple(item.id for item in DLI_INDICATORS)
DISPLAY_IDS = tuple(item.id for item in DISPLAY_INDICATORS)
DEFINITION_BY_ID = {item.id: item for item in DISPLAY_INDICATORS}


class DliLiquidityService:
    def __init__(self, repository: MarketIndicatorRepository) -> None:
        self.repository = repository

    def build(self, *, days: int = 365) -> dict[str, Any]:
        display_days = max(30, min(days, 3650))
        now = datetime.now()
        model_cutoff = now - timedelta(days=3650)
        display_cutoff = now - timedelta(days=display_days)
        history_map = self.repository.get_history_points(list(DISPLAY_IDS), start_date=model_cutoff)
        meta_map = {item["id"]: item for item in self.repository.list_active_meta("Macro")}

        current = self._composite_at(now, history_map)
        threshold_series = self._composite_history(
            history_map,
            start_date=now - timedelta(days=1825),
            end_date=now,
        )
        thresholds = self._thresholds(threshold_series)
        score = current["score"]
        state, tone = self._state(score, thresholds["p20"], thresholds["p50"], thresholds["p80"])
        score_percentile = self._score_percentile(
            score,
            [item["score"] for item in threshold_series if item.get("score") is not None],
        )
        display_history = [
            {
                "date": item["date"].isoformat(),
                "score": round(item["score"], 2),
                "state": self._state(item["score"], thresholds["p20"], thresholds["p50"], thresholds["p80"])[0],
            }
            for item in threshold_series
            if item["date"] >= display_cutoff
        ]
        updated_at = self._latest_update(history_map)

        return {
            "score": None if score is None else round(score),
            "raw_score": None if score is None else round(score, 2),
            "score_percentile": None if score_percentile is None else round(score_percentile, 2),
            "state": state,
            "tone": tone,
            "updated_at": updated_at.isoformat() if updated_at else None,
            "coverage": current["coverage"],
            "methodology": "rolling_median_mad_weighted_v1",
            "thresholds": thresholds,
            "components": current["components"],
            "history": display_history,
            "indicators": self._indicator_payloads(history_map, meta_map, display_cutoff),
            "alerts": self._alerts(current["components"]),
        }

    def _indicator_payloads(
        self,
        history_map: dict[str, list[dict[str, Any]]],
        meta_map: dict[str, dict[str, Any]],
        display_cutoff: datetime,
    ) -> list[dict[str, Any]]:
        payloads = []
        for definition in DISPLAY_INDICATORS:
            rows = [
                item
                for item in history_map.get(definition.id, [])
                if item["timestamp"] >= display_cutoff
            ]
            meta = meta_map.get(definition.id, {})
            history = [{"date": item["date"], "value": item["value"]} for item in rows]
            payloads.append(
                {
                    "indicator_id": definition.id,
                    "name": meta.get("name") or definition.label,
                    "category": meta.get("category") or "Macro",
                    "unit": meta.get("unit") or "",
                    "current_value": history[-1]["value"] if history else None,
                    "last_updated": history[-1]["date"] if history else None,
                    "history": history,
                }
            )
        return payloads

    def _composite_history(
        self,
        history_map: dict[str, list[dict[str, Any]]],
        *,
        start_date: datetime,
        end_date: datetime,
    ) -> list[dict[str, Any]]:
        raw_dates = sorted(
            {
                item["timestamp"]
                for indicator_id in SCORED_IDS
                for item in history_map.get(indicator_id, [])
                if start_date <= item["timestamp"] <= end_date
            }
        )
        dates = self._weekly_sample_dates(raw_dates)
        series = []
        for date in dates:
            composite = self._composite_at(date, history_map)
            if composite["score"] is not None:
                series.append({"date": date, "score": composite["score"]})
        return series

    @staticmethod
    def _weekly_sample_dates(dates: list[datetime]) -> list[datetime]:
        sampled: list[datetime] = []
        seen_weeks: set[tuple[int, int]] = set()
        for date in reversed(dates):
            key = date.isocalendar()[:2]
            if key in seen_weeks:
                continue
            seen_weeks.add(key)
            sampled.append(date)
        return list(reversed(sampled))

    def _composite_at(
        self,
        as_of: datetime,
        history_map: dict[str, list[dict[str, Any]]],
    ) -> dict[str, Any]:
        components = []
        for definition in DLI_INDICATORS:
            points = [
                (item["timestamp"], float(item["value"]))
                for item in history_map.get(definition.id, [])
                if item["timestamp"] <= as_of and math.isfinite(float(item["value"]))
            ]
            score_payload = self._indicator_score(definition, points, as_of)
            components.append(score_payload)

        valid = [item for item in components if item["score"] is not None]
        if not valid:
            return {"score": None, "coverage": 0.0, "components": components}

        total_available_group_weight = sum(
            GROUP_WEIGHTS[group]
            for group in GROUP_WEIGHTS
            if any(item["group"] == group for item in valid)
        )
        score = 0.0
        effective_weights: dict[str, float] = {}
        for group, group_weight in GROUP_WEIGHTS.items():
            group_items = [item for item in valid if item["group"] == group]
            if not group_items or total_available_group_weight <= 0:
                continue
            effective_group_weight = group_weight / total_available_group_weight * 100.0
            group_raw_weight = sum(item["weight"] for item in group_items)
            if group_raw_weight <= 0:
                continue
            for item in group_items:
                effective_weight = effective_group_weight * item["weight"] / group_raw_weight
                effective_weights[item["indicator_id"]] = effective_weight
                score += item["score"] * effective_weight / 100.0

        for item in components:
            effective_weight = effective_weights.get(item["indicator_id"], 0.0)
            item["effective_weight"] = round(effective_weight, 4)
            item["contribution"] = None if item["score"] is None else round((item["score"] - 50.0) * effective_weight / 100.0, 4)

        original_available_weight = sum(item["weight"] for item in valid)
        return {
            "score": score,
            "coverage": round(original_available_weight / sum(GROUP_WEIGHTS.values()) * 100.0, 2),
            "components": sorted(
                components,
                key=lambda item: abs(item["contribution"] or 0.0),
                reverse=True,
            ),
        }

    def _indicator_score(
        self,
        definition: DliIndicatorDefinition,
        points: list[tuple[datetime, float]],
        as_of: datetime,
    ) -> dict[str, Any]:
        base = {
            "indicator_id": definition.id,
            "name": definition.label,
            "short_label": definition.short_label,
            "group": definition.group,
            "group_label": definition.group_label,
            "weight": definition.weight,
            "effective_weight": 0.0,
            "polarity": definition.polarity,
            "current_value": None,
            "score": None,
            "z_score": None,
            "percentile": None,
            "contribution": None,
            "change_pct": None,
            "last_updated": None,
            "missing_reason": None,
        }
        if len(points) < 3:
            base["missing_reason"] = "insufficient_history"
            return base

        points = sorted(points, key=lambda item: item[0])
        current_date, current_value = points[-1]
        window_start = as_of - timedelta(days=3650)
        sample = [value for date, value in points if date >= window_start]
        if len(sample) < 3:
            base["missing_reason"] = "insufficient_window"
            return base

        z_score = self._support_z_score(current_value, sample, definition.polarity)
        percentile = self._support_percentile(current_value, sample, definition.polarity)
        robust_score = self._z_to_score(z_score)
        robust_weight = 0.7 if len(sample) >= 60 else 0.5
        score = robust_score * robust_weight + percentile * (1.0 - robust_weight)
        change_pct = self._change_pct(points)
        base.update(
            {
                "current_value": current_value,
                "score": round(max(0.0, min(100.0, score)), 4),
                "z_score": round(z_score, 4),
                "percentile": round(percentile, 4),
                "change_pct": None if change_pct is None else round(change_pct, 4),
                "last_updated": current_date.isoformat(),
            }
        )
        return base

    @staticmethod
    def _support_z_score(current: float, sample: list[float], polarity: str) -> float:
        center = median(sample)
        deviations = [abs(value - center) for value in sample]
        mad = median(deviations)
        denom = 1.4826 * mad
        if denom <= 0:
            denom = pstdev(sample) if len(sample) > 1 else 0.0
        if denom <= 0:
            return 0.0
        z_score = (current - center) / denom
        if polarity == "lower_supports":
            z_score *= -1.0
        return max(-4.0, min(4.0, z_score))

    @staticmethod
    def _support_percentile(current: float, sample: list[float], polarity: str) -> float:
        if len(sample) <= 1:
            return 50.0
        below = sum(1 for value in sample if value < current)
        equal = sum(1 for value in sample if value == current)
        percentile = ((below + 0.5 * equal) / len(sample)) * 100.0
        if polarity == "lower_supports":
            percentile = 100.0 - percentile
        return max(0.0, min(100.0, percentile))

    @staticmethod
    def _z_to_score(z_score: float) -> float:
        return 0.5 * (1.0 + math.erf(z_score / (1.35 * math.sqrt(2.0)))) * 100.0

    @staticmethod
    def _change_pct(points: list[tuple[datetime, float]]) -> float | None:
        if len(points) < 2:
            return None
        current_date, current = points[-1]
        target_date = current_date - timedelta(days=30)
        previous = None
        for date, value in points:
            if date <= target_date:
                previous = value
            else:
                break
        if previous is None:
            previous = points[0][1]
        if previous == 0:
            return None
        return ((current - previous) / abs(previous)) * 100.0

    @staticmethod
    def _thresholds(series: list[dict[str, Any]]) -> dict[str, Any]:
        values = sorted(item["score"] for item in series if item.get("score") is not None)
        if len(values) < 20:
            return {"p20": 43.0, "p50": 50.0, "p80": 68.0, "source": "fallback", "sample_size": len(values)}
        return {
            "p20": round(DliLiquidityService._quantile(values, 0.2), 2),
            "p50": round(DliLiquidityService._quantile(values, 0.5), 2),
            "p80": round(DliLiquidityService._quantile(values, 0.8), 2),
            "source": "rolling_5y",
            "sample_size": len(values),
        }

    @staticmethod
    def _quantile(values: list[float], q: float) -> float:
        if not values:
            return 50.0
        position = (len(values) - 1) * q
        lower = math.floor(position)
        upper = math.ceil(position)
        if lower == upper:
            return values[int(position)]
        weight = position - lower
        return values[lower] * (1.0 - weight) + values[upper] * weight

    @staticmethod
    def _score_percentile(score: float | None, values: list[float]) -> float | None:
        if score is None or not values:
            return None
        below = sum(1 for value in values if value < score)
        equal = sum(1 for value in values if value == score)
        percentile = ((below + 0.5 * equal) / len(values)) * 100.0
        return max(0.0, min(100.0, percentile))

    @staticmethod
    def _state(score: float | None, p20: float, p50: float, p80: float) -> tuple[str, str]:
        if score is None:
            return "等待数据", "neutral"
        if score >= p80:
            return "流动性宽松", "support"
        if score <= p20:
            return "流动性收紧", "pressure"
        if score < p50:
            return "中性偏紧", "pressure"
        return "中性偏松", "support"

    @staticmethod
    def _latest_update(history_map: dict[str, list[dict[str, Any]]]) -> datetime | None:
        dates = [
            item["timestamp"]
            for rows in history_map.values()
            for item in rows
            if item.get("timestamp") is not None
        ]
        return max(dates) if dates else None

    @staticmethod
    def _alerts(components: list[dict[str, Any]]) -> list[str]:
        valid = [item for item in components if item.get("score") is not None]
        if not valid:
            return ["等待后台采集宏观指标后生成评分。"]
        alerts = []
        for item in valid[:4]:
            direction = "支撑" if item["score"] >= 50 else "压制"
            change = "--" if item["change_pct"] is None else f"{item['change_pct']:+.2f}%"
            contribution = item.get("contribution") or 0.0
            display_name = item.get("name") or item.get("short_label") or item["indicator_id"]
            alerts.append(
                f"{display_name}当前对风险资产形成{direction}，DLI 贡献 {contribution:+.2f}，30 日变化 {change}。"
            )
        return alerts
