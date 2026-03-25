from __future__ import annotations

from copy import deepcopy
from typing import Any


RULE_OPERATORS: list[dict[str, str]] = [
    {"key": "gt", "label": "大于"},
    {"key": "gte", "label": "大于等于"},
    {"key": "lt", "label": "小于"},
    {"key": "lte", "label": "小于等于"},
]

GROUP_LOGICS: list[dict[str, str]] = [
    {"key": "and", "label": "全部满足"},
    {"key": "or", "label": "满足任一"},
]


def build_condition(
    node_id: str,
    label: str,
    left: dict[str, Any],
    operator: str,
    right: dict[str, Any],
    enabled: bool = True,
) -> dict[str, Any]:
    return {
        "id": node_id,
        "node_type": "condition",
        "label": label,
        "left": left,
        "operator": operator,
        "right": right,
        "enabled": enabled,
    }


def build_group(
    node_id: str,
    label: str,
    logic: str,
    children: list[dict[str, Any]] | None = None,
    enabled: bool = True,
) -> dict[str, Any]:
    return {
        "id": node_id,
        "node_type": "group",
        "label": label,
        "logic": logic,
        "enabled": enabled,
        "children": deepcopy(children or []),
    }


def risk_defaults() -> dict[str, Any]:
    return {
        "stoploss": -0.10,
        "roi_targets": [],
        "trailing": {
            "enabled": False,
            "positive": 0.02,
            "offset": 0.03,
            "only_offset_reached": True,
        },
        "partial_exits": [],
    }


def blank_strategy_config() -> dict[str, Any]:
    return {
        "indicators": {},
        "entry": build_group("entry_root", "入场条件组", "and", []),
        "exit": build_group("exit_root", "离场条件组", "or", []),
        "risk": risk_defaults(),
    }


def editor_contract() -> dict[str, Any]:
    return {
        "operators": deepcopy(RULE_OPERATORS),
        "group_logics": deepcopy(GROUP_LOGICS),
        "blank_condition": build_condition(
            "condition",
            "条件",
            {"kind": "price", "field": "close"},
            "gt",
            {"kind": "value", "value": 0},
        ),
        "blank_group": build_group("group", "条件组", "and", []),
        "blank_config": blank_strategy_config(),
    }


def normalize_indicator_params(params: list[dict[str, Any]], engine_params: list[dict[str, Any]]) -> list[dict[str, Any]]:
    engine_map = {item["key"]: item for item in engine_params}
    normalized = []
    for item in params:
        key = str(item.get("key") or "").strip()
        if not key or key not in engine_map:
            continue
        base = deepcopy(engine_map[key])
        base["label"] = str(item.get("label") or base["label"])
        for field in ("default", "min", "max", "step"):
            if item.get(field) is not None:
                base[field] = item[field]
        normalized.append(base)
    return normalized or deepcopy(engine_params)


def normalize_strategy_config(config: dict[str, Any], default_config: dict[str, Any]) -> dict[str, Any]:
    normalized = deepcopy(default_config or blank_strategy_config())
    if not config:
        return normalized
    normalized["indicators"] = deepcopy(config.get("indicators") or normalized.get("indicators") or {})
    normalized["entry"] = normalize_group_node(
        config.get("entry"),
        normalized.get("entry") or build_group("entry_root", "入场条件组", "and", []),
        "entry_root",
        "入场条件组",
    )
    normalized["exit"] = normalize_group_node(
        config.get("exit"),
        normalized.get("exit") or build_group("exit_root", "离场条件组", "or", []),
        "exit_root",
        "离场条件组",
    )
    normalized["risk"] = normalize_risk(config.get("risk") or {}, normalized.get("risk") or {})
    return normalized


def normalize_group_node(node: dict[str, Any] | None, fallback: dict[str, Any], node_id: str, label: str) -> dict[str, Any]:
    base = deepcopy(fallback or build_group(node_id, label, "and", []))
    source = deepcopy(node or base)
    if source.get("node_type") != "group":
        source = build_group(node_id, label, base.get("logic", "and"), source.get("children") or [])
    source["id"] = source.get("id") or node_id
    source["label"] = source.get("label") or label
    source["logic"] = source.get("logic") if source.get("logic") in {"and", "or"} else base.get("logic", "and")
    source["enabled"] = bool(source.get("enabled", True))
    source["children"] = [normalize_rule_node(child) for child in source.get("children") or []]
    return source


def normalize_rule_node(node: dict[str, Any]) -> dict[str, Any]:
    if (node or {}).get("node_type") == "group":
        return normalize_group_node(
            node,
            build_group(node.get("id") or "group", node.get("label") or "条件组", node.get("logic") or "and", []),
            node.get("id") or "group",
            node.get("label") or "条件组",
        )
    return {
        "id": node.get("id") or "condition",
        "node_type": "condition",
        "label": node.get("label") or "条件",
        "left": deepcopy(node.get("left") or {"kind": "price", "field": "close"}),
        "operator": node.get("operator") if node.get("operator") in {"gt", "gte", "lt", "lte"} else "gt",
        "right": deepcopy(node.get("right") or {"kind": "value", "value": 0}),
        "enabled": bool(node.get("enabled", True)),
    }


def normalize_risk(risk: dict[str, Any], base_risk: dict[str, Any] | None = None) -> dict[str, Any]:
    normalized = deepcopy(base_risk or risk_defaults())
    normalized["stoploss"] = float(risk.get("stoploss", normalized.get("stoploss", risk_defaults()["stoploss"])))

    roi_targets = risk.get("roi_targets")
    if roi_targets is None:
        roi_targets = normalized.get("roi_targets") or []
    normalized["roi_targets"] = [
        {
            "id": item.get("id") or f"roi_{index}",
            "minutes": int(item.get("minutes", 0)),
            "profit": float(item.get("profit", 0)),
            "enabled": bool(item.get("enabled", True)),
        }
        for index, item in enumerate(roi_targets or [])
    ]

    trailing = risk.get("trailing") or deepcopy(normalized.get("trailing") or {})
    normalized["trailing"] = {
        "enabled": bool(trailing.get("enabled", normalized["trailing"]["enabled"])),
        "positive": float(trailing.get("positive", normalized["trailing"]["positive"])),
        "offset": float(trailing.get("offset", normalized["trailing"]["offset"])),
        "only_offset_reached": bool(trailing.get("only_offset_reached", normalized["trailing"]["only_offset_reached"])),
    }

    partial_exits = risk.get("partial_exits")
    if partial_exits is None:
        partial_exits = normalized.get("partial_exits") or []
    normalized["partial_exits"] = [
        {
            "id": item.get("id") or f"partial_{index + 1}",
            "profit": float(item.get("profit", 0)),
            "size_pct": float(item.get("size_pct", 0)),
            "enabled": bool(item.get("enabled", True)),
        }
        for index, item in enumerate(partial_exits or [])
    ]
    return normalized


def normalize_parameter_space(parameter_space: dict[str, list[Any]]) -> dict[str, list[Any]]:
    normalized: dict[str, list[Any]] = {}
    for key, values in (parameter_space or {}).items():
        if not isinstance(values, list):
            continue
        normalized[str(key)] = list(values)
    return normalized


def find_node_in_group(group: dict[str, Any], node_id: str) -> dict[str, Any] | None:
    for child in group.get("children") or []:
        if child.get("id") == node_id:
            return child
        if child.get("node_type") == "group":
            nested = find_node_in_group(child, node_id)
            if nested:
                return nested
    return None


def set_by_path(payload: dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    current: Any = payload
    for part in parts[:-1]:
        if isinstance(current, dict) and current.get("node_type") == "group":
            next_node = find_node_in_group(current, part)
            if next_node is None:
                raise ValueError(f"未找到规则路径: {path}")
            current = next_node
            continue
        if isinstance(current, dict) and part in {"entry", "exit"}:
            current = current.setdefault(part, build_group(f"{part}_root", "条件组", "and", []))
            continue
        if isinstance(current, list):
            current = next((item for item in current if item.get("id") == part), None)
            if current is None:
                raise ValueError(f"未找到列表路径: {path}")
            continue
        current = current.setdefault(part, {})
    current[parts[-1]] = value


def normalize_strategy_payload(
    *,
    template_spec: dict[str, Any],
    config: dict[str, Any],
    parameter_space: dict[str, list[Any]] | None,
) -> tuple[dict[str, Any], dict[str, list[Any]]]:
    default_config = template_spec["default_config"]
    default_parameter_space = template_spec["default_parameter_space"]
    normalized_config = normalize_strategy_config(config or {}, default_config)
    normalized_parameter_space = normalize_parameter_space(parameter_space or default_parameter_space)
    return normalized_config, normalized_parameter_space
