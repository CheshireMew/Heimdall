from __future__ import annotations

import math
from typing import Any

from .binance_numbers import safe_float, to_int
from .binance_web3_support import chain_platform, ratio_score, token_key


class BinanceWeb3HeatRankComposer:
    def compose(
        self,
        *,
        chain_id: str,
        top_search: list[dict[str, Any]],
        trending: list[dict[str, Any]],
        volume_rank: list[dict[str, Any]],
        tx_rank: list[dict[str, Any]],
        unique_rank: list[dict[str, Any]],
        social_hype: list[dict[str, Any]],
        smart_money: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        tokens: dict[str, dict[str, Any]] = {}

        def ensure(item: dict[str, Any]) -> dict[str, Any] | None:
            key = token_key(item)
            if not key:
                return None
            current = tokens.setdefault(
                key,
                {
                    "symbol": item.get("symbol"),
                    "chain_id": item.get("chain_id") or chain_id,
                    "contract_address": item.get("contract_address"),
                    "icon_url": item.get("icon_url") or item.get("logo_url"),
                    "platform": chain_platform(item.get("chain_id") or chain_id),
                    "ranks": {},
                    "metrics": {},
                    "audit_info": {},
                },
            )
            self._merge_token_base(current, item)
            return current

        for source_name, rows in [
            ("top_search", top_search),
            ("trending", trending),
            ("volume", volume_rank),
            ("transactions", tx_rank),
            ("unique_traders", unique_rank),
        ]:
            for index, item in enumerate(rows, start=1):
                token = ensure(item)
                if token is None:
                    continue
                token["ranks"][source_name] = index

        max_social_hype = max([safe_float(item.get("social_hype")) or 0 for item in social_hype] or [0])
        for item in social_hype:
            token = ensure(item)
            if token is None:
                continue
            social_value = safe_float(item.get("social_hype"))
            token["metrics"]["social_hype"] = social_value
            token["sentiment"] = item.get("sentiment")
            token["summary"] = item.get("summary")
            token["ranks"]["social_hype"] = len(token["ranks"]) + 1
            token["metrics"]["social_hype_normalized"] = ratio_score(social_value, max_social_hype)

        max_inflow = max([safe_float(item.get("inflow")) or 0 for item in smart_money] or [0])
        for index, item in enumerate(smart_money, start=1):
            token = ensure(item)
            if token is None:
                continue
            inflow = safe_float(item.get("inflow"))
            token["ranks"]["smart_money"] = index
            token["metrics"]["smart_money_inflow"] = inflow
            token["metrics"]["smart_money_traders"] = item.get("traders")
            token["metrics"]["smart_money_inflow_normalized"] = ratio_score(inflow, max_inflow)
            if item.get("risk_level") is not None:
                token["metrics"]["smart_money_risk_level"] = item.get("risk_level")

        scored = [self._score_token(item) for item in tokens.values()]
        scored.sort(key=lambda item: (-item["heat_score"], item.get("symbol") or ""))
        for index, item in enumerate(scored, start=1):
            item["rank"] = index
        return scored

    def _merge_token_base(self, current: dict[str, Any], item: dict[str, Any]) -> None:
        for target, source in [
            ("symbol", "symbol"),
            ("chain_id", "chain_id"),
            ("contract_address", "contract_address"),
            ("icon_url", "icon_url"),
        ]:
            if not current.get(target) and item.get(source):
                current[target] = item.get(source)
        if not current.get("icon_url") and item.get("logo_url"):
            current["icon_url"] = item.get("logo_url")
        for key in [
            "price",
            "market_cap",
            "liquidity",
            "holders",
            "launch_time",
            "percent_change_1h",
            "percent_change_24h",
            "volume_1h",
            "volume_4h",
            "volume_24h",
            "count_1h",
            "count_24h",
            "unique_trader_1h",
            "unique_trader_24h",
            "kyc_holders",
        ]:
            if current["metrics"].get(key) in (None, "") and item.get(key) not in (None, ""):
                current["metrics"][key] = item.get(key)
        if item.get("audit_info"):
            current["audit_info"] = item.get("audit_info")

    def _score_token(self, item: dict[str, Any]) -> dict[str, Any]:
        ranks = item["ranks"]
        metrics = item["metrics"]
        components = {
            "top_search": self._rank_component(ranks.get("top_search"), 100, 20),
            "trending": self._rank_component(ranks.get("trending"), 100, 20),
            "social_hype": (metrics.get("social_hype_normalized") or 0) * 15,
            "volume_growth": self._growth_component(metrics.get("volume_1h"), metrics.get("volume_24h"), 15),
            "transaction_growth": self._growth_component(metrics.get("count_1h"), metrics.get("count_24h"), 15),
            "unique_traders": self._rank_component(ranks.get("unique_traders"), 100, 10),
            "smart_money": (metrics.get("smart_money_inflow_normalized") or 0) * 15,
        }
        penalties = {
            "low_liquidity": self._liquidity_penalty(metrics.get("liquidity")),
            "contract_risk": self._contract_risk_penalty(item),
        }
        raw_score = sum(components.values()) - sum(penalties.values())
        return {
            **item,
            "heat_score": round(max(0, min(100, raw_score)), 2),
            "components": {key: round(value, 2) for key, value in components.items()},
            "penalties": {key: round(value, 2) for key, value in penalties.items()},
        }

    def _rank_component(self, rank: Any, total: int, weight: float) -> float:
        value = to_int(rank)
        if value is None or value <= 0:
            return 0
        return max(0, (total - value + 1) / total) * weight

    def _growth_component(self, recent: Any, total_24h: Any, weight: float) -> float:
        recent_value = safe_float(recent)
        day_value = safe_float(total_24h)
        if recent_value is None or day_value is None or recent_value <= 0 or day_value <= 0:
            return 0
        hourly_average = max(day_value / 24, 1e-12)
        ratio = recent_value / hourly_average
        return min(1, math.log1p(ratio) / math.log1p(8)) * weight

    def _liquidity_penalty(self, liquidity: Any) -> float:
        value = safe_float(liquidity)
        if value is None:
            return 8
        if value < 10_000:
            return 28
        if value < 50_000:
            return 18
        if value < 100_000:
            return 10
        if value < 250_000:
            return 4
        return 0

    def _contract_risk_penalty(self, item: dict[str, Any]) -> float:
        audit_info = item.get("audit_info") or {}
        metrics = item.get("metrics") or {}
        risk_level = to_int(audit_info.get("riskLevel"))
        if risk_level is None:
            risk_level = to_int(metrics.get("smart_money_risk_level"))
        risk_num = to_int(audit_info.get("riskNum")) or 0
        caution_num = to_int(audit_info.get("cautionNum")) or 0
        penalty = min(24, risk_num * 5 + caution_num * 1.5)
        if risk_level is not None:
            if risk_level >= 4:
                penalty += 30
            elif risk_level >= 2:
                penalty += 14
        return penalty
