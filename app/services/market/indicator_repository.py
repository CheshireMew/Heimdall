from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

from app.infra.db.database import DatabaseRuntime
from app.infra.db.schema import MarketIndicatorData, MarketIndicatorMeta


class MarketIndicatorRepository:
    def __init__(self, *, database_runtime: DatabaseRuntime) -> None:
        self.database_runtime = database_runtime

    def list_active_meta(self, category: str | None = None) -> list[dict[str, Any]]:
        with self.database_runtime.session_scope() as session:
            query = session.query(MarketIndicatorMeta).filter(MarketIndicatorMeta.is_active == 1)
            if category:
                query = query.filter(MarketIndicatorMeta.category == category)
            rows = query.order_by(MarketIndicatorMeta.category.asc(), MarketIndicatorMeta.name.asc()).all()
            return [
                {
                    "id": row.id,
                    "name": row.name,
                    "category": row.category,
                    "unit": row.unit,
                    "frequency": row.frequency,
                    "description": row.description,
                }
                for row in rows
            ]

    def get_history_points(
        self,
        indicator_ids: list[str],
        *,
        start_date: datetime | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        if not indicator_ids:
            return {}

        with self.database_runtime.session_scope() as session:
            query = session.query(MarketIndicatorData).filter(MarketIndicatorData.indicator_id.in_(indicator_ids))
            if start_date:
                query = query.filter(MarketIndicatorData.timestamp >= start_date)
            rows = query.order_by(
                MarketIndicatorData.indicator_id.asc(),
                MarketIndicatorData.timestamp.asc(),
            ).all()
            grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for row in rows:
                grouped[row.indicator_id].append(
                    {
                        "date": row.timestamp.isoformat(),
                        "timestamp": row.timestamp,
                        "value": row.value,
                    }
                )
            return grouped
