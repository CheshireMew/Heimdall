from __future__ import annotations

from app.services.market.crypto_index_service import CryptoIndexService


class CryptoIndexAppService:
    def __init__(self, provider: CryptoIndexService) -> None:
        self.provider = provider

    async def get_index(self, top_n: int, days: int):
        return await self.provider.build_index(top_n=top_n, days=days)
