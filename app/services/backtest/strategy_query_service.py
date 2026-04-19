from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.infra.db.database import session_scope
from app.infra.db.schema import StrategyDefinition, StrategyVersion
from app.contracts.backtest import StrategyVersionRecord
from app.services.backtest.strategy_catalog import (
    get_builtin_strategy_definitions,
    get_indicator_catalog,
    get_indicator_engine_catalog,
    get_template_catalog,
    get_template_runtime_contract,
)
from app.services.backtest.run_form_contract import backtest_run_defaults
from app.services.backtest.strategy_contract import editor_contract, strategy_runtime_profile

from .strategy_support import normalize_strategy_version_payload


class StrategyQueryService:
    def get_editor_contract(self) -> dict[str, Any]:
        contract = editor_contract()
        contract["run_defaults"] = backtest_run_defaults()
        return contract

    def list_templates(self) -> list[dict[str, Any]]:
        return get_template_catalog()

    def list_indicators(self) -> list[dict[str, Any]]:
        return get_indicator_catalog()

    def list_indicator_engines(self) -> list[dict[str, Any]]:
        return get_indicator_engine_catalog()

    def list_strategies(self) -> list[dict[str, Any]]:
        with session_scope() as session:
            definitions = (
                session.query(StrategyDefinition)
                .order_by(StrategyDefinition.category.asc(), StrategyDefinition.name.asc())
                .all()
            )
            version_rows = session.query(StrategyVersion).order_by(StrategyVersion.version.desc()).all()

        versions_by_key: dict[str, list[StrategyVersion]] = {}
        for version_row in version_rows:
            versions_by_key.setdefault(version_row.strategy_key, []).append(version_row)

        result: list[dict[str, Any]] = []
        builtin_by_key = {item["key"]: deepcopy(item) for item in get_builtin_strategy_definitions()}

        for strategy_key, builtin in builtin_by_key.items():
            db_versions = [row for row in versions_by_key.get(strategy_key, []) if row.version != 1]
            has_custom_default = any(row.is_default for row in db_versions)
            builtin_versions = []
            for version_payload in builtin["versions"]:
                builtin_versions.append(
                    self._build_version_payload(
                        template=builtin["template"],
                        version=version_payload["version"],
                        name=version_payload["name"],
                        notes=version_payload.get("notes"),
                        is_default=version_payload.get("is_default", False) and not has_custom_default,
                        config=version_payload["config"] or {},
                        parameter_space=version_payload.get("parameter_space") or {},
                        version_id=None,
                    )
                )

            result.append(
                {
                    "key": strategy_key,
                    "name": builtin["name"],
                    "template": builtin["template"],
                    "category": builtin["category"],
                    "description": builtin.get("description"),
                    "is_active": True,
                    "template_runtime": get_template_runtime_contract(builtin["template"]),
                    "versions": [
                        *self._build_db_versions(builtin["template"], db_versions),
                        *builtin_versions,
                    ],
                }
            )

        for definition in definitions:
            if definition.key in builtin_by_key:
                continue
            result.append(
                {
                    "key": definition.key,
                    "name": definition.name,
                    "template": definition.template,
                    "category": definition.category,
                    "description": definition.description,
                    "is_active": definition.is_active,
                    "template_runtime": get_template_runtime_contract(definition.template),
                    "versions": self._build_db_versions(definition.template, versions_by_key.get(definition.key, [])),
                }
            )

        return sorted(result, key=lambda item: (item["category"], item["name"].lower()))

    def get_strategy_version(self, strategy_key: str, version: int | None = None) -> StrategyVersionRecord:
        builtin_definition = self._get_builtin_definition(strategy_key)
        with session_scope() as session:
            definition = session.query(StrategyDefinition).filter(StrategyDefinition.key == strategy_key).first()
            db_versions = (
                session.query(StrategyVersion)
                .filter(StrategyVersion.strategy_key == strategy_key)
                .order_by(StrategyVersion.is_default.desc(), StrategyVersion.version.desc())
                .all()
            )

        if builtin_definition:
            filtered_versions = [row for row in db_versions if row.version != 1]
            if version is None:
                selected = next((row for row in filtered_versions if row.is_default), None)
                if selected is None:
                    return self._build_builtin_version_record(builtin_definition)
            elif version == 1:
                return self._build_builtin_version_record(builtin_definition)
            else:
                selected = next((row for row in filtered_versions if row.version == version), None)

            if selected is None:
                raise ValueError(f"策略不存在: {strategy_key} v{version if version is not None else 'default'}")
            return self._build_strategy_version_record(
                definition_name=builtin_definition["name"],
                description=builtin_definition.get("description"),
                template=builtin_definition["template"],
                strategy_key=strategy_key,
                strategy_version=selected,
            )

        if not definition:
            raise ValueError(f"策略不存在: {strategy_key} v{version if version is not None else 'default'}")

        selected = None
        if version is None:
            selected = db_versions[0] if db_versions else None
        else:
            selected = next((row for row in db_versions if row.version == version), None)
        if selected is None:
            raise ValueError(f"策略不存在: {strategy_key} v{version if version is not None else 'default'}")
        return self._build_strategy_version_record(
            definition_name=definition.name,
            description=definition.description,
            template=definition.template,
            strategy_key=strategy_key,
            strategy_version=selected,
        )

    def _build_db_versions(self, template: str, versions: list[StrategyVersion]) -> list[dict[str, Any]]:
        return [
            self._build_version_payload(
                template=template,
                version=version.version,
                name=version.name,
                notes=version.notes,
                is_default=version.is_default,
                config=version.config or {},
                parameter_space=version.parameter_space or {},
                version_id=version.id,
            )
            for version in versions
        ]

    def _build_version_payload(
        self,
        *,
        template: str,
        version: int,
        name: str,
        notes: str | None,
        is_default: bool,
        config: dict[str, Any],
        parameter_space: dict[str, Any],
        version_id: int | None,
    ) -> dict[str, Any]:
        normalized_config, normalized_parameter_space = normalize_strategy_version_payload(
            template,
            config,
            parameter_space,
        )
        return {
            "id": version_id,
            "version": version,
            "name": name,
            "notes": notes,
            "is_default": is_default,
            "config": normalized_config,
            "parameter_space": normalized_parameter_space,
            "runtime": strategy_runtime_profile(normalized_config),
        }

    def _build_builtin_version_record(self, definition: dict[str, Any]) -> StrategyVersionRecord:
        version_payload = definition["versions"][0]
        normalized_config, normalized_parameter_space = normalize_strategy_version_payload(
            definition["template"],
            version_payload["config"] or {},
            version_payload.get("parameter_space") or {},
        )
        return StrategyVersionRecord(
            strategy_key=definition["key"],
            strategy_name=definition["name"],
            version=version_payload["version"],
            template=definition["template"],
            config=normalized_config,
            parameter_space=normalized_parameter_space,
            description=definition.get("description"),
            notes=version_payload.get("notes"),
            version_name=version_payload["name"],
            id=None,
            is_default=True,
        )

    def _build_strategy_version_record(
        self,
        *,
        definition_name: str,
        description: str | None,
        template: str,
        strategy_key: str,
        strategy_version: StrategyVersion,
    ) -> StrategyVersionRecord:
        normalized_config, normalized_parameter_space = normalize_strategy_version_payload(
            template,
            strategy_version.config or {},
            strategy_version.parameter_space or {},
        )
        return StrategyVersionRecord(
            strategy_key=strategy_key,
            strategy_name=definition_name,
            version=strategy_version.version,
            template=template,
            config=normalized_config,
            parameter_space=normalized_parameter_space,
            description=description,
            notes=strategy_version.notes,
            version_name=strategy_version.name,
            id=strategy_version.id,
            is_default=strategy_version.is_default,
        )

    def _get_builtin_definition(self, strategy_key: str) -> dict[str, Any] | None:
        return next(
            (definition for definition in get_builtin_strategy_definitions() if definition["key"] == strategy_key),
            None,
        )
