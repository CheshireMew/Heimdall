import asyncio

import pytest

from app.services.market_scheduler_runtime import MarketSchedulerRuntime


@pytest.mark.asyncio
async def test_scheduler_start_registers_jobs_without_immediate_work(monkeypatch):
    runtime = MarketSchedulerRuntime(indicator_repository=object(), cleanup_old_data=lambda: None)
    calls: list[str] = []

    async def record_indicator_job():
        calls.append("indicator")

    async def record_cleanup_job():
        calls.append("cleanup")

    monkeypatch.setattr(runtime, "_run_market_indicator_job", record_indicator_job)
    monkeypatch.setattr(runtime, "_cleanup_old_data", record_cleanup_job)

    runtime.start()
    await asyncio.sleep(0)

    try:
        assert calls == []
        assert {job.id for job in runtime.scheduler.get_jobs()} == {
            "fetch_market_indicators",
            "data_retention_cleanup",
        }
    finally:
        await runtime.shutdown()
