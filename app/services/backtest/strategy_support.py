from __future__ import annotations

from typing import Any

from app.contracts.backtest import StrategyVersionRecord
from app.services.backtest.strategy_catalog import get_template_spec
from app.services.backtest.strategy_contract import (
    normalize_strategy_payload,
    strategy_runtime_profile,
)


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


def build_strategy_version_response_payload(
    record: StrategyVersionRecord,
) -> dict[str, Any]:
    normalized_config, normalized_parameter_space = normalize_strategy_version_payload(
        record.template,
        record.config,
        record.parameter_space,
    )
    return {
        "id": record.id,
        "version": record.version,
        "name": record.version_name or record.strategy_name,
        "notes": record.notes,
        "is_default": record.is_default,
        "config": normalized_config,
        "parameter_space": normalized_parameter_space,
        "runtime": strategy_runtime_profile(normalized_config),
    }
