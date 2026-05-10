from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from app.infra.persistence.market.indicator_repository import MarketIndicatorRepository
from app.services.market.dli_service import DliLiquidityService


class IndicatorService:
    def __init__(self, repository: MarketIndicatorRepository) -> None:
        self.repository = repository
        self.dli_service = DliLiquidityService(repository)

    def get_indicators(
        self,
        category: str | None,
        days: int,
    ) -> list[dict[str, Any]]:
        cutoff_date = datetime.now() - timedelta(days=days)
        metas = self.repository.list_active_meta(category)
        history_map = self.repository.get_history_points([meta["id"] for meta in metas], start_date=cutoff_date)

        result: list[dict[str, Any]] = []
        for meta in metas:
            history = [
                {"date": item["date"], "value": item["value"]}
                for item in history_map.get(meta["id"], [])
            ]
            result.append(
                {
                    "indicator_id": meta["id"],
                    "name": meta["name"],
                    "category": meta["category"],
                    "unit": meta["unit"],
                    "current_value": history[-1]["value"] if history else None,
                    "last_updated": history[-1]["date"] if history else None,
                    "history": history,
                }
            )
        return result

    def get_dli_liquidity(self, days: int) -> dict[str, Any]:
        return self.dli_service.build(days=days)
