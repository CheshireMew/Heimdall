"""
测试所有数据源的可用性
"""
import asyncio

async def test_all_sources():
    print("=" * 60)
    print("数据源可用性测试")
    print("=" * 60)

    # Test 1: FRED API
    print("\n[1/5] Testing FRED API...")
    try:
        from app.services.indicators.macro_provider_v2 import MacroProviderV2
        from config import settings

        if settings.FRED_API_KEY:
            provider = MacroProviderV2()
            data = await provider._fetch_fred_api("DGS10", "US10Y_TEST")
            if data:
                print(f"[OK] FRED API Working: {data['value']}")
            else:
                print("[ERROR] FRED API: No data returned")
        else:
            print("[WARN] FRED_API_KEY not configured")
    except Exception as e:
        print(f"[ERROR] FRED API Error: {e}")

    # Test 2: YFinance
    print("\n[2/5] Testing YFinance...")
    try:
        from app.services.indicators.macro_provider_v2 import MacroProviderV2
        provider = MacroProviderV2()
        data = await provider._fetch_yfinance_ticker("^TNX", "US10Y_TEST")
        if data:
            print(f"[OK] YFinance Working: {data['value']}")
        else:
            print("[ERROR] YFinance: No data returned")
    except Exception as e:
        print(f"[ERROR] YFinance Error: {e}")

    # Test 3: Binance PAXG
    print("\n[3/5] Testing Binance PAXG (Gold)...")
    try:
        from app.services.indicators.crypto_gold_provider import CryptoGoldProvider
        provider = CryptoGoldProvider()
        data = await provider._fetch_gold_price()
        if data:
            print(f"[OK] Binance PAXG Working: ${data['value']}/oz")
        else:
            print("[ERROR] Binance PAXG: No data returned")
    except Exception as e:
        print(f"[ERROR] Binance PAXG Error: {e}")

    # Test 4: Mempool (Hashrate)
    print("\n[4/5] Testing Mempool.space...")
    try:
        from app.services.indicators.onchain_provider import OnchainProvider
        provider = OnchainProvider()
        data = await provider._fetch_mempool_data()
        if data:
            print(f"[OK] Mempool Working: {len(data)} metrics")
            for d in data:
                print(f"  - {d['indicator_id']}: {d['value']}")
        else:
            print("[ERROR] Mempool: No data returned")
    except Exception as e:
        print(f"[ERROR] Mempool Error: {e}")

    # Test 5: Fear & Greed
    print("\n[5/5] Testing Fear & Greed Index...")
    try:
        from app.services.indicators.sentiment_provider import SentimentProvider
        provider = SentimentProvider()
        data = await provider._fetch_fear_greed_index()
        if data:
            print(f"[OK] Fear & Greed Working: {data[0]['value']} (Index)")
        else:
            print("[ERROR] Fear & Greed: No data returned")
    except Exception as e:
        print(f"[ERROR] Fear & Greed Error: {e}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_all_sources())
