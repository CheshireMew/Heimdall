from __future__ import annotations

import asyncio
from typing import Any, Callable

from app.services.market.funding_rate_service import FundingRateService


class FundingRateAppService:
    def __init__(self, *, funding_rate_service: FundingRateService) -> None:
        self.funding_rate_service = funding_rate_service

    async def _run_in_thread(self, action: Callable[[], Any]) -> Any:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, action)

    async def get_current_funding_rate(self, symbol: str) -> dict[str, Any]:
        return await self._run_in_thread(lambda: self.funding_rate_service.fetch_current_rate(symbol))

    async def sync_funding_rate_history(
        self,
        *,
        symbol: str,
        start_date: str | None,
        end_date: str | None,
    ) -> dict[str, Any]:
        return await self._run_in_thread(
            lambda: self.funding_rate_service.sync_history(
                symbol,
                start_date=start_date,
                end_date=end_date,
            )
        )

    async def get_funding_rate_history(
        self,
        *,
        symbol: str,
        start_date: str | None,
        end_date: str | None,
        limit: int | None,
    ) -> dict[str, Any]:
        return await self._run_in_thread(
            lambda: self.funding_rate_service.get_history(
                symbol,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
            )
        )
