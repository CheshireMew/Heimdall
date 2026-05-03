from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

from starlette.requests import HTTPConnection

from app.runtime import AppRuntimeServices
from app.runtime_refs import RuntimeServiceRef


def get_runtime_services(connection: HTTPConnection) -> AppRuntimeServices:
    runtime_services = getattr(connection.app.state, "runtime_services", None)
    if runtime_services is None:
        raise RuntimeError("App runtime services are not initialized")
    return cast(AppRuntimeServices, runtime_services)


def runtime_dependency(ref: RuntimeServiceRef) -> Callable[[HTTPConnection], Any]:
    def dependency(connection: HTTPConnection) -> Any:
        runtime_services = get_runtime_services(connection)
        return runtime_services.require_service(ref)

    dependency.__name__ = f"runtime_dependency__{ref.section}__{ref.name}"
    return dependency
