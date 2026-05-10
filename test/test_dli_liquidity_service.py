from __future__ import annotations

from datetime import datetime, timedelta

from app.application.indicators.market_cron import INDICATOR_META
from app.infra.persistence.market.indicator_repository import MarketIndicatorRepository
from app.services.market.dli_cache import DliLiquidityCache
from app.services.market.dli_service import DLI_INDICATORS, DliLiquidityService
from app.services.market.indicator_service import IndicatorService


def test_dli_liquidity_service_builds_weighted_robust_score(installed_database_runtime):
    repository = MarketIndicatorRepository(database_runtime=installed_database_runtime)
    now = datetime.now().replace(microsecond=0)
    points = []
    for definition in DLI_INDICATORS:
        for index in range(90):
            timestamp = now - timedelta(days=89 - index)
            value = 100.0 + index if definition.polarity == "higher_supports" else 200.0 - index
            points.append({"indicator_id": definition.id, "timestamp": timestamp, "value": value})
    repository.upsert_points(points, INDICATOR_META)

    payload = DliLiquidityService(repository).build(days=90)

    assert payload["score"] is not None
    assert payload["score"] > 80
    assert payload["state"] in {"中性", "流动性宽松"}
    assert payload["coverage"] == 100.0
    assert payload["thresholds"]["sample_size"] > 0
    assert round(sum(item["effective_weight"] for item in payload["components"]), 6) == 100
    assert {item["indicator_id"] for item in payload["components"]} == {item.id for item in DLI_INDICATORS}
    assert payload["alerts"]


def test_dli_liquidity_service_reports_missing_coverage(installed_database_runtime):
    repository = MarketIndicatorRepository(database_runtime=installed_database_runtime)
    now = datetime.now().replace(microsecond=0)
    points = [
        {"indicator_id": "FED_BALANCE", "timestamp": now - timedelta(days=2), "value": 100.0},
        {"indicator_id": "FED_BALANCE", "timestamp": now - timedelta(days=1), "value": 101.0},
        {"indicator_id": "FED_BALANCE", "timestamp": now, "value": 102.0},
    ]
    repository.upsert_points(points, INDICATOR_META)

    payload = DliLiquidityService(repository).build(days=30)

    assert payload["score"] is not None
    assert payload["coverage"] == 30.0
    missing = [item for item in payload["components"] if item["score"] is None]
    assert missing
    assert all(item["missing_reason"] for item in missing)


class CountingIndicatorRepository:
    def __init__(self) -> None:
        self.history_reads = 0

    def get_history_points(self, indicator_ids, *, start_date=None):
        self.history_reads += 1
        return {}

    def list_active_meta(self, category=None):
        return []


def test_indicator_service_caches_dli_payload_until_invalidated():
    repository = CountingIndicatorRepository()
    cache = DliLiquidityCache(ttl_seconds=60)
    service = IndicatorService(repository, dli_cache=cache)

    first = service.get_dli_liquidity(days=30)
    second = service.get_dli_liquidity(days=30)

    assert first == second
    assert repository.history_reads == 1

    cache.invalidate_all()
    service.get_dli_liquidity(days=30)

    assert repository.history_reads == 2
