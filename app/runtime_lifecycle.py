from __future__ import annotations

from app.runtime import AppRuntimeServices
from app.runtime_refs import MARKET_BINANCE_MARKET_INTEL


async def start_market_scheduler(service, _runtime_services: AppRuntimeServices) -> None:
    service.start()


async def start_binance_snapshot(service, runtime_services: AppRuntimeServices) -> None:
    binance_market = runtime_services.require_service(MARKET_BINANCE_MARKET_INTEL)
    await service.start(
        spot_ticker_loader=binance_market.spot.get_ticker_24hr,
        usdm_ticker_loader=binance_market.usdm.get_ticker_24hr,
        usdm_mark_loader=binance_market.usdm.get_mark_price,
    )


async def restore_paper_runs(service, _runtime_services: AppRuntimeServices) -> None:
    await service.restore_active_runs()


async def shutdown_service(service, _runtime_services: AppRuntimeServices) -> None:
    await service.shutdown()
