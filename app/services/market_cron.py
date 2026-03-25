import logging
import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.infra.db.database import init_db, session_scope
from app.infra.db.schema import MarketIndicatorMeta, MarketIndicatorData
from app.services.indicators.macro_provider_v2 import MacroProviderV2 as MacroProvider
from app.services.indicators.onchain_provider import OnchainProvider
from app.services.indicators.sentiment_provider import SentimentProvider
from app.services.indicators.tech_calculator import TechCalculatorProvider
from app.services.indicators.crypto_gold_provider import CryptoGoldProvider
from config import settings
from app.services.data_retention import cleanup_old_data

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 指标元数据配置: indicator_id -> (display_name, category, unit)
INDICATOR_META = {
    # Macro
    "US10Y":            ("US 10Y Treasury Yield", "Macro", "%"),
    "NASDAQ":           ("NASDAQ Composite",      "Macro", ""),
    "GOLD":             ("Gold Spot Price",        "Macro", "USD"),
    "HY_SPREAD":        ("High Yield Spread",     "Macro", "%"),
    "FED_RATE":         ("Fed Funds Rate",         "Macro", "%"),
    "FED_BALANCE":      ("Fed Balance Sheet",      "Macro", "M USD"),
    # Onchain
    "HASHRATE":         ("BTC Hashrate",           "Onchain", "EH/s"),
    "DIFFICULTY":       ("Mining Difficulty",       "Onchain", "T"),
    "STABLECOIN_CAP":   ("Stablecoin Market Cap",  "Onchain", "USD"),
    "USDT_CAP":         ("USDT Market Cap",        "Onchain", "USD"),
    "USDC_CAP":         ("USDC Market Cap",        "Onchain", "USD"),
    # Sentiment
    "FEAR_GREED":       ("Fear & Greed Index",     "Sentiment", ""),
    "GOOGLE_TRENDS_BTC":("Google Trends: BTC",     "Sentiment", ""),
    # Tech
    "200WMA":           ("200-Week Moving Avg",    "Tech", "USD"),
    "S19_BREAKEVEN":    ("S19 Miner Breakeven",    "Tech", "USD"),
    "S21_BREAKEVEN":    ("S21 Miner Breakeven",    "Tech", "USD"),
    "S23_BREAKEVEN":    ("S23 Miner Breakeven",    "Tech", "USD"),
    "BTC_DRAWDOWN":     ("BTC Drawdown from ATH",  "Tech", "%"),
}

class MarketIndicatorCronJob:
    """市场核心指标定时汇聚作业类"""

    def __init__(self):
        self.providers = [
            MacroProvider(),
            OnchainProvider(),
            SentimentProvider(),
            TechCalculatorProvider(),
            CryptoGoldProvider(),
        ]

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

        logger.info(f"MarketIndicator Cron Job Complete. Inserted {len(all_data_points)} records.")

    def _save_to_db(self, data_points: list):
        """将获取到的指标数据点插入数据表"""
        with session_scope() as db:
            try:
                 for pt in data_points:
                     ind_id = pt["indicator_id"]
                     meta_info = INDICATOR_META.get(ind_id, (ind_id.replace("_", " ").title(), "General", ""))
                     display_name, category, unit = meta_info

                     meta = db.query(MarketIndicatorMeta).filter_by(id=ind_id).first()
                     if not meta:
                          new_meta = MarketIndicatorMeta(
                               id=ind_id,
                               name=display_name,
                               category=category,
                               unit=unit,
                          )
                          db.add(new_meta)
                          db.flush()
                     elif meta.category == "General":
                          # Fix existing records with wrong category
                          meta.category = category
                          meta.name = display_name
                          meta.unit = unit
                          db.flush()

                 for pt in data_points:
                     exists = db.query(MarketIndicatorData).filter(
                         MarketIndicatorData.indicator_id == pt["indicator_id"],
                         MarketIndicatorData.timestamp == pt["timestamp"]
                     ).first()

                     if not exists:
                         entry = MarketIndicatorData(
                             indicator_id=pt["indicator_id"],
                             timestamp=pt["timestamp"],
                             value=pt["value"]
                         )
                         db.add(entry)
            except Exception as e:
                 logger.error(f"Failed to save Market Indicator to DB: {e}")
                 raise

# 全局单例调度器
scheduler = AsyncIOScheduler()

def start_scheduler():
    """启动全局异步定时器"""
    job = MarketIndicatorCronJob()

    # 模拟第一次立刻执行
    asyncio.create_task(job.run())

    # 设定每 4 小时执行一次数据汇总汇聚
    scheduler.add_job(job.run, 'interval', hours=settings.MARKET_CRON_INTERVAL_HOURS, id='fetch_market_indicators', replace_existing=True)

    # 数据保留清理: 每 24 小时执行一次
    asyncio.create_task(cleanup_old_data())
    scheduler.add_job(cleanup_old_data, 'interval', hours=24, id='data_retention_cleanup', replace_existing=True)

    scheduler.start()
    logger.info(f"Market Indicator Scheduler Started. Fetching every {settings.MARKET_CRON_INTERVAL_HOURS} hours.")

if __name__ == "__main__":
    init_db()
    asyncio.run(MarketIndicatorCronJob().run())
