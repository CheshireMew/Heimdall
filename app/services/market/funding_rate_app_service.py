from __future__ import annotations

from app.schemas.market import FundingRateHistoryResponse, FundingRateSnapshotResponse, FundingRateSyncResponse
from app.services.executor import run_sync
from app.services.market.funding_rate_service import FundingRateService


class FundingRateAppService:
    def __init__(self, *, funding_rate_service: FundingRateService) -> None:
        self.funding_rate_service = funding_rate_service

    async def get_current_funding_rate(self, symbol: str) -> FundingRateSnapshotResponse:
        payload = await run_sync(lambda: self.funding_rate_service.fetch_current_rate(symbol))
        return FundingRateSnapshotResponse.model_validate(payload)

    async def sync_funding_rate_history(
        self,
        *,
        symbol: str,
        start_date: str | None,
        end_date: str | None,
    ) -> FundingRateSyncResponse:
        payload = await run_sync(
            lambda: self.funding_rate_service.sync_history(
                symbol,
                start_date=start_date,
                end_date=end_date,
            )
        )
        return FundingRateSyncResponse.model_validate(payload)

    async def get_funding_rate_history(
        self,
        *,
        symbol: str,
        start_date: str | None,
        end_date: str | None,
        limit: int | None,
    ) -> FundingRateHistoryResponse:
        payload = await run_sync(
            lambda: self.funding_rate_service.get_history(
                symbol,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
            )
        )
        return FundingRateHistoryResponse.model_validate(payload)
