from __future__ import annotations

from datetime import datetime

from sqlalchemy.sql.elements import ColumnElement

from app.infra.db.schema import BacktestRun

RUN_STATUS_RUNNING = "running"
RUN_STATUS_COMPLETED = "completed"
RUN_STATUS_FAILED = "failed"
RUN_STATUS_STOPPED = "stopped"
RETENTION_ELIGIBLE_STATUSES = (RUN_STATUS_COMPLETED, RUN_STATUS_FAILED, RUN_STATUS_STOPPED)


def active_run_filters(*, execution_mode: str, engine: str) -> tuple[ColumnElement[bool], ...]:
    return (
        BacktestRun.status == RUN_STATUS_RUNNING,
        BacktestRun.execution_mode == execution_mode,
        BacktestRun.engine == engine,
    )


def retention_eligible_run_filters(cutoff_dt: datetime) -> tuple[ColumnElement[bool], ...]:
    # Retention is only allowed to remove terminal runs; runtime-restorable rows use the same
    # status/mode/engine boundary as task restoration and must never be selected by age alone.
    return (
        BacktestRun.status.in_(RETENTION_ELIGIBLE_STATUSES),
        BacktestRun.created_at < cutoff_dt,
    )
