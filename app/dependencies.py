from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

from starlette.requests import HTTPConnection

from app.runtime import AppRuntimeServices, RuntimeSection


def get_runtime_services(connection: HTTPConnection) -> AppRuntimeServices:
    runtime_services = getattr(connection.app.state, "runtime_services", None)
    if runtime_services is None:
        raise RuntimeError("App runtime services are not initialized")
    return cast(AppRuntimeServices, runtime_services)


def runtime_dependency(path: str) -> Callable[[HTTPConnection], Any]:
    section_name, service_name = _parse_runtime_path(path)

    def dependency(connection: HTTPConnection) -> Any:
        runtime_services = get_runtime_services(connection)
        section = getattr(runtime_services, section_name, None)
        if not isinstance(section, RuntimeSection):
            raise RuntimeError(f"Runtime section is not initialized: {section_name}")
        service = getattr(section, service_name, None)
        if service is None:
            raise RuntimeError(f"Runtime service is not initialized: {path}")
        return service

    dependency.__name__ = f"runtime_dependency__{section_name}__{service_name}"
    return dependency


def _parse_runtime_path(path: str) -> tuple[str, str]:
    parts = path.split(".")
    if len(parts) != 2 or not all(parts):
        raise ValueError(f"Invalid runtime service path: {path}")
    return parts[0], parts[1]
