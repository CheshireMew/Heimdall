from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class SimulateDcaCommand:
    symbol: str
    amount: float
    investment_time: str
    timezone: str
    strategy: str
    start_date: str | None = None
    days: int | None = None
    strategy_params: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ComparePairsCommand:
    symbol_a: str
    symbol_b: str
    days: int
    timeframe: str
