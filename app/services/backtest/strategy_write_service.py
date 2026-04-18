from __future__ import annotations

from typing import Any

from app.infra.db.database import session_scope
from app.infra.db.schema import StrategyDefinition, StrategyVersion
from app.services.backtest.models import StrategyVersionRecord
from app.services.backtest.scripted_template_runtime import template_supports_version_editing
from app.services.backtest.strategy_catalog import create_indicator_definition, create_template_definition, get_template_runtime_contract

from .strategy_support import normalize_strategy_version_payload


class StrategyWriteService:
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
        runtime_contract = get_template_runtime_contract(template)
        if not template_supports_version_editing(runtime_contract):
            raise ValueError("该内置脚本策略当前只提供固定版本，不支持复制编辑")
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
