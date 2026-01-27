import sys
import os
import asyncio
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.market_provider import MarketProvider
from utils.logger import logger

def download_history(symbol, timeframe, start_year=None):
    """
    下载历史数据
    :param start_year: 起始年份 (int)，如果为 None 则默认 2017 (Binance Launch)
    """
    provider = MarketProvider()
    
    end_date = datetime.now()
    
    if start_year:
        start_date = datetime(year=start_year, month=1, day=1)
    else:
        # Default to 2017-01-01 if "ALL" requested or no days specified
        start_date = datetime(year=2017, month=1, day=1)
    
    print(f"🚀 开始下载 {symbol} - {timeframe} 全量历史数据")
    print(f"📅 范围: {start_date} -> {end_date}")
    print("⏳ 这将花费较长时间，请耐心等待...")
    
    try:
        data = provider.fetch_ohlcv_range(symbol, timeframe, start_date, end_date)
        
        if data:
            print(f"✅ 下载完成! 共 {len(data)} 条K线数据已存入数据库。")
            print(f"📊 实际覆盖: {datetime.fromtimestamp(data[0][0]/1000)} -> {datetime.fromtimestamp(data[-1][0]/1000)}")
        else:
            print("❌ 未获取到数据。")
        
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        logger.error(f"History download failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python download_history.py <SYMBOL> <TIMEFRAME> [START_YEAR]")
        print("Example: python download_history.py BTC/USDT 5m 2020")
        print("Example (All Time): python download_history.py BTC/USDT 5m")
        sys.exit(1)
        
    symbol = sys.argv[1]
    timeframe = sys.argv[2]
    # If 3rd arg provided, parse as year. Else default to all (2017).
    start_year = int(sys.argv[3]) if len(sys.argv) > 3 else 2017
    
    download_history(symbol, timeframe, start_year)
