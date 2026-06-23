from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar, cast

from starlette.requests import HTTPConnection

from app.runtime import AppRuntimeServices

TService = TypeVar("TService")


def get_runtime_services(connection: HTTPConnection) -> AppRuntimeServices:
    runtime_services = getattr(connection.app.state, "runtime_services", None)
    if runtime_services is None:
        raise RuntimeError("App runtime services are not initialized")
    return cast(AppRuntimeServices, runtime_services)


def runtime_dependency(name: str) -> Callable[[HTTPConnection], Any]:
    def dependency(connection: HTTPConnection) -> Any:
        return get_runtime_services(connection).require(name)

    dependency.__name__ = f"runtime_dependency__{name}"
    return dependency
