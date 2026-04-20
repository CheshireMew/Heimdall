from __future__ import annotations

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.infra.db import DatabaseRuntime
from app.services.data_retention import cleanup_old_data
from app.services.market_cron import MarketIndicatorCronJob
from config import settings

logger = logging.getLogger(__name__)


class MarketSchedulerRuntime:
    def __init__(self, *, database_runtime: DatabaseRuntime) -> None:
        self.database_runtime = database_runtime
        self.scheduler = AsyncIOScheduler()
        self._deferred_tasks: set[asyncio.Task[None]] = set()
        self._job = MarketIndicatorCronJob(database_runtime=database_runtime)

    def _schedule_deferred_start(self, callback, *, delay_seconds: float) -> None:
        async def _runner() -> None:
            await asyncio.sleep(delay_seconds)
            await callback()

        task = asyncio.create_task(_runner())
        self._deferred_tasks.add(task)
        task.add_done_callback(self._deferred_tasks.discard)

    def start(self) -> None:
        if self.scheduler.running:
            logger.info("Market Indicator Scheduler already running, skip duplicate start.")
            return

        # 避免首轮后台任务与 API 启动争抢导入和网络资源。
        self._schedule_deferred_start(self._job.run, delay_seconds=15.0)
        self.scheduler.add_job(
            self._job.run,
            'interval',
            hours=settings.MARKET_CRON_INTERVAL_HOURS,
            id='fetch_market_indicators',
            replace_existing=True,
        )

        self._schedule_deferred_start(self._cleanup_old_data, delay_seconds=30.0)
        self.scheduler.add_job(
            self._cleanup_old_data,
            'interval',
            hours=24,
            id='data_retention_cleanup',
            replace_existing=True,
        )

        self.scheduler.start()
        logger.info(f"Market Indicator Scheduler Started. Fetching every {settings.MARKET_CRON_INTERVAL_HOURS} hours.")

    async def _cleanup_old_data(self) -> None:
        await cleanup_old_data(self.database_runtime)

    async def shutdown(self) -> None:
        if self._deferred_tasks:
            tasks = list(self._deferred_tasks)
            self._deferred_tasks.clear()
            for task in tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

        if self.scheduler.running:
            self.scheduler.shutdown()
