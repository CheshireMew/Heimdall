from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class StrategyVersionRecord:
    strategy_key: str
    strategy_name: str
    version: int
    template: str
    config: dict[str, Any]
    parameter_space: dict[str, list[Any]] = field(default_factory=dict)
    description: str | None = None
    notes: str | None = None
    version_name: str | None = None
    id: int | None = None
    is_default: bool = False


@dataclass(slots=True)
class PortfolioConfigRecord:
    symbols: list[str]
    max_open_trades: int
    position_size_pct: float
    stake_mode: str = "fixed"


@dataclass(slots=True)
class ResearchConfigRecord:
    slippage_bps: float = 0.0
    funding_rate_daily: float = 0.0
    in_sample_ratio: float = 100.0
    optimize_metric: str = "sharpe"
    optimize_trials: int = 0
    rolling_windows: int = 0


@dataclass(slots=True)
class BacktestSignalRecord:
    timestamp: datetime
    price: float
    signal: str
    confidence: float
    indicators: dict[str, Any] | None = None
    reasoning: str | None = None


@dataclass(slots=True)
class BacktestTradeRecord:
    opened_at: datetime
    closed_at: datetime | None
    entry_price: float
    exit_price: float | None
    stake_amount: float
    amount: float
    profit_abs: float
    profit_pct: float
    max_drawdown_pct: float | None = None
    duration_minutes: int | None = None
    entry_tag: str | None = None
    exit_reason: str | None = None
    leverage: float = 1.0
    pair: str | None = None
    side: str = "long"


@dataclass(slots=True)
class BacktestEquityPointRecord:
    timestamp: datetime
    equity: float
    pnl_abs: float
    drawdown_pct: float


@dataclass(slots=True)
class BacktestExecutionResult:
    total_candles: int
    signals: list[BacktestSignalRecord] = field(default_factory=list)
    trades: list[BacktestTradeRecord] = field(default_factory=list)
    equity_curve: list[BacktestEquityPointRecord] = field(default_factory=list)
    report: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
