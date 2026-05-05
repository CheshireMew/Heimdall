from __future__ import annotations

from app.runtime import AppRuntimeServices


async def start_market_scheduler(service, _runtime_services: AppRuntimeServices) -> None:
    service.start()


async def start_binance_snapshot(service, _runtime_services: AppRuntimeServices) -> None:
    await service.start()


async def start_binance_market_page_refresher(service, _runtime_services: AppRuntimeServices) -> None:
    service.start()


async def restore_paper_runs(service, _runtime_services: AppRuntimeServices) -> None:
    await service.restore_active_runs()


async def shutdown_service(service, _runtime_services: AppRuntimeServices) -> None:
    await service.shutdown()
