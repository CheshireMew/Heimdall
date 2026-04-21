from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FactorExecutionConfig:
    research_run_id: int
    initial_cash: float
    fee_rate: float
    position_size_pct: float
    stake_mode: str = "fixed"
    entry_threshold: float | None = None
    exit_threshold: float | None = None
    stoploss_pct: float = -0.08
    takeprofit_pct: float = 0.16
    max_hold_bars: int = 20
