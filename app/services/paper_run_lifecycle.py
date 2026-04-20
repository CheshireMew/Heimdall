from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.infra.db.database import DatabaseRuntime
from app.infra.db.schema import BacktestRun
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
