import asyncio
import logging

from app.infra.db.database import session_scope
from app.infra.db.schema_runtime import init_db
from app.infra.db.schema import MarketIndicatorMeta, MarketIndicatorData

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
        self.providers = None

    def _get_providers(self):
        if self.providers is None:
            from app.services.indicators.crypto_gold_provider import CryptoGoldProvider
            from app.services.indicators.macro_provider_v2 import MacroProviderV2 as MacroProvider
            from app.services.indicators.onchain_provider import OnchainProvider
            from app.services.indicators.sentiment_provider import SentimentProvider
            from app.services.indicators.tech_calculator import TechCalculatorProvider

            self.providers = [
                MacroProvider(),
                OnchainProvider(),
                SentimentProvider(),
                TechCalculatorProvider(),
                CryptoGoldProvider(),
            ]
        return self.providers

    async def run(self):
        """执行聚合逻辑"""
        logger.info("Starting MarketIndicator Cron Job...")

        all_data_points = []
        for provider in self._get_providers():
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

if __name__ == "__main__":
    init_db()
    asyncio.run(MarketIndicatorCronJob().run())
