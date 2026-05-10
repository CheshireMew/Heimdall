import asyncio
import logging

from app.application.indicators.ports import DliCacheInvalidator, IndicatorProvider, MarketIndicatorWriter

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
    "TGA":              ("Treasury General Account", "Macro", "M USD"),
    "ONRRP":            ("Overnight Reverse Repo", "Macro", "B USD"),
    "SOFR":             ("Secured Overnight Financing Rate", "Macro", "%"),
    "US02Y":            ("US 2Y Treasury Yield",   "Macro", "%"),
    "M2":               ("M2 Money Supply",        "Macro", "B USD"),
    "VIX":              ("CBOE Volatility Index",  "Macro", ""),
    "DXY":              ("Trade Weighted U.S. Dollar Index", "Macro", ""),
    "WTI":              ("WTI Crude Oil",          "Macro", "USD"),
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
            self.repository.upsert_points(data_points, INDICATOR_META)
        except Exception as e:
            logger.error(f"Failed to save Market Indicator to DB: {e}")
            raise

