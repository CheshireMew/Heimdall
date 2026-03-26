from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BASE_DIR / "data" / "heimdall.db"


def _default_runtime_root() -> Path:
    local_appdata = os.getenv("LOCALAPPDATA")
    if local_appdata:
        return Path(local_appdata) / "Heimdall"
    return Path.home() / ".heimdall"


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    EXCHANGE_ID: str = "binance"
    SYMBOLS: list[str] = Field(default_factory=lambda: ["BTC/USDT", "ETH/USDT", "SOL/USDT", "DOGE/USDT"])
    TIMEFRAME: str = "1h"
    LIMIT: int = 1000

    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    AI_MODEL: str = "deepseek-chat"

    FRED_API_KEY: str = ""
    ALPHA_VANTAGE_API_KEY: str = ""

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    DATABASE_URL: str = Field(default_factory=lambda: f"sqlite:///{DEFAULT_DB_PATH}")

    EMA_PERIOD: int = 20
    RSI_PERIOD: int = 14
    MACD_FAST: int = 12
    MACD_SLOW: int = 26
    MACD_SIGNAL: int = 9

    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:4173",
            "http://127.0.0.1:4173",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ]
    )

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    FRONTEND_DEV_PORT: int = 4173

    RATE_LIMIT_DEFAULT: str = "60/minute"
    RATE_LIMIT_HEAVY: str = "10/minute"

    EXCHANGE_MAX_RETRIES: int = 3
    EXCHANGE_RETRY_DELAY: int = 2
    EXCHANGE_TASK_TIMEOUT: int = 90
    EXCHANGE_FETCH_LIMIT: int = 1000

    REDIS_KLINE_TTL: int = 300
    WS_UPDATE_INTERVAL: int = 5

    API_MAX_LIMIT: int = 5000
    HISTORY_DEFAULT_LIMIT: int = 500
    INDICATORS_DEFAULT_DAYS: int = 30

    DCA_INDICATOR_BUFFER_DAYS: int = 200
    DCA_MA_PERIOD: int = 200
    DCA_DEFAULT_MULTIPLIER: float = 3.0
    DCA_MULTIPLIER_MIN: float = 0.01
    DCA_MULTIPLIER_MAX: float = 100.0
    DCA_VA_MAX_MULTIPLE: int = 10
    DCA_STANDARD_MAX_MULTIPLE: int = 5
    DCA_COIN_PRECISION: float = 1e-8
    DCA_CACHE_TTL: int = 600

    PAIR_COMPARE_BASE_TIMEFRAME: str = "5m"

    BTC_GENESIS_DATE: str = "2009-01-03"
    BTC_EARLY_HISTORY_CUTOFF_TS: int = 1502928000000
    AHR999_COEFF_A: float = 5.84
    AHR999_COEFF_B: float = 17.01

    LLM_TEMPERATURE: float = 0.1
    LLM_REQUEST_TIMEOUT: float = 30.0

    MARKET_CRON_INTERVAL_HOURS: int = 4

    SENTIMENT_API_URL: str = "https://api.alternative.me/fng/"
    MEMPOOL_API_URL: str = "https://mempool.space/api/v1/mining/hashrate/3d"
    STABLECOIN_CHART_API_URL: str = "https://stablecoins.llama.fi/stablecoincharts/all"
    STABLECOIN_LIST_API_URL: str = "https://stablecoins.llama.fi/stablecoins?includePrices=false"
    FRED_API_URL: str = "https://api.stlouisfed.org/fred/series/observations"
    FRED_REQUEST_TIMEOUT: int = 15
    YFINANCE_REQUEST_DELAY: int = 2
    COINGECKO_BASE_URL: str = "https://api.coingecko.com/api/v3"
    COINGECKO_API_KEY: str = ""
    COINGECKO_TIMEOUT: float = 20.0
    COINGECKO_MAX_CONCURRENCY: int = 3
    COINGECKO_MAX_RETRIES: int = 2
    COINGECKO_RETRY_DELAY: float = 2.0
    COINGECKO_REQUEST_GAP: float = 1.0
    COINGECKO_CACHE_TTL: int = 900

    MINING_ELECTRICITY_COST_KWH: float = 0.08
    BTC_BLOCK_REWARD: float = 3.125
    BTC_BLOCKS_PER_DAY: int = 144
    MINER_EFFICIENCY_JTH: dict[str, float] = Field(
        default_factory=lambda: {"S19 Pro": 29.5, "S21": 17.5, "S23": 10.0}
    )

    LOG_LEVEL: str = "INFO"

    KLINE_RETENTION_DAYS: int = 365
    BACKTEST_RETENTION_DAYS: int = 90
    BACKTEST_INITIAL_CASH: float = 100000.0
    BACKTEST_DEFAULT_FEE_RATE: float = 0.1

    FREQTRADE_BACKTEST_TIMEOUT_SECONDS: int = 600
    FREQTRADE_WORKSPACE_DIR: Path = Field(default_factory=lambda: _default_runtime_root() / "freqtrade")

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("SYMBOLS", mode="before")
    @classmethod
    def parse_symbols(cls, value: Any) -> list[str]:
        if isinstance(value, str):
            return [symbol.strip() for symbol in value.split(",") if symbol.strip()]
        return value


settings = AppSettings()

__all__ = ["AppSettings", "settings", "BASE_DIR", "DEFAULT_DB_PATH"]
