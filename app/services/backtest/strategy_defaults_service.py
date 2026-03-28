from __future__ import annotations

from app.infra.db.database import session_scope
from app.infra.db.schema import StrategyDefinition, StrategyVersion
from app.services.backtest.strategy_catalog import get_builtin_strategy_definitions

from .strategy_support import normalize_strategy_version_payload


class StrategyDefaultsService:
    def ensure_defaults(self) -> None:
        builtin_strategies = get_builtin_strategy_definitions()
        with session_scope() as session:
            for definition in builtin_strategies:
                strategy = session.query(StrategyDefinition).filter_by(key=definition["key"]).first()
                if not strategy:
                    strategy = StrategyDefinition(
                        key=definition["key"],
                        name=definition["name"],
                        template=definition["template"],
                        category=definition["category"],
                        description=definition.get("description"),
                        is_active=True,
                    )
                    session.add(strategy)
                    session.flush()
                else:
                    strategy.name = definition["name"]
                    strategy.template = definition["template"]
                    strategy.category = definition["category"]
                    strategy.description = definition.get("description")
                    strategy.is_active = True

                for version_payload in definition["versions"]:
                    existing = (
                        session.query(StrategyVersion)
                        .filter_by(strategy_key=definition["key"], version=version_payload["version"])
                        .first()
                    )
                    normalized_config, normalized_parameter_space = normalize_strategy_version_payload(
                        definition["template"],
                        version_payload["config"] or {},
                        version_payload.get("parameter_space") or {},
                    )
                    if existing:
                        if existing.config != normalized_config:
                            existing.config = normalized_config
                        if (existing.parameter_space or {}) != normalized_parameter_space:
                            existing.parameter_space = normalized_parameter_space
                        existing.name = version_payload["name"]
                        existing.notes = version_payload.get("notes")
                        existing.is_default = version_payload.get("is_default", False)
                        continue
                    session.add(
                        StrategyVersion(
                            strategy_key=definition["key"],
                            version=version_payload["version"],
                            name=version_payload["name"],
                            config=normalized_config,
                            parameter_space=normalized_parameter_space,
                            notes=version_payload.get("notes"),
                            is_default=version_payload.get("is_default", False),
                        )
                    )
