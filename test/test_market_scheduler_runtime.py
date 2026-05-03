import asyncio
import logging

import pytest

from app.services.market_scheduler_runtime import MarketSchedulerRuntime


@pytest.mark.asyncio
async def test_deferred_scheduler_task_logs_and_consumes_callback_exception(caplog):
    runtime = MarketSchedulerRuntime(database_runtime=object())

    async def fail():
        raise RuntimeError("boom")

    with caplog.at_level(logging.ERROR):
        task = runtime._schedule_deferred_start(fail, delay_seconds=0, task_name="test_task")
        await task
        await asyncio.sleep(0)

    assert not runtime._deferred_tasks
    assert "Deferred scheduler task failed: test_task" in caplog.text
