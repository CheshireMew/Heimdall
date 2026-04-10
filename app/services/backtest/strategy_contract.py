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

TIMEFRAME_OPTIONS: list[dict[str, str]] = [
    {"key": "base", "label": "跟随运行周期"},
    {"key": "1m", "label": "1 分钟"},
    {"key": "5m", "label": "5 分钟"},
    {"key": "15m", "label": "15 分钟"},
    {"key": "1h", "label": "1 小时"},
    {"key": "4h", "label": "4 小时"},
    {"key": "1d", "label": "1 天"},
]

RUN_TIMEFRAME_KEYS: list[str] = [item["key"] for item in TIMEFRAME_OPTIONS if item["key"] != "base"]

MARKET_TYPE_OPTIONS: list[dict[str, str]] = [
    {"key": "spot", "label": "现货"},
    {"key": "futures", "label": "合约"},
]

DIRECTION_OPTIONS: list[dict[str, str]] = [
    {"key": "long_only", "label": "只做多"},
    {"key": "long_short", "label": "多空双向"},
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


def execution_defaults() -> dict[str, Any]:
    return {
        "market_type": "spot",
        "direction": "long_only",
    }


def branch_defaults(branch_id: str, label: str, *, enabled: bool = True) -> dict[str, Any]:
    return {
        "id": branch_id,
        "label": label,
        "enabled": enabled,
        "regime": build_group(f"{branch_id}_regime", f"{label}状态", "and", []),
        "long_entry": build_group(f"{branch_id}_long_entry", f"{label}做多入场", "and", [], enabled=True),
        "long_exit": build_group(f"{branch_id}_long_exit", f"{label}做多离场", "or", [], enabled=True),
        "short_entry": build_group(f"{branch_id}_short_entry", f"{label}做空入场", "and", [], enabled=False),
        "short_exit": build_group(f"{branch_id}_short_exit", f"{label}做空离场", "or", [], enabled=False),
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
        "execution": execution_defaults(),
        "regime_priority": ["trend", "range"],
        "trend": branch_defaults("trend", "趋势", enabled=True),
        "range": branch_defaults("range", "区间", enabled=False),
        "risk": risk_defaults(),
    }


def editor_contract() -> dict[str, Any]:
    return {
        "operators": deepcopy(RULE_OPERATORS),
        "group_logics": deepcopy(GROUP_LOGICS),
        "timeframe_options": deepcopy(TIMEFRAME_OPTIONS),
        "market_type_options": deepcopy(MARKET_TYPE_OPTIONS),
        "direction_options": deepcopy(DIRECTION_OPTIONS),
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


def timeframe_to_minutes(timeframe: str) -> int:
    mapping = {
        "1m": 1,
        "5m": 5,
        "15m": 15,
        "1h": 60,
        "4h": 240,
        "1d": 1440,
    }
    if timeframe not in mapping:
        raise ValueError(f"不支持的时间周期: {timeframe}")
    return mapping[timeframe]


def explicit_indicator_timeframes(config: dict[str, Any]) -> list[str]:
    normalized: set[str] = set()
    for indicator in (config.get("indicators") or {}).values():
        if not isinstance(indicator, dict):
            continue
        timeframe = normalize_indicator_timeframe(indicator.get("timeframe"))
        if timeframe != "base":
            normalized.add(timeframe)
    return sorted(normalized, key=timeframe_to_minutes)


def preferred_run_timeframe(config: dict[str, Any]) -> str:
    indicator_timeframes = explicit_indicator_timeframes(config)
    return indicator_timeframes[0] if indicator_timeframes else RUN_TIMEFRAME_KEYS[3]


def allowed_run_timeframes(config: dict[str, Any]) -> list[str]:
    indicator_timeframes = explicit_indicator_timeframes(config)
    if not indicator_timeframes:
        return list(RUN_TIMEFRAME_KEYS)
    smallest_minutes = timeframe_to_minutes(indicator_timeframes[0])
    allowed = []
    for timeframe in RUN_TIMEFRAME_KEYS:
        base_minutes = timeframe_to_minutes(timeframe)
        if smallest_minutes >= base_minutes and smallest_minutes % base_minutes == 0:
            allowed.append(timeframe)
    return allowed or [preferred_run_timeframe(config)]


def strategy_runtime_profile(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "indicator_timeframes": explicit_indicator_timeframes(config),
        "allowed_run_timeframes": allowed_run_timeframes(config),
        "preferred_run_timeframe": preferred_run_timeframe(config),
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
    source_config = migrate_legacy_config(config)
    normalized["indicators"] = normalize_indicators(source_config.get("indicators") or normalized.get("indicators") or {})
    normalized["execution"] = normalize_execution(source_config.get("execution") or normalized.get("execution") or {})
    normalized["regime_priority"] = normalize_regime_priority(
        source_config.get("regime_priority"),
        normalized.get("regime_priority") or ["trend", "range"],
    )
    normalized["trend"] = normalize_branch_node(
        source_config.get("trend"),
        normalized.get("trend") or branch_defaults("trend", "趋势", enabled=True),
        "trend",
        "趋势",
    )
    normalized["range"] = normalize_branch_node(
        source_config.get("range"),
        normalized.get("range") or branch_defaults("range", "区间", enabled=False),
        "range",
        "区间",
    )
    normalized["risk"] = normalize_risk(source_config.get("risk") or {}, normalized.get("risk") or {})
    return normalized


def normalize_indicators(indicators: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for indicator_id, indicator in (indicators or {}).items():
        indicator_key = str(indicator_id or "").strip()
        if not indicator_key or not isinstance(indicator, dict):
            continue
        normalized[indicator_key] = {
            "label": str(indicator.get("label") or indicator_key),
            "type": str(indicator.get("type") or "").strip(),
            "timeframe": normalize_indicator_timeframe(indicator.get("timeframe")),
            "params": deepcopy(indicator.get("params") or {}),
        }
    return normalized


def normalize_indicator_timeframe(value: Any) -> str:
    timeframe = str(value or "base").strip()
    valid_keys = {item["key"] for item in TIMEFRAME_OPTIONS}
    return timeframe if timeframe in valid_keys else "base"


def normalize_execution(value: dict[str, Any]) -> dict[str, Any]:
    market_type = str((value or {}).get("market_type") or "spot").strip()
    direction = str((value or {}).get("direction") or "long_only").strip()
    if market_type not in {"spot", "futures"}:
        market_type = "spot"
    if direction not in {"long_only", "long_short"}:
        direction = "long_only"
    if market_type == "spot":
        direction = "long_only"
    return {
        "market_type": market_type,
        "direction": direction,
    }


def normalize_regime_priority(value: Any, fallback: list[str] | None = None) -> list[str]:
    normalized: list[str] = []
    for item in value or []:
        branch_key = str(item or "").strip()
        if branch_key not in {"trend", "range"} or branch_key in normalized:
            continue
        normalized.append(branch_key)
    for item in fallback or ["trend", "range"]:
        if item in {"trend", "range"} and item not in normalized:
            normalized.append(item)
    return normalized or ["trend", "range"]


def normalize_branch_node(branch: dict[str, Any] | None, fallback: dict[str, Any], branch_id: str, label: str) -> dict[str, Any]:
    base = deepcopy(fallback or branch_defaults(branch_id, label))
    source = deepcopy(branch or base)
    if not isinstance(source, dict):
        source = deepcopy(base)
    return {
        "id": source.get("id") or base.get("id") or branch_id,
        "label": source.get("label") or base.get("label") or label,
        "enabled": bool(source.get("enabled", base.get("enabled", True))),
        "regime": normalize_group_node(
            source.get("regime"),
            base.get("regime") or build_group(f"{branch_id}_regime", f"{label}状态", "and", []),
            f"{branch_id}_regime",
            f"{label}状态",
        ),
        "long_entry": normalize_group_node(
            source.get("long_entry"),
            base.get("long_entry") or build_group(f"{branch_id}_long_entry", f"{label}做多入场", "and", []),
            f"{branch_id}_long_entry",
            f"{label}做多入场",
        ),
        "long_exit": normalize_group_node(
            source.get("long_exit"),
            base.get("long_exit") or build_group(f"{branch_id}_long_exit", f"{label}做多离场", "or", []),
            f"{branch_id}_long_exit",
            f"{label}做多离场",
        ),
        "short_entry": normalize_group_node(
            source.get("short_entry"),
            base.get("short_entry") or build_group(f"{branch_id}_short_entry", f"{label}做空入场", "and", [], enabled=False),
            f"{branch_id}_short_entry",
            f"{label}做空入场",
        ),
        "short_exit": normalize_group_node(
            source.get("short_exit"),
            base.get("short_exit") or build_group(f"{branch_id}_short_exit", f"{label}做空离场", "or", [], enabled=False),
            f"{branch_id}_short_exit",
            f"{label}做空离场",
        ),
    }


def normalize_group_node(node: dict[str, Any] | None, fallback: dict[str, Any], node_id: str, label: str) -> dict[str, Any]:
    base = deepcopy(fallback or build_group(node_id, label, "and", []))
    source = deepcopy(node or base)
    if source.get("node_type") != "group":
        source = build_group(node_id, label, base.get("logic", "and"), source.get("children") or [], enabled=base.get("enabled", True))
    source["id"] = source.get("id") or node_id
    source["label"] = source.get("label") or label
    source["logic"] = source.get("logic") if source.get("logic") in {"and", "or"} else base.get("logic", "and")
    source["enabled"] = bool(source.get("enabled", base.get("enabled", True)))
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


def migrate_legacy_config(config: dict[str, Any]) -> dict[str, Any]:
    if "trend" in config or "range" in config:
        migrated = deepcopy(config)
        for branch_key, label in (("trend", "趋势"), ("range", "区间")):
            branch = migrated.get(branch_key)
            if not isinstance(branch, dict):
                continue
            if "long_entry" in branch or "short_entry" in branch:
                continue
            branch["long_entry"] = deepcopy(branch.pop("entry", build_group(f"{branch_key}_long_entry", f"{label}做多入场", "and", [])))
            branch["long_exit"] = deepcopy(branch.pop("exit", build_group(f"{branch_key}_long_exit", f"{label}做多离场", "or", [])))
            branch["short_entry"] = deepcopy(branch_defaults(branch_key, label)["short_entry"])
            branch["short_exit"] = deepcopy(branch_defaults(branch_key, label)["short_exit"])
        if "execution" not in migrated:
            migrated["execution"] = execution_defaults()
        return migrated

    migrated = {
        "indicators": deepcopy(config.get("indicators") or {}),
        "execution": execution_defaults(),
        "regime_priority": ["trend", "range"],
        "trend": branch_defaults("trend", "趋势", enabled=True),
        "range": branch_defaults("range", "区间", enabled=False),
        "risk": deepcopy(config.get("risk") or risk_defaults()),
    }
    migrated["trend"]["regime"] = build_group("trend_regime", "趋势状态", "and", [])
    migrated["trend"]["long_entry"] = deepcopy(config.get("entry") or build_group("trend_long_entry", "趋势做多入场", "and", []))
    migrated["trend"]["long_exit"] = deepcopy(config.get("exit") or build_group("trend_long_exit", "趋势做多离场", "or", []))
    return migrated
