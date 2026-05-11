import asyncio
import logging

from app.application.indicators.ports import DliCacheInvalidator, IndicatorProvider, MarketIndicatorWriter
from app.domain.market.dli_catalog import market_indicator_meta_catalog

logger = logging.getLogger(__name__)

class MarketIndicatorCronJob:
    """市场核心指标定时汇聚作业类"""

    def __init__(
        self,
        *,
        repository: MarketIndicatorWriter,
        providers: list[IndicatorProvider],
        dli_cache: DliCacheInvalidator | None = None,
    ):
        self.repository = repository
        self.providers = providers
        self.dli_cache = dli_cache

    async def run(self):
        """执行聚合逻辑"""
        logger.info("Starting MarketIndicator Cron Job...")

        all_data_points = []
        for provider in self.providers:
            try:
                points = await provider.fetch_data()
                all_data_points.extend(points)
            except Exception as e:
                logger.error(f"Error fetching from provider {provider.__class__.__name__}: {e}")

        if all_data_points:
            self._save_to_db(all_data_points)
            if self.dli_cache is not None:
                self.dli_cache.invalidate_all()

        logger.info(f"MarketIndicator Cron Job Complete. Inserted {len(all_data_points)} records.")

    def _save_to_db(self, data_points: list):
        """将获取到的指标数据点插入数据表"""
        try:
            self.repository.upsert_points(data_points, market_indicator_meta_catalog())
        except Exception as e:
            logger.error(f"Failed to save Market Indicator to DB: {e}")
            raise

