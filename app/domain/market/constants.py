"""
Centralized constants for the application to avoid magic strings.
"""
from enum import Enum

# Market Data Constants
DEFAULT_EXCHANGE_ID = 'binance'
DEFAULT_TIMEFRAME = '1h'
DEFAULT_LIMIT = 1000

# Redis Key Prefixes
KEY_PREFIX_KLINE = "kline"
KEY_PREFIX_SENTIMENT = "sentiment"

class Timeframe(str, Enum):
    M1 = '1m'
    M5 = '5m'
    M15 = '15m'
    H1 = '1h'
    H4 = '4h'
    D1 = '1d'
    W1 = '1w'
    M1_MONTH = '1M'

class ExchangeID(str, Enum):
    BINANCE = 'binance'
    OKX = 'okx'
    BYBIT = 'bybit'

# Common Symbols (Optional, could remain in settings if dynamic)
SYMBOL_BTC_USDT = 'BTC/USDT'
SYMBOL_ETH_USDT = 'ETH/USDT'
