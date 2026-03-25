from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.infra.db.database import session_scope
from app.infra.db.schema import MarketIndicatorMeta, MarketIndicatorData


class IndicatorService:
    def get_indicators(self, category: Optional[str], days: int) -> List[Dict[str, Any]]:
        cutoff_date = datetime.now() - timedelta(days=days)

        with session_scope() as session:
            result: List[Dict[str, Any]] = []

            meta_query = session.query(MarketIndicatorMeta).filter(MarketIndicatorMeta.is_active == 1)
            if category:
                meta_query = meta_query.filter(MarketIndicatorMeta.category == category)
            metas = meta_query.all()

            meta_ids = [meta.id for meta in metas]
            all_data_points = []
            if meta_ids:
                all_data_points = (
                    session.query(MarketIndicatorData)
                    .filter(
                        MarketIndicatorData.indicator_id.in_(meta_ids),
                        MarketIndicatorData.timestamp >= cutoff_date,
                    )
                    .order_by(
                        MarketIndicatorData.indicator_id.asc(),
                        MarketIndicatorData.timestamp.asc(),
                    )
                    .all()
                )

            grouped = defaultdict(list)
            for dp in all_data_points:
                grouped[dp.indicator_id].append(dp)

            for meta in metas:
                history = [
                    {"date": dp.timestamp.isoformat(), "value": dp.value}
                    for dp in grouped.get(meta.id, [])
                ]
                result.append(
                    {
                        "indicator_id": meta.id,
                        "name": meta.name,
                        "category": meta.category,
                        "unit": meta.unit,
                        "current_value": history[-1]["value"] if history else None,
                        "last_updated": history[-1]["date"] if history else None,
                        "history": history,
                    }
                )

            return result
