from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

class BacktestReportSnapshotResponse(BaseModel):
    profit_pct: float | None = None
    profit_abs: float | None = None
    final_balance: float | None = None
    max_drawdown_pct: float | None = None
    sharpe: float | None = None
    calmar: float | None = None
    profit_factor: float | None = None
    win_rate: float | None = None
    total_trades: int | None = None


class BacktestDateRangeResponse(BaseModel):
    start: str
    end: str


class BacktestPairBreakdownResponse(BaseModel):
    pair: str
    trades: int
    profit_abs: float
    profit_pct: float
    win_rate: float


class BacktestStrategySummaryResponse(BaseModel):
    key: str
    name: str
    version: int
    template: str


class BacktestPortfolioSummaryResponse(BaseModel):
    symbols: list[str] = Field(default_factory=list)
    max_open_trades: int | None = None
    position_size_pct: float | None = None
    stake_mode: str | None = None
    stake_currency: str | None = None


class BacktestPortfolioPayloadResponse(BaseModel):
    symbols: list[str] = Field(default_factory=list)
    max_open_trades: int | None = None
    position_size_pct: float | None = None
    stake_mode: str | None = None


class BacktestResearchPayloadResponse(BaseModel):
    slippage_bps: float | None = None
    funding_rate_daily: float | None = None
    in_sample_ratio: float | None = None
    optimize_metric: str | None = None
    optimize_trials: int | None = None
    rolling_windows: int | None = None


class BacktestOptimizationTrialResponse(BaseModel):
    trial: int
    score: float | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    report: BacktestReportSnapshotResponse | None = None


class BacktestOptimizationSummaryResponse(BaseModel):
    metric: str
    trial_count: int
    best_score: float | None = None
    best_config: dict[str, Any] = Field(default_factory=dict)
    trials: list[BacktestOptimizationTrialResponse] = Field(default_factory=list)


class BacktestIterationSummaryResponse(BaseModel):
    range: BacktestDateRangeResponse | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    report: BacktestReportSnapshotResponse | None = None


class BacktestRollingWindowResponse(BaseModel):
    index: int
    train: BacktestDateRangeResponse | None = None
    test: BacktestDateRangeResponse
    config: dict[str, Any] = Field(default_factory=dict)
    optimization: BacktestOptimizationSummaryResponse | None = None
    report: BacktestReportSnapshotResponse | None = None


class BacktestResearchReportResponse(BaseModel):
    selected_config: dict[str, Any] = Field(default_factory=dict)
    in_sample_ratio: float
    slippage_bps: float
    funding_rate_daily: float
    optimization: BacktestOptimizationSummaryResponse | None = None
    in_sample: BacktestIterationSummaryResponse | None = None
    out_of_sample: BacktestIterationSummaryResponse | None = None
    rolling_windows: list[BacktestRollingWindowResponse] = Field(default_factory=list)


class BacktestReportResponse(BaseModel):
    initial_cash: float
    final_balance: float
    profit_abs: float
    profit_pct: float
    annualized_return_pct: float | None = None
    max_drawdown_pct: float
    sharpe: float | None = None
    sortino: float | None = None
    calmar: float | None = None
    profit_factor: float | None = None
    expectancy_ratio: float | None = None
    win_rate: float
    total_trades: int
    wins: int
    losses: int
    draws: int
    avg_trade_pct: float | None = None
    avg_trade_duration_minutes: int | None = None
    best_trade_pct: float | None = None
    worst_trade_pct: float | None = None
    pair_breakdown: list[BacktestPairBreakdownResponse] = Field(default_factory=list)
    symbols: list[str] = Field(default_factory=list)
    timeframe: str | None = None
    strategy: BacktestStrategySummaryResponse | None = None
    portfolio: BacktestPortfolioSummaryResponse | None = None
    research: BacktestResearchReportResponse | None = None


class BacktestSampleRangesResponse(BaseModel):
    requested: BacktestDateRangeResponse | None = None
    displayed: BacktestDateRangeResponse | None = None
    in_sample: BacktestDateRangeResponse | None = None
    out_of_sample: BacktestDateRangeResponse | None = None


class BacktestPaperPositionResponse(BaseModel):
    symbol: str
    side: str = "long"
    opened_at: str
    entry_price: float
    remaining_amount: float
    remaining_cost: float
    highest_price: float
    lowest_price: float
    last_price: float
    taken_partial_ids: list[str] = Field(default_factory=list)


class BacktestRuntimeStateResponse(BaseModel):
    cash_balance: float
    last_processed: dict[str, int | None] = Field(default_factory=dict)
    positions: dict[str, BacktestPaperPositionResponse] = Field(default_factory=dict)


class BacktestPaperLiveResponse(BaseModel):
    cash_balance: float
    open_positions: int
    positions: list[BacktestPaperPositionResponse] = Field(default_factory=list)
    last_updated: str
    stop_reason: str | None = None


class BacktestRunMetadataResponse(BaseModel):
    schema_version: int | None = None
    execution_mode: str | None = None
    engine: str | None = None
    exchange: str | None = None
    market_type: str | None = None
    direction: str | None = None
    strategy_key: str | None = None
    strategy_name: str | None = None
    strategy_version: int | None = None
    strategy_template: str | None = None
    strategy_notes: str | None = None
    symbols: list[str] = Field(default_factory=list)
    execution_symbols: list[str] = Field(default_factory=list)
    price_source: str | None = None
    portfolio_label: str | None = None
    initial_cash: float | None = None
    fee_rate: float | None = None
    fee_ratio: float | None = None
    timeframe: str | None = None
    stake_currency: str | None = None
    portfolio: BacktestPortfolioPayloadResponse | None = None
    research: BacktestResearchPayloadResponse | BacktestResearchReportResponse | None = None
    selected_config: dict[str, Any] = Field(default_factory=dict)
    sample_ranges: BacktestSampleRangesResponse | None = None
    runtime_state: BacktestRuntimeStateResponse | None = None
    paper_live: BacktestPaperLiveResponse | None = None
    report: BacktestReportResponse | None = None
    raw_stats: BacktestReportSnapshotResponse | None = None
    error: str | None = None
