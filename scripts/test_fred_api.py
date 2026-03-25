"""
Test FRED API Configuration
"""
import asyncio
import httpx
import os
from dotenv import load_dotenv

async def test_fred_api():
    print("=" * 70)
    print("          FRED API Configuration Test")
    print("=" * 70)
    print()

    # Load environment variables
    load_dotenv()
    api_key = os.getenv('FRED_API_KEY')

    if not api_key:
        print("[ERROR] FRED_API_KEY not found in .env file")
        return False

    print(f"[OK] API Key loaded: {api_key[:8]}...{api_key[-4:]}")
    print()

    # Test API connection
    print("Testing FRED API connection...")
    print()

    try:
        url = 'https://api.stlouisfed.org/fred/series/observations'

        # Test multiple indicators
        tests = [
            ('DGS10', '10-Year Treasury Rate'),
            ('DFF', 'Federal Funds Rate'),
            ('M2SL', 'M2 Money Supply')
        ]

        async with httpx.AsyncClient(timeout=10.0) as client:
            for series_id, name in tests:
                params = {
                    'series_id': series_id,
                    'api_key': api_key,
                    'file_type': 'json',
                    'limit': 1,
                    'sort_order': 'desc'
                }

                res = await client.get(url, params=params)

                if res.status_code == 200:
                    data = res.json()
                    obs = data.get('observations', [])
                    if obs:
                        value = obs[0].get('value')
                        date = obs[0].get('date')
                        if value != '.':  # FRED uses '.' for missing values
                            print(f"[OK] {name:25} : {value:>10} ({date})")
                        else:
                            print(f"[--] {name:25} : No data ({date})")
                    else:
                        print(f"[FAIL] {name:25} : No data returned")
                else:
                    print(f"[FAIL] {name:25} : HTTP {res.status_code}")
                    print(f"       Error: {res.text[:100]}")
                    return False

                # Small delay to avoid rapid requests
                await asyncio.sleep(0.5)

        print()
        print("=" * 70)
        print("SUCCESS! FRED API is configured and working properly!")
        print("=" * 70)
        return True

    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        print()
        print("Please check:")
        print("  1. API Key is correct")
        print("  2. Network connection is available")
        print("  3. Firewall is not blocking FRED API")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_fred_api())
    sys.exit(0 if success else 1)
