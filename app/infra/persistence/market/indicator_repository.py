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

    def upsert_points(self, data_points: list[dict[str, Any]], meta_catalog: dict[str, tuple[str, str, str]]) -> None:
        with self.database_runtime.session_scope() as session:
            ensured_meta_ids: set[str] = set()
            for point in data_points:
                indicator_id = point["indicator_id"]
                if indicator_id in ensured_meta_ids:
                    continue
                display_name, category, unit = meta_catalog.get(
                    indicator_id,
                    (indicator_id.replace("_", " ").title(), "General", ""),
                )
                meta = session.query(MarketIndicatorMeta).filter_by(id=indicator_id).first()
                if not meta:
                    session.add(
                        MarketIndicatorMeta(
                            id=indicator_id,
                            name=display_name,
                            category=category,
                            unit=unit,
                        )
                    )
                    session.flush()
                elif meta.category == "General":
                    meta.category = category
                    meta.name = display_name
                    meta.unit = unit
                    session.flush()
                ensured_meta_ids.add(indicator_id)

            for point in data_points:
                exists = (
                    session.query(MarketIndicatorData)
                    .filter(
                        MarketIndicatorData.indicator_id == point["indicator_id"],
                        MarketIndicatorData.timestamp == point["timestamp"],
                    )
                    .first()
                )
                if not exists:
                    session.add(
                        MarketIndicatorData(
                            indicator_id=point["indicator_id"],
                            timestamp=point["timestamp"],
                            value=point["value"],
                        )
                    )
