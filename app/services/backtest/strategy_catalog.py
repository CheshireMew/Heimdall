from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.infra.db.database import session_scope
from app.infra.db.schema import IndicatorDefinition, StrategyTemplateDefinition
from app.services.backtest.scripted_template_runtime import get_template_runtime
from app.services.backtest.strategy_contract import (
    blank_strategy_config,
    editor_contract,
    normalize_indicator_params,
    normalize_parameter_space,
    normalize_strategy_identifier,
    normalize_strategy_config,
)
from app.services.backtest.strategy_definitions import (
    BUILTIN_INDICATOR_ENGINES,
    BUILTIN_TEMPLATE_DEFINITIONS,
)


def get_indicator_engine_catalog() -> list[dict[str, Any]]:
    return [
        {"key": key, **deepcopy(spec)}
        for key, spec in BUILTIN_INDICATOR_ENGINES.items()
    ]


def get_builtin_indicator_catalog() -> list[dict[str, Any]]:
    return [
        {
            "key": key,
            "engine": key,
            "is_builtin": True,
            **deepcopy(spec),
        }
        for key, spec in BUILTIN_INDICATOR_ENGINES.items()
    ]


def get_indicator_catalog() -> list[dict[str, Any]]:
    catalog = {item["key"]: item for item in get_builtin_indicator_catalog()}
    with session_scope() as session:
        rows = (
            session.query(IndicatorDefinition)
            .order_by(IndicatorDefinition.key.asc())
            .all()
        )
        for row in rows:
            catalog[row.key] = _indicator_row_payload(row)
    return sorted(
        catalog.values(),
        key=lambda item: (item.get("is_builtin") is False, item["name"].lower()),
    )


def get_indicator_registry_map() -> dict[str, dict[str, Any]]:
    return {item["key"]: item for item in get_indicator_catalog()}


def create_indicator_definition(
    *,
    key: str,
    name: str,
    engine_key: str,
    description: str | None,
    params: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    key = normalize_strategy_identifier(key, "指标标识")
    if key in BUILTIN_INDICATOR_ENGINES:
        raise ValueError("该指标标识已被内置指标占用")
    engine_spec = BUILTIN_INDICATOR_ENGINES.get(engine_key)
    if not engine_spec:
        raise ValueError("不支持的指标引擎")
    normalized_params = normalize_indicator_params(
        params or deepcopy(engine_spec["params"]), engine_spec["params"]
    )
    with session_scope() as session:
        existing = session.query(IndicatorDefinition).filter_by(key=key).first()
        if existing:
            raise ValueError(f"指标已存在: {key}")
        row = IndicatorDefinition(
            key=key,
            name=name.strip() or key,
            engine=engine_key,
            description=description.strip() if description else None,
            outputs=deepcopy(engine_spec["outputs"]),
            params=normalized_params,
            is_builtin=False,
        )
        session.add(row)
        session.flush()
        return _indicator_row_payload(row)


def get_builtin_template_catalog() -> list[dict[str, Any]]:
    indicator_map = get_indicator_registry_map()
    contract = editor_contract()
    catalog: list[dict[str, Any]] = []
    for template_key, spec in BUILTIN_TEMPLATE_DEFINITIONS.items():
        catalog.append(
            _template_payload(
                template_key, spec, indicator_map, contract, is_builtin=True
            )
        )
    return catalog


def get_template_catalog() -> list[dict[str, Any]]:
    indicator_map = get_indicator_registry_map()
    contract = editor_contract()
    catalog = {item["template"]: item for item in get_builtin_template_catalog()}
    with session_scope() as session:
        rows = (
            session.query(StrategyTemplateDefinition)
            .order_by(StrategyTemplateDefinition.key.asc())
            .all()
        )
        for row in rows:
            catalog[row.key] = _template_row_payload(row, indicator_map, contract)
    return sorted(
        catalog.values(),
        key=lambda item: (item.get("is_builtin") is False, item["name"].lower()),
    )


def get_template_spec(template: str) -> dict[str, Any]:
    for item in get_template_catalog():
        if item["template"] == template:
            return item
    raise ValueError(f"不支持的策略模板: {template}")


def get_template_runtime_contract(template: str) -> dict[str, Any]:
    return get_template_runtime(template)


def create_template_definition(
    *,
    key: str,
    name: str,
    category: str,
    description: str | None,
    indicator_keys: list[str],
    default_config: dict[str, Any],
    default_parameter_space: dict[str, list[Any]] | None,
) -> dict[str, Any]:
    key = normalize_strategy_identifier(key, "模板标识")
    if key in BUILTIN_TEMPLATE_DEFINITIONS:
        raise ValueError("该模板标识已被内置模板占用")
    indicator_map = get_indicator_registry_map()
    merged_indicator_keys = list(
        dict.fromkeys(
            [
                *indicator_keys,
                *[
                    item.get("type")
                    for item in (default_config.get("indicators") or {}).values()
                    if item.get("type")
                ],
            ]
        )
    )
    missing = [
        indicator_key
        for indicator_key in merged_indicator_keys
        if indicator_key not in indicator_map
    ]
    if missing:
        raise ValueError(f"存在未注册的指标: {', '.join(missing)}")
    normalized_config = normalize_strategy_config(
        default_config, blank_strategy_config()
    )
    normalized_parameter_space = normalize_parameter_space(
        default_parameter_space or {}
    )
    with session_scope() as session:
        existing = session.query(StrategyTemplateDefinition).filter_by(key=key).first()
        if existing:
            raise ValueError(f"模板已存在: {key}")
        row = StrategyTemplateDefinition(
            key=key,
            name=name.strip() or key,
            category=category.strip() or "custom",
            description=description.strip() if description else None,
            indicator_keys=merged_indicator_keys,
            default_config=normalized_config,
            default_parameter_space=normalized_parameter_space,
            is_builtin=False,
        )
        session.add(row)
        session.flush()
    return get_template_spec(key)


def get_builtin_strategy_definitions() -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for template_key, spec in BUILTIN_TEMPLATE_DEFINITIONS.items():
        builtin = spec["builtin"]
        result.append(
            {
                "key": builtin["key"],
                "name": spec["name"],
                "template": template_key,
                "category": spec["category"],
                "description": spec["description"],
                "versions": [
                    {
                        "version": 1,
                        "name": builtin["version_name"],
                        "notes": builtin["notes"],
                        "is_default": True,
                        "config": normalize_strategy_config(
                            deepcopy(spec["config"]), blank_strategy_config()
                        ),
                        "parameter_space": deepcopy(spec["parameter_space"]),
                    }
                ],
            }
        )
    return result


def _indicator_row_payload(row: IndicatorDefinition) -> dict[str, Any]:
    return {
        "key": row.key,
        "engine": row.engine,
        "name": row.name,
        "description": row.description,
        "outputs": deepcopy(row.outputs or []),
        "params": deepcopy(row.params or []),
        "is_builtin": False,
    }


def _template_payload(
    template_key: str,
    spec: dict[str, Any],
    indicator_map: dict[str, dict[str, Any]],
    contract: dict[str, Any],
    *,
    is_builtin: bool,
) -> dict[str, Any]:
    runtime = get_template_runtime(template_key)
    return {
        "template": template_key,
        "name": spec["name"],
        "category": spec["category"],
        "description": spec["description"],
        "is_builtin": is_builtin,
        "template_runtime": runtime,
        "indicator_keys": list(spec["indicator_keys"]),
        "indicator_registry": [
            deepcopy(indicator_map[indicator_key])
            for indicator_key in spec["indicator_keys"]
            if indicator_key in indicator_map
        ],
        "operators": deepcopy(contract["operators"]),
        "group_logics": deepcopy(contract["group_logics"]),
        "default_config": normalize_strategy_config(
            deepcopy(spec["config"]), contract["blank_config"]
        ),
        "default_parameter_space": deepcopy(spec["parameter_space"]),
    }


def _template_row_payload(
    row: StrategyTemplateDefinition,
    indicator_map: dict[str, dict[str, Any]],
    contract: dict[str, Any],
) -> dict[str, Any]:
    indicator_keys = list(row.indicator_keys or [])
    runtime = get_template_runtime(row.key)
    return {
        "template": row.key,
        "name": row.name,
        "category": row.category,
        "description": row.description,
        "is_builtin": False,
        "template_runtime": runtime,
        "indicator_keys": indicator_keys,
        "indicator_registry": [
            deepcopy(indicator_map[indicator_key])
            for indicator_key in indicator_keys
            if indicator_key in indicator_map
        ],
        "operators": deepcopy(contract["operators"]),
        "group_logics": deepcopy(contract["group_logics"]),
        "default_config": normalize_strategy_config(
            deepcopy(row.default_config or {}), contract["blank_config"]
        ),
        "default_parameter_space": deepcopy(row.default_parameter_space or {}),
    }
