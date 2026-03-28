from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.strategy_contract import (
    StrategyConditionNodeResponse,
    StrategyGroupNodeResponse,
    StrategyIndicatorOutputResponse,
    StrategyIndicatorParamResponse,
    StrategyTemplateConfigResponse,
)
from app.schemas.backtest_result import BacktestReportResponse, BacktestRunMetadataResponse


class BacktestPortfolioRequest(BaseModel):
    symbols: list[str] = Field(default_factory=lambda: ["BTC/USDT", "ETH/USDT"])
    max_open_trades: int = Field(default=2, ge=1, le=50)
    position_size_pct: float = Field(default=25.0, gt=0, le=100)
    stake_mode: Literal["fixed", "unlimited"] = "fixed"

    @field_validator("symbols", mode="before")
    @classmethod
    def parse_symbols(cls, value: Any) -> list[str]:
        if isinstance(value, str):
            return [symbol.strip() for symbol in value.split(",") if symbol.strip()]
        return value

    @model_validator(mode="after")
    def validate_portfolio(self) -> "BacktestPortfolioRequest":
        if not self.symbols:
            raise ValueError("至少选择一个交易对")
        if self.stake_mode == "fixed" and self.position_size_pct * self.max_open_trades > 100:
            raise ValueError("固定仓位下，单笔仓位百分比乘以最大持仓数不能超过 100")
        return self


class BacktestResearchRequest(BaseModel):
    slippage_bps: float = Field(default=5.0, ge=0, le=1000)
    funding_rate_daily: float = Field(default=0.0, ge=-10, le=10)
    in_sample_ratio: float = Field(default=70.0, ge=50, le=100)
    optimize_metric: Literal["sharpe", "profit_pct", "calmar", "profit_factor"] = "sharpe"
    optimize_trials: int = Field(default=12, ge=0, le=500)
    rolling_windows: int = Field(default=3, ge=0, le=24)


class BacktestStartRequest(BaseModel):
    strategy_key: str = "ema_rsi_macd"
    strategy_version: int | None = None
    timeframe: str = "1h"
    days: int = Field(default=180, ge=7, le=3650)
    initial_cash: float = Field(default=100000.0, gt=0)
    fee_rate: float = Field(default=0.1, ge=0, le=100)
    portfolio: BacktestPortfolioRequest = Field(default_factory=BacktestPortfolioRequest)
    research: BacktestResearchRequest = Field(default_factory=BacktestResearchRequest)


class BacktestStartResponse(BaseModel):
    success: bool
    backtest_id: int
    message: str


class PaperStartRequest(BaseModel):
    strategy_key: str = "ema_rsi_macd"
    strategy_version: int | None = None
    timeframe: str = "1h"
    initial_cash: float = Field(default=100000.0, gt=0)
    fee_rate: float = Field(default=0.1, ge=0, le=100)
    portfolio: BacktestPortfolioRequest = Field(default_factory=BacktestPortfolioRequest)


class PaperStartResponse(BaseModel):
    success: bool
    run_id: int
    message: str


class PaperStopResponse(BaseModel):
    success: bool
    run_id: int
    message: str


class BacktestDeleteResponse(BaseModel):
    success: bool
    run_id: int
    message: str


class BacktestMetricsResponse(BaseModel):
    total_candles: int
    total_signals: int
    buy_signals: int
    sell_signals: int
    hold_signals: int


class BacktestSignalResponse(BaseModel):
    id: int
    timestamp: str | None
    price: float
    signal: str
    confidence: float
    indicators: dict[str, Any] | None = None
    reasoning: str | None = None


class BacktestTradeResponse(BaseModel):
    id: int
    pair: str
    opened_at: str | None
    closed_at: str | None
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
    leverage: float


class BacktestEquityPointResponse(BaseModel):
    id: int
    timestamp: str | None
    equity: float
    pnl_abs: float
    drawdown_pct: float


class BacktestRunResponse(BaseModel):
    id: int
    symbol: str
    timeframe: str
    start_date: str | None
    end_date: str | None
    status: str
    metadata: BacktestRunMetadataResponse | None = None
    report: BacktestReportResponse | None = None
    created_at: str | None
    metrics: BacktestMetricsResponse
    signals: list[BacktestSignalResponse] | None = None


class PaginationResponse(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class BacktestDetailResponse(BacktestRunResponse):
    signals: list[BacktestSignalResponse]
    trades: list[BacktestTradeResponse]
    equity_curve: list[BacktestEquityPointResponse]
    pagination: PaginationResponse


class StrategyVersionResponse(BaseModel):
    id: int
    version: int
    name: str
    notes: str | None = None
    is_default: bool
    config: StrategyTemplateConfigResponse
    parameter_space: dict[str, list[Any]]


class StrategyDefinitionResponse(BaseModel):
    key: str
    name: str
    template: str
    category: str
    description: str | None = None
    is_active: bool
    versions: list[StrategyVersionResponse]


class StrategyIndicatorRegistryResponse(BaseModel):
    key: str
    engine: str
    name: str
    description: str | None = None
    outputs: list[StrategyIndicatorOutputResponse]
    params: list[StrategyIndicatorParamResponse]
    is_builtin: bool


class StrategyOperatorResponse(BaseModel):
    key: str
    label: str


class StrategyGroupLogicResponse(BaseModel):
    key: str
    label: str


class StrategyIndicatorEngineResponse(BaseModel):
    key: str
    engine: str
    name: str
    description: str | None = None
    outputs: list[StrategyIndicatorOutputResponse]
    params: list[StrategyIndicatorParamResponse]


class StrategyTemplateResponse(BaseModel):
    template: str
    name: str
    category: str
    description: str | None = None
    is_builtin: bool = False
    indicator_keys: list[str] = Field(default_factory=list)
    indicator_registry: list[StrategyIndicatorRegistryResponse]
    operators: list[StrategyOperatorResponse]
    group_logics: list[StrategyGroupLogicResponse]
    default_config: StrategyTemplateConfigResponse
    default_parameter_space: dict[str, list[Any]]


class StrategyEditorContractResponse(BaseModel):
    operators: list[StrategyOperatorResponse]
    group_logics: list[StrategyGroupLogicResponse]
    blank_condition: StrategyConditionNodeResponse
    blank_group: StrategyGroupNodeResponse
    blank_config: StrategyTemplateConfigResponse


class StrategyVersionCreateRequest(BaseModel):
    key: str
    name: str
    template: str
    category: str
    description: str | None = None
    config: StrategyTemplateConfigResponse
    parameter_space: dict[str, list[Any]] = Field(default_factory=dict)
    notes: str | None = None
    make_default: bool = True


class IndicatorDefinitionCreateRequest(BaseModel):
    key: str
    name: str
    engine_key: str
    description: str | None = None
    params: list[StrategyIndicatorParamResponse] = Field(default_factory=list)


class StrategyTemplateCreateRequest(BaseModel):
    key: str
    name: str
    category: str
    description: str | None = None
    indicator_keys: list[str] = Field(default_factory=list)
    default_config: StrategyTemplateConfigResponse
    default_parameter_space: dict[str, list[Any]] = Field(default_factory=dict)
