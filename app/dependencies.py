from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar, cast

from starlette.requests import HTTPConnection

from app.runtime import AppRuntimeServices
from app.runtime_refs import RuntimeServiceRef

TService = TypeVar("TService")

def get_runtime_services(connection: HTTPConnection) -> AppRuntimeServices:
    runtime_services = getattr(connection.app.state, "runtime_services", None)
    if runtime_services is None:
        raise RuntimeError("App runtime services are not initialized")
    return cast(AppRuntimeServices, runtime_services)


def runtime_dependency(ref: RuntimeServiceRef[TService]) -> Callable[[HTTPConnection], TService]:
    def dependency(connection: HTTPConnection) -> TService:
        runtime_services = get_runtime_services(connection)
        return runtime_services.require_service(ref)

    dependency.__name__ = f"runtime_dependency__{ref.section}__{ref.name}"
    return dependency
