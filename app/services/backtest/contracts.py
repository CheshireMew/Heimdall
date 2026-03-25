from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.services.backtest.models import PortfolioConfigRecord, ResearchConfigRecord


@dataclass(slots=True)
class BacktestStartCommand:
    strategy_key: str
    strategy_version: int | None
    timeframe: str
    days: int
    initial_cash: float
    fee_rate: float
    portfolio: PortfolioConfigRecord
    research: ResearchConfigRecord


@dataclass(slots=True)
class CreateIndicatorDefinitionCommand:
    key: str
    name: str
    engine_key: str
    description: str | None = None
    params: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class CreateStrategyTemplateCommand:
    key: str
    name: str
    category: str
    description: str | None = None
    indicator_keys: list[str] = field(default_factory=list)
    default_config: dict[str, Any] = field(default_factory=dict)
    default_parameter_space: dict[str, list[Any]] = field(default_factory=dict)


@dataclass(slots=True)
class CreateStrategyVersionCommand:
    key: str
    name: str
    template: str
    category: str
    description: str | None = None
    config: dict[str, Any] = field(default_factory=dict)
    parameter_space: dict[str, list[Any]] = field(default_factory=dict)
    notes: str | None = None
    make_default: bool = True
