from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Mapping, TypeVar

from app.runtime_refs import RuntimeServiceRef


RuntimeRole = Literal["all", "api", "background"]
RuntimeTarget = Literal["api", "background"]
TService = TypeVar("TService")


RUNTIME_ROLE_TARGETS: dict[RuntimeRole, tuple[RuntimeTarget, ...]] = {
    "all": ("api", "background"),
    "api": ("api",),
    "background": ("background",),
}


def runtime_role_targets(role: RuntimeRole) -> tuple[RuntimeTarget, ...]:
    return RUNTIME_ROLE_TARGETS[role]


def runtime_role_has_target(role: RuntimeRole, target: RuntimeTarget) -> bool:
    return target in runtime_role_targets(role)


@dataclass(slots=True)
class AppRuntimeServices:
    _services: dict[RuntimeServiceRef, Any] = field(default_factory=dict)

    @classmethod
    def empty(cls) -> AppRuntimeServices:
        return cls()

    @classmethod
    def from_entries(cls, entries: Mapping[RuntimeServiceRef, Any]) -> AppRuntimeServices:
        services = cls.empty()
        for ref, service in entries.items():
            services.set_service(ref, service)
        return services

    def get_service(self, ref: RuntimeServiceRef[TService]) -> TService | None:
        return self._services.get(ref)

    def set_service(self, ref: RuntimeServiceRef[TService], service: TService) -> None:
        self._services[ref] = service

    def require_service(self, ref: RuntimeServiceRef[TService]) -> TService:
        service = self.get_service(ref)
        if service is None:
            raise RuntimeError(f"Runtime service is not initialized: {ref.key}")
        return service
