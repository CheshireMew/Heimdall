import sys
import os
import time

# Ensure we can import from core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.market_provider import MarketProvider
from config import settings

def test_fetch_data():
    print(f"\n--- Testing MarketProvider ({settings.EXCHANGE_ID}) ---")
    
    try:
        provider = MarketProvider()
    except Exception as e:
        print(f"Failed to init provider: {e}")
        return

    symbol = settings.SYMBOLS[0] # BTC/USDT typically
    print(f"Fetching {symbol} ...")
    
    # 模拟少量数据
    data = provider.get_kline_data(symbol, limit=5)
    
    if data and len(data) > 0:
        print(f"Successfully fetched {len(data)} candles.")
        print("Sample (Latest):", data[-1])
        # Check structure: [timestamp, open, high, low, close, volume]
        sample = data[-1]
        if len(sample) >= 6:
            print("Data Structure: OK")
        else:
            print("Data Structure: FAILED")
    else:
        print("Fetch FAILED (Empty data)")

if __name__ == "__main__":
    test_fetch_data()
