from __future__ import annotations

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.application.indicators.market_cron import MarketIndicatorCronJob
from app.infra.executor import run_background
from app.services.persistence_ports import DataRetentionCleanup, IndicatorRepositoryPort
from app.services.market.dli_cache import DliLiquidityCache
from config import settings

logger = logging.getLogger(__name__)


class MarketSchedulerRuntime:
    def __init__(
        self,
        *,
        indicator_repository: IndicatorRepositoryPort,
        cleanup_old_data: DataRetentionCleanup,
        dli_cache: DliLiquidityCache | None = None,
    ) -> None:
        self._cleanup_old_data_callback = cleanup_old_data
        self.scheduler = AsyncIOScheduler()
        self._job = MarketIndicatorCronJob(
            repository=indicator_repository,
            providers=_build_indicator_providers(),
            dli_cache=dli_cache,
        )

    def start(self) -> None:
        if self.scheduler.running:
            logger.info("Market Indicator Scheduler already running, skip duplicate start.")
            return

        self.scheduler.add_job(
            self._run_market_indicator_job,
            'interval',
            hours=settings.MARKET_CRON_INTERVAL_HOURS,
            id='fetch_market_indicators',
            replace_existing=True,
        )

        self.scheduler.add_job(
            self._cleanup_old_data,
            'interval',
            hours=24,
            id='data_retention_cleanup',
            replace_existing=True,
        )

        self.scheduler.start()
        logger.info(f"Market Indicator Scheduler Started. Fetching every {settings.MARKET_CRON_INTERVAL_HOURS} hours.")

    async def _run_market_indicator_job(self) -> None:
        await run_background(lambda: asyncio.run(self._job.run()))

    async def _cleanup_old_data(self) -> None:
        await run_background(self._cleanup_old_data_callback)

    async def shutdown(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown()


def _build_indicator_providers():
    from app.services.indicators.crypto_gold_provider import CryptoGoldProvider
    from app.services.indicators.macro_provider_v2 import MacroProviderV2 as MacroProvider
    from app.services.indicators.onchain_provider import OnchainProvider
    from app.services.indicators.sentiment_provider import SentimentProvider
    from app.services.indicators.tech_calculator import TechCalculatorProvider

    return [
        MacroProvider(),
        OnchainProvider(),
        SentimentProvider(),
        TechCalculatorProvider(),
        CryptoGoldProvider(),
    ]
