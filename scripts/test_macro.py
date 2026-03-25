import asyncio
from app.services.indicators.macro_provider_v2 import MacroProviderV2 as MacroProvider

async def test():
    print("Testing MacroProvider...")
    p = MacroProvider()
    data = await p.fetch_data()
    print(f"Fetched {len(data)} indicators")
    for d in data:
        print(f"  {d['indicator_id']}: {d['value']}")

asyncio.run(test())
