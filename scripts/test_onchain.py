import asyncio
from app.services.indicators.onchain_provider import OnchainProvider

async def test():
    print("Testing OnchainProvider...")
    p = OnchainProvider()
    data = await p.fetch_data()
    print(f"Fetched {len(data)} indicators:")
    for d in data:
        print(f"  {d['indicator_id']}: {d['value']}")

asyncio.run(test())
