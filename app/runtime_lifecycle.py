from __future__ import annotations

from app.runtime import AppRuntimeServices


async def start_market_scheduler(service, _runtime_services: AppRuntimeServices) -> None:
    service.start()


async def start_binance_snapshot(service, _runtime_services: AppRuntimeServices) -> None:
    await service.start()


async def start_binance_market_page_refresher(service, _runtime_services: AppRuntimeServices) -> None:
    service.start()


async def start_paper_run_monitoring(service, _runtime_services: AppRuntimeServices) -> None:
    await service.start_active_run_monitoring()


async def shutdown_service(service, _runtime_services: AppRuntimeServices) -> None:
    await service.shutdown()
