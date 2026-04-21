from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import Request
from fastapi.responses import JSONResponse

from app.background_runtime import BackgroundRuntimeController, BackgroundRuntimeStatus
from app.runtime import AppRuntimeServices
from app.runtime_graph import INFRA_DATABASE_RUNTIME, build_app_runtime_services


def _logger():
    from utils.logger import logger

    return logger


def _init_db(database_runtime) -> None:
    from app.infra.db.schema_runtime import verify_database_schema

    verify_database_schema(database_runtime)


async def _init_db_async(app) -> None:
    try:
        database_runtime = app.state.runtime_services.require_service(INFRA_DATABASE_RUNTIME)
        await asyncio.to_thread(_init_db, database_runtime)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        app.state.database_error = exc
        _logger().error(f"数据库初始化失败: {exc}", exc_info=True)


async def _start_background_services(app, runtime_services: AppRuntimeServices) -> None:
    try:
        database_task = getattr(app.state, "database_task", None)
        if database_task is not None:
            await database_task
        if getattr(app.state, "database_error", None) is not None:
            return
        background_runtime = BackgroundRuntimeController(runtime_services)
        app.state.background_runtime = background_runtime
        await background_runtime.start()
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        app.state.background_services_error = exc
        _logger().error(f"后台服务启动失败: {exc}", exc_info=True)


async def _shutdown_background_services(app) -> None:
    background_runtime = getattr(app.state, "background_runtime", None)
    if background_runtime is not None:
        await background_runtime.shutdown()


def _dispose_runtime_services(app) -> None:
    runtime_services = getattr(app.state, "runtime_services", None)
    database_runtime = runtime_services.get_service(INFRA_DATABASE_RUNTIME) if runtime_services is not None else None
    if database_runtime is not None:
        database_runtime.dispose()


async def _cancel_task(task: asyncio.Task | None) -> None:
    if task is None or task.done():
        return
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)


@asynccontextmanager
async def lifespan(app):
    app.state.database_error = None
    app.state.background_services_error = None
    app.state.background_runtime = None
    app.state.runtime_services = await asyncio.to_thread(build_app_runtime_services)
    app.state.database_task = asyncio.create_task(_init_db_async(app))
    app.state.background_services_task = asyncio.create_task(
        _start_background_services(app, app.state.runtime_services)
    )
    yield
    await _cancel_task(getattr(app.state, "background_services_task", None))
    await _cancel_task(getattr(app.state, "database_task", None))
    await _shutdown_background_services(app)
    _dispose_runtime_services(app)


def requires_runtime_initialization(path: str) -> bool:
    return path.startswith("/api/") and path != "/api/v1/status"


def build_health_payload(app) -> tuple[dict[str, object], int]:
    database_task = getattr(app.state, "database_task", None)
    background_services_task = getattr(app.state, "background_services_task", None)
    database_error = getattr(app.state, "database_error", None)
    background_services_error = getattr(app.state, "background_services_error", None)
    background_runtime = getattr(app.state, "background_runtime", None)
    background_runtime_state = (
        background_runtime.state if background_runtime is not None else None
    )

    background_component = "disabled"
    if background_runtime_state is not None:
        background_component = background_runtime_state.status.value
    elif background_services_task is not None and not background_services_task.done():
        background_component = "starting"

    components = {
        "database": "failed"
        if database_error
        else (
            "starting"
            if database_task is not None and not database_task.done()
            else "ready"
        ),
        "background_runtime": background_component,
    }

    if database_error is not None:
        return {
            "status": "unhealthy",
            "version": "2.0.0",
            "components": components,
            "detail": "Database initialization failed",
        }, 503
    if background_services_error is not None:
        return {
            "status": "unhealthy",
            "version": "2.0.0",
            "components": components,
            "detail": "Background services failed",
        }, 503
    if (
        background_runtime_state is not None
        and background_runtime_state.status == BackgroundRuntimeStatus.FAILED
    ):
        return {
            "status": "unhealthy",
            "version": "2.0.0",
            "components": components,
            "detail": "Background runtime failed",
        }, 503
    if components["database"] != "ready":
        return {
            "status": "starting",
            "version": "2.0.0",
            "components": components,
        }, 503
    return {
        "status": "healthy",
        "version": "2.0.0",
        "components": components,
    }, 200


async def wait_for_background_services(request: Request, call_next):
    if requires_runtime_initialization(request.url.path):
        database_task = getattr(request.app.state, "database_task", None)
        if database_task is not None and not database_task.done():
            await database_task
        if getattr(request.app.state, "database_error", None) is not None:
            return JSONResponse(
                status_code=503, content={"detail": "Database initialization failed"}
            )
    return await call_next(request)
