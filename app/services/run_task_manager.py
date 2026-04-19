from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from utils.logger import logger


class RunTaskManager:
    def __init__(
        self,
        *,
        list_active_run_ids: Callable[[], list[int]],
        tick: Callable[[int], bool],
        mark_failed: Callable[[int, str], None],
        interval_seconds: Callable[[], float],
        error_label: str,
    ) -> None:
        self._list_active_run_ids = list_active_run_ids
        self._tick = tick
        self._mark_failed = mark_failed
        self._interval_seconds = interval_seconds
        self._error_label = error_label
        self._tasks: dict[int, asyncio.Task[Any]] = {}

    async def restore_active_runs(self) -> None:
        loop = asyncio.get_running_loop()
        run_ids = await loop.run_in_executor(None, self._list_active_run_ids)
        for run_id in run_ids:
            self.ensure_task(run_id, initial_delay=self._interval_seconds())

    async def shutdown(self) -> None:
        tasks = list(self._tasks.values())
        self._tasks.clear()
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def ensure_task(self, run_id: int, *, initial_delay: float = 0.0) -> None:
        task = self._tasks.get(run_id)
        if task and not task.done():
            return
        self._tasks[run_id] = asyncio.create_task(self._run_loop(run_id, initial_delay=initial_delay))

    async def cancel_task(self, run_id: int) -> None:
        task = self._tasks.pop(run_id, None)
        if not task:
            return
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)

    async def _run_loop(self, run_id: int, *, initial_delay: float = 0.0) -> None:
        try:
            if initial_delay > 0:
                await asyncio.sleep(initial_delay)
            while True:
                loop = asyncio.get_running_loop()
                should_continue = await loop.run_in_executor(None, lambda: self._tick(run_id))
                if not should_continue:
                    self._tasks.pop(run_id, None)
                    return
                await asyncio.sleep(self._interval_seconds())
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, lambda: self._mark_failed(run_id, str(exc)))
            self._tasks.pop(run_id, None)
            # 单个模拟运行失败已经写回对应 run，不应把整个后台 runtime 标记为不可用。
            logger.error(f"{self._error_label} run_id={run_id}: {exc}", exc_info=True)
