import os

# 尝试加载 .env 文件（如果安装了 python-dotenv）
try:
    from dotenv import load_dotenv
    load_dotenv()  # 从 .env 文件加载环境变量
except ImportError:
    pass  # 如果没有安装 python-dotenv，则直接使用系统环境变量

# ==========================================
# 市场数据配置 (Market Data)
# ==========================================
# 使用的交易所 (必须是 ccxt 支持的 ID, 如 'binance', 'okx', 'bybit')
EXCHANGE_ID = 'binance' 

# 交易对列表
SYMBOLS = [
    'BTC/USDT',
    'ETH/USDT',
    'SOL/USDT',
    'DOGE/USDT',
]

# K线周期 (Timeframe)
TIMEFRAME = '1h'  # 支持 1m, 5m, 1h, 4h, 1d 等

# 获取 K 线的数量 (用于计算指标)
LIMIT = 1000

# ==========================================
# AI 配置 (DeepSeek)
# ==========================================
# DeepSeek API Key (从环境变量获取，必须在 .env 中配置)
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

# DeepSeek Base URL
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# 模型名称
AI_MODEL = "deepseek-chat"

# ==========================================
# Redis 配置
# ==========================================
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

# ==========================================
# 数据库配置
# ==========================================
from pathlib import Path
_BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = _BASE_DIR / "data" / "heimdall.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

# ==========================================
# 技术指标参数 (Technical Analysis)
# ==========================================
EMA_PERIOD = 20
RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
