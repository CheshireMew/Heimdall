from __future__ import annotations

from typing import Any

from app.services.backtest.models import StrategyVersionRecord
from app.services.backtest.strategy_catalog import (
    create_indicator_definition,
    create_template_definition,
    get_builtin_strategy_definitions,
    get_indicator_catalog,
    get_indicator_engine_catalog,
    get_template_catalog,
    get_template_spec,
)
from app.services.backtest.strategy_contract import editor_contract, normalize_strategy_payload
from app.infra.db.database import engine, session_scope
from app.infra.db.schema import Base, StrategyDefinition, StrategyVersion


def normalize_strategy_version_payload(
    template: str,
    config: dict[str, Any],
    parameter_space: dict[str, list[Any]] | None,
) -> tuple[dict[str, Any], dict[str, list[Any]]]:
    return normalize_strategy_payload(
        template_spec=get_template_spec(template),
        config=dict(config or {}),
        parameter_space=dict(parameter_space or {}),
    )


class StrategyLibraryService:
    def get_editor_contract(self) -> dict[str, Any]:
        return editor_contract()

    def list_templates(self) -> list[dict[str, Any]]:
        return get_template_catalog()

    def list_indicators(self) -> list[dict[str, Any]]:
        return get_indicator_catalog()

    def list_indicator_engines(self) -> list[dict[str, Any]]:
        return get_indicator_engine_catalog()

    def create_indicator(
        self,
        *,
        key: str,
        name: str,
        engine_key: str,
        description: str | None,
        params: list[dict[str, Any]] | None,
    ) -> dict[str, Any]:
        return create_indicator_definition(
            key=key,
            name=name,
            engine_key=engine_key,
            description=description,
            params=params,
        )

    def create_template(
        self,
        *,
        key: str,
        name: str,
        category: str,
        description: str | None,
        indicator_keys: list[str],
        default_config: dict[str, Any],
        default_parameter_space: dict[str, list[Any]] | None,
    ) -> dict[str, Any]:
        return create_template_definition(
            key=key,
            name=name,
            category=category,
            description=description,
            indicator_keys=indicator_keys,
            default_config=default_config,
            default_parameter_space=default_parameter_space,
        )

    def ensure_defaults(self) -> None:
        Base.metadata.create_all(engine, tables=[StrategyDefinition.__table__, StrategyVersion.__table__])
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
                    if existing:
                        normalized_config, normalized_parameter_space = normalize_strategy_version_payload(
                            definition["template"],
                            version_payload["config"] or {},
                            version_payload.get("parameter_space") or {},
                        )
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
                            config=version_payload["config"],
                            parameter_space=version_payload.get("parameter_space") or {},
                            notes=version_payload.get("notes"),
                            is_default=version_payload.get("is_default", False),
                        )
                    )

    def list_strategies(self) -> list[dict[str, Any]]:
        self.ensure_defaults()
        with session_scope() as session:
            definitions = (
                session.query(StrategyDefinition)
                .order_by(StrategyDefinition.category.asc(), StrategyDefinition.name.asc())
                .all()
            )
            result: list[dict[str, Any]] = []
            for definition in definitions:
                versions = (
                    session.query(StrategyVersion)
                    .filter_by(strategy_key=definition.key)
                    .order_by(StrategyVersion.version.desc())
                    .all()
                )
                result.append(
                    {
                        "key": definition.key,
                        "name": definition.name,
                        "template": definition.template,
                        "category": definition.category,
                        "description": definition.description,
                        "is_active": definition.is_active,
                        "versions": [
                            {
                                "id": version.id,
                                "version": version.version,
                                "name": version.name,
                                "notes": version.notes,
                                "is_default": version.is_default,
                                "config": version.config,
                                "parameter_space": version.parameter_space or {},
                            }
                            for version in versions
                        ],
                    }
                )
            return result

    def get_strategy_version(self, strategy_key: str, version: int | None = None) -> StrategyVersionRecord:
        self.ensure_defaults()
        with session_scope() as session:
            query = session.query(StrategyDefinition, StrategyVersion).join(
                StrategyVersion, StrategyVersion.strategy_key == StrategyDefinition.key
            ).filter(StrategyDefinition.key == strategy_key)

            if version is None:
                row = query.order_by(StrategyVersion.is_default.desc(), StrategyVersion.version.desc()).first()
            else:
                row = query.filter(StrategyVersion.version == version).first()

            if not row:
                raise ValueError(f"策略不存在: {strategy_key} v{version if version is not None else 'default'}")

            definition, strategy_version = row
            normalized_config, normalized_parameter_space = normalize_strategy_version_payload(
                definition.template,
                strategy_version.config or {},
                strategy_version.parameter_space or {},
            )
            return StrategyVersionRecord(
                strategy_key=definition.key,
                strategy_name=definition.name,
                version=strategy_version.version,
                template=definition.template,
                config=normalized_config,
                parameter_space=normalized_parameter_space,
                description=definition.description,
                notes=strategy_version.notes,
                version_name=strategy_version.name,
                id=strategy_version.id,
                is_default=strategy_version.is_default,
            )

    def create_strategy_version(
        self,
        *,
        key: str,
        name: str,
        template: str,
        category: str,
        description: str | None,
        config: dict[str, Any],
        parameter_space: dict[str, list[Any]] | None,
        notes: str | None,
        make_default: bool,
    ) -> StrategyVersionRecord:
        Base.metadata.create_all(engine, tables=[StrategyDefinition.__table__, StrategyVersion.__table__])
        normalized_config, normalized_parameter_space = normalize_strategy_version_payload(template, config, parameter_space)
        with session_scope() as session:
            definition = session.query(StrategyDefinition).filter_by(key=key).first()
            if not definition:
                definition = StrategyDefinition(
                    key=key,
                    name=name,
                    template=template,
                    category=category,
                    description=description,
                    is_active=True,
                )
                session.add(definition)
                session.flush()
            else:
                definition.template = template
                definition.category = category
                definition.description = description

            current_max = (
                session.query(StrategyVersion.version)
                .filter_by(strategy_key=key)
                .order_by(StrategyVersion.version.desc())
                .first()
            )
            next_version = (current_max[0] if current_max else 0) + 1

            if make_default:
                session.query(StrategyVersion).filter_by(strategy_key=key).update({"is_default": False})

            strategy_version = StrategyVersion(
                strategy_key=key,
                version=next_version,
                name=name,
                config=normalized_config,
                parameter_space=normalized_parameter_space,
                notes=notes,
                is_default=make_default or current_max is None,
            )
            session.add(strategy_version)
            session.flush()

            return StrategyVersionRecord(
                strategy_key=definition.key,
                strategy_name=definition.name,
                version=strategy_version.version,
                template=definition.template,
                config=normalized_config,
                parameter_space=normalized_parameter_space,
                description=definition.description,
                notes=strategy_version.notes,
                version_name=strategy_version.name,
                id=strategy_version.id,
                is_default=strategy_version.is_default,
            )
