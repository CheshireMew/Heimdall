from __future__ import annotations

import asyncio
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import TypeVar

from config import settings

T = TypeVar("T")

_database_executor = ThreadPoolExecutor(
    max_workers=max(int(settings.BLOCKING_DATABASE_MAX_WORKERS), 1),
    thread_name_prefix="heimdall-db",
)
_compute_executor = ThreadPoolExecutor(
    max_workers=max(int(settings.BLOCKING_COMPUTE_MAX_WORKERS), 1),
    thread_name_prefix="heimdall-compute",
)
_external_io_executor = ThreadPoolExecutor(
    max_workers=max(int(settings.BLOCKING_EXTERNAL_IO_MAX_WORKERS), 1),
    thread_name_prefix="heimdall-external",
)
_background_executor = ThreadPoolExecutor(
    max_workers=max(int(settings.BLOCKING_BACKGROUND_MAX_WORKERS), 1),
    thread_name_prefix="heimdall-background",
)


async def _run(executor: ThreadPoolExecutor, action: Callable[[], T]) -> T:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, action)


async def run_database(action: Callable[[], T]) -> T:
    return await _run(_database_executor, action)


async def run_compute(action: Callable[[], T]) -> T:
    return await _run(_compute_executor, action)


async def run_external_io(action: Callable[[], T]) -> T:
    return await _run(_external_io_executor, action)


async def run_background(action: Callable[[], T]) -> T:
    return await _run(_background_executor, action)
