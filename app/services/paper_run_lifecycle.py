from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.infra.db.database import DatabaseRuntime
from app.infra.db.schema import BacktestRun
from app.services.backtest.run_lifecycle import RUN_STATUS_FAILED
from app.services.executor import run_sync
from app.services.run_task_manager import RunTaskManager
from app.services.backtest.run_contract import PAPER_LIVE_EXECUTION_MODE, parse_run_metadata, update_paper_metadata
from utils.time_utils import utc_now_naive


class PaperRunLifecycle:
    def __init__(
        self,
        *,
        engine: str,
        run_repository,
        database_runtime: DatabaseRuntime,
        runtime_state: Callable[[Any], dict[str, Any]],
    ) -> None:
        self.engine = engine
        self.run_repository = run_repository
        self.database_runtime = database_runtime
        self.runtime_state = runtime_state

    def list_active_run_ids(self) -> list[int]:
        return self.run_repository.list_active_run_ids(
            execution_mode=PAPER_LIVE_EXECUTION_MODE,
            engine=self.engine,
        )

    def mark_stopped(self, run_id: int, status: str, reason: str) -> None:
        with self.database_runtime.session_scope() as session:
            run = session.query(BacktestRun).filter(BacktestRun.id == run_id).first()
            if not run:
                return
            if run.execution_mode != PAPER_LIVE_EXECUTION_MODE or run.engine != self.engine:
                return
            metadata = parse_run_metadata(run.metadata_info)
            run.status = status
            # Stop/fail writes must preserve the latest runtime_state shape; otherwise a manager
            # can accidentally erase open positions while only trying to mark lifecycle state.
            run.metadata_info = update_paper_metadata(
                metadata,
                runtime_state=self.runtime_state(metadata),
                last_updated=utc_now_naive().isoformat(),
                stop_reason=reason,
            )
            session.flush()


class PaperRunController:
    def __init__(
        self,
        *,
        engine: str,
        run_repository,
        database_runtime: DatabaseRuntime,
        runtime_state: Callable[[Any], dict[str, Any]],
        tick: Callable[[int], bool],
        interval_seconds: Callable[[], float],
        error_label: str,
    ) -> None:
        self.lifecycle = PaperRunLifecycle(
            engine=engine,
            run_repository=run_repository,
            database_runtime=database_runtime,
            runtime_state=runtime_state,
        )
        self._task_manager = RunTaskManager(
            list_active_run_ids=self.lifecycle.list_active_run_ids,
            tick=tick,
            mark_failed=self.mark_failed,
            interval_seconds=interval_seconds,
            error_label=error_label,
        )

    async def restore_active_runs(self) -> None:
        await self._task_manager.restore_active_runs()

    async def shutdown(self) -> None:
        await self._task_manager.shutdown()

    def activate_run(self, run_id: int) -> None:
        self._task_manager.ensure_task(run_id)

    async def cancel_run(self, run_id: int) -> None:
        await self._task_manager.cancel_task(run_id)

    def mark_failed(self, run_id: int, reason: str) -> None:
        self.lifecycle.mark_stopped(run_id, RUN_STATUS_FAILED, reason)

    def mark_stopped(self, run_id: int, status: str, reason: str) -> None:
        self.lifecycle.mark_stopped(run_id, status, reason)


class PaperRunHost:
    def __init__(self, controller: PaperRunController) -> None:
        self._controller = controller

    async def restore_active_runs(self) -> None:
        await self._controller.restore_active_runs()

    async def shutdown(self) -> None:
        await self._controller.shutdown()

    def activate_created_run(self, run_id: int) -> None:
        self._controller.activate_run(run_id)

    async def stop_and_cancel_run(self, run_id: int, *, status: str, reason: str) -> None:
        await run_sync(lambda: self._controller.mark_stopped(run_id, status, reason))
        await self._controller.cancel_run(run_id)


class PaperRunHostedService:
    paper_host: PaperRunHost

    async def restore_active_runs(self) -> None:
        await self.paper_host.restore_active_runs()

    async def shutdown(self) -> None:
        await self.paper_host.shutdown()

    def _activate_created_run(self, run_id: int) -> None:
        self.paper_host.activate_created_run(run_id)

    async def _stop_and_cancel_run(self, run_id: int, *, status: str, reason: str) -> None:
        await self.paper_host.stop_and_cancel_run(run_id, status=status, reason=reason)
