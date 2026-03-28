from __future__ import annotations

from typing import Any

from app.services.backtest.strategy_catalog import get_template_spec
from app.services.backtest.strategy_contract import normalize_strategy_payload


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
