from __future__ import annotations

from typing import Any

from app.infra.db.database import session_scope
from app.infra.db.schema import StrategyDefinition, StrategyVersion
from app.services.backtest.models import StrategyVersionRecord
from app.services.backtest.strategy_catalog import (
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
            result: list[dict[str, Any]] = []
            for definition in definitions:
                runtime_contract = get_template_runtime_contract(definition.template)
                versions = (
                    session.query(StrategyVersion)
                    .filter_by(strategy_key=definition.key)
                    .order_by(StrategyVersion.version.desc())
                    .all()
                )
                normalized_versions = []
                for version in versions:
                    normalized_config, normalized_parameter_space = normalize_strategy_version_payload(
                        definition.template,
                        version.config or {},
                        version.parameter_space or {},
                    )
                    normalized_versions.append(
                        {
                            "id": version.id,
                            "version": version.version,
                            "name": version.name,
                            "notes": version.notes,
                            "is_default": version.is_default,
                            "config": normalized_config,
                            "parameter_space": normalized_parameter_space,
                            "runtime": strategy_runtime_profile(normalized_config),
                        }
                    )
                result.append(
                    {
                        "key": definition.key,
                        "name": definition.name,
                        "template": definition.template,
                        "category": definition.category,
                        "description": definition.description,
                        "is_active": definition.is_active,
                        "template_runtime": runtime_contract,
                        "versions": normalized_versions,
                    }
                )
            return result

    def get_strategy_version(self, strategy_key: str, version: int | None = None) -> StrategyVersionRecord:
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
