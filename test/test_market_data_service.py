from app.services.market.market_data_service import MarketDataService
from config import settings


def test_fetch_data():
    print(f"\n--- Testing MarketDataService ({settings.EXCHANGE_ID}) ---")

    try:
        service = MarketDataService()
    except Exception as e:
        print(f"Failed to init service: {e}")
        return

    symbol = settings.SYMBOLS[0]
    print(f"Fetching {symbol} ...")

    data = service.get_kline_data(symbol, limit=5)

    if data and len(data) > 0:
        print(f"Successfully fetched {len(data)} candles.")
        print("Sample (Latest):", data[-1])
        sample = data[-1]
        if len(sample) >= 6:
            print("Data Structure: OK")
        else:
            print("Data Structure: FAILED")
    else:
        print("Fetch FAILED (Empty data)")


if __name__ == "__main__":
    test_fetch_data()
