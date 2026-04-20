from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.contracts.backtest_defaults import DEFAULT_PORTFOLIO, DEFAULT_RESEARCH
from app.contracts.backtest_symbols import normalize_backtest_symbols

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


class BacktestPortfolioConfig(BaseModel):
    symbols: list[str] = Field(default_factory=lambda: list(DEFAULT_PORTFOLIO["symbols"]))
    max_open_trades: int = Field(default=DEFAULT_PORTFOLIO["max_open_trades"], ge=1, le=50)
    position_size_pct: float = Field(default=DEFAULT_PORTFOLIO["position_size_pct"], gt=0, le=100)
    stake_mode: Literal["fixed", "unlimited"] = DEFAULT_PORTFOLIO["stake_mode"]

    @field_validator("symbols", mode="before")
    @classmethod
    def parse_symbols(cls, value: Any) -> list[str]:
        if isinstance(value, str):
            return [symbol.strip() for symbol in value.split(",") if symbol.strip()]
        return value

    @model_validator(mode="after")
    def validate_portfolio(self) -> "BacktestPortfolioConfig":
        self.symbols = normalize_backtest_symbols(self.symbols)
        if not self.symbols:
            raise ValueError("至少选择一个交易对")
        if self.stake_mode == "fixed" and self.position_size_pct * self.max_open_trades > 100:
            raise ValueError("固定仓位下，单笔仓位百分比乘以最大持仓数不能超过 100")
        return self


class BacktestResearchConfig(BaseModel):
    slippage_bps: float = Field(default=DEFAULT_RESEARCH["slippage_bps"], ge=0, le=1000)
    funding_rate_daily: float = Field(default=DEFAULT_RESEARCH["funding_rate_daily"], ge=-10, le=10)
    in_sample_ratio: float = Field(default=DEFAULT_RESEARCH["in_sample_ratio"], ge=50, le=100)
    optimize_metric: Literal["sharpe", "profit_pct", "calmar", "profit_factor"] = DEFAULT_RESEARCH["optimize_metric"]
    optimize_trials: int = Field(default=DEFAULT_RESEARCH["optimize_trials"], ge=0, le=500)
    rolling_windows: int = Field(default=DEFAULT_RESEARCH["rolling_windows"], ge=0, le=24)


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
    report: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


@dataclass(slots=True)
class BacktestStartCommand:
    strategy_key: str
    strategy_version: int | None
    timeframe: str
    start_date: datetime
    end_date: datetime
    initial_cash: float
    fee_rate: float
    portfolio: BacktestPortfolioConfig
    research: BacktestResearchConfig


@dataclass(slots=True)
class PaperStartCommand:
    strategy_key: str
    strategy_version: int | None
    timeframe: str
    initial_cash: float
    fee_rate: float
    portfolio: BacktestPortfolioConfig


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
