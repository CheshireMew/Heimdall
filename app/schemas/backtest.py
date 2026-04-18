from __future__ import annotations

from datetime import date, timedelta
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
from app.services.backtest.contracts import (
    BacktestStartCommand,
    CreateIndicatorDefinitionCommand,
    CreateStrategyTemplateCommand,
    CreateStrategyVersionCommand,
    PaperStartCommand,
)
from app.services.backtest.models import PortfolioConfigRecord, ResearchConfigRecord
from app.services.backtest.run_form_contract import (
    DEFAULT_FEE_RATE,
    DEFAULT_HISTORY_MODE,
    DEFAULT_INITIAL_CASH,
    DEFAULT_PORTFOLIO,
    DEFAULT_RANGE_DAYS,
    DEFAULT_RESEARCH,
    DEFAULT_STRATEGY_KEY,
    DEFAULT_TIMEFRAME,
    OPTIMIZE_METRIC_OPTIONS,
    default_backtest_dates,
)


class BacktestPortfolioRequest(BaseModel):
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
    def validate_portfolio(self) -> "BacktestPortfolioRequest":
        if not self.symbols:
            raise ValueError("至少选择一个交易对")
        if self.stake_mode == "fixed" and self.position_size_pct * self.max_open_trades > 100:
            raise ValueError("固定仓位下，单笔仓位百分比乘以最大持仓数不能超过 100")
        return self


class BacktestResearchRequest(BaseModel):
    slippage_bps: float = Field(default=DEFAULT_RESEARCH["slippage_bps"], ge=0, le=1000)
    funding_rate_daily: float = Field(default=DEFAULT_RESEARCH["funding_rate_daily"], ge=-10, le=10)
    in_sample_ratio: float = Field(default=DEFAULT_RESEARCH["in_sample_ratio"], ge=50, le=100)
    optimize_metric: Literal["sharpe", "profit_pct", "calmar", "profit_factor"] = DEFAULT_RESEARCH["optimize_metric"]
    optimize_trials: int = Field(default=DEFAULT_RESEARCH["optimize_trials"], ge=0, le=500)
    rolling_windows: int = Field(default=DEFAULT_RESEARCH["rolling_windows"], ge=0, le=24)


class BacktestStartRequest(BaseModel):
    strategy_key: str = DEFAULT_STRATEGY_KEY
    strategy_version: int | None = None
    timeframe: str = DEFAULT_TIMEFRAME
    start_date: date = Field(default_factory=lambda: default_backtest_dates()[0])
    end_date: date = Field(default_factory=lambda: default_backtest_dates()[1])
    initial_cash: float = Field(default=DEFAULT_INITIAL_CASH, gt=0)
    fee_rate: float = Field(default=DEFAULT_FEE_RATE, ge=0, le=100)
    portfolio: BacktestPortfolioRequest = Field(default_factory=BacktestPortfolioRequest)
    research: BacktestResearchRequest = Field(default_factory=BacktestResearchRequest)

    @model_validator(mode="after")
    def validate_range(self) -> "BacktestStartRequest":
        if self.start_date >= self.end_date:
            raise ValueError("开始日期必须早于结束日期")
        if (self.end_date - self.start_date).days < 7:
            raise ValueError("回测区间至少需要 7 天")
        if (self.end_date - self.start_date).days > 3650:
            raise ValueError("回测区间不能超过 3650 天")
        return self

    def to_command(self) -> BacktestStartCommand:
        from datetime import datetime, time, timezone

        return BacktestStartCommand(
            strategy_key=self.strategy_key,
            strategy_version=self.strategy_version,
            timeframe=self.timeframe,
            start_date=datetime.combine(self.start_date, time.min, tzinfo=timezone.utc),
            end_date=datetime.combine(self.end_date, time.max, tzinfo=timezone.utc),
            initial_cash=self.initial_cash,
            fee_rate=self.fee_rate,
            portfolio=PortfolioConfigRecord(
                symbols=list(self.portfolio.symbols),
                max_open_trades=self.portfolio.max_open_trades,
                position_size_pct=self.portfolio.position_size_pct,
                stake_mode=self.portfolio.stake_mode,
            ),
            research=ResearchConfigRecord(
                slippage_bps=self.research.slippage_bps,
                funding_rate_daily=self.research.funding_rate_daily,
                in_sample_ratio=self.research.in_sample_ratio,
                optimize_metric=self.research.optimize_metric,
                optimize_trials=self.research.optimize_trials,
                rolling_windows=self.research.rolling_windows,
            ),
        )


class BacktestStartResponse(BaseModel):
    success: bool
    backtest_id: int
    message: str


class PaperStartRequest(BaseModel):
    strategy_key: str = DEFAULT_STRATEGY_KEY
    strategy_version: int | None = None
    timeframe: str = DEFAULT_TIMEFRAME
    initial_cash: float = Field(default=DEFAULT_INITIAL_CASH, gt=0)
    fee_rate: float = Field(default=DEFAULT_FEE_RATE, ge=0, le=100)
    portfolio: BacktestPortfolioRequest = Field(default_factory=BacktestPortfolioRequest)

    def to_command(self) -> PaperStartCommand:
        return PaperStartCommand(
            strategy_key=self.strategy_key,
            strategy_version=self.strategy_version,
            timeframe=self.timeframe,
            initial_cash=self.initial_cash,
            fee_rate=self.fee_rate,
            portfolio=PortfolioConfigRecord(
                symbols=list(self.portfolio.symbols),
                max_open_trades=self.portfolio.max_open_trades,
                position_size_pct=self.portfolio.position_size_pct,
                stake_mode=self.portfolio.stake_mode,
            ),
        )


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
    runtime: "StrategyRunProfileResponse"


class StrategyTemplateCapabilitiesResponse(BaseModel):
    signal_runtime: bool = True
    paper: bool = True
    version_editing: bool = True


class StrategyTemplateRuntimeResponse(BaseModel):
    builder_kind: str = "rules"
    capabilities: StrategyTemplateCapabilitiesResponse = Field(default_factory=StrategyTemplateCapabilitiesResponse)


class StrategyDefinitionResponse(BaseModel):
    key: str
    name: str
    template: str
    category: str
    description: str | None = None
    is_active: bool
    template_runtime: StrategyTemplateRuntimeResponse = Field(default_factory=StrategyTemplateRuntimeResponse)
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


class StrategyRunProfileResponse(BaseModel):
    indicator_timeframes: list[str] = Field(default_factory=list)
    allowed_run_timeframes: list[str] = Field(default_factory=list)
    preferred_run_timeframe: str


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
    template_runtime: StrategyTemplateRuntimeResponse = Field(default_factory=StrategyTemplateRuntimeResponse)
    indicator_keys: list[str] = Field(default_factory=list)
    indicator_registry: list[StrategyIndicatorRegistryResponse]
    operators: list[StrategyOperatorResponse]
    group_logics: list[StrategyGroupLogicResponse]
    default_config: StrategyTemplateConfigResponse
    default_parameter_space: dict[str, list[Any]]


class BacktestRunDefaultsResponse(BaseModel):
    strategy_key: str = DEFAULT_STRATEGY_KEY
    timeframe: str = DEFAULT_TIMEFRAME
    start_date: str = Field(default_factory=lambda: default_backtest_dates()[0].isoformat())
    end_date: str = Field(default_factory=lambda: default_backtest_dates()[1].isoformat())
    initial_cash: float = DEFAULT_INITIAL_CASH
    fee_rate: float = DEFAULT_FEE_RATE
    portfolio: BacktestPortfolioRequest = Field(default_factory=BacktestPortfolioRequest)
    research: BacktestResearchRequest = Field(default_factory=BacktestResearchRequest)
    history_mode: Literal["backtest", "paper"] = DEFAULT_HISTORY_MODE
    optimize_metric_options: list[StrategyOperatorResponse] = Field(
        default_factory=lambda: [StrategyOperatorResponse(**item) for item in OPTIMIZE_METRIC_OPTIONS]
    )


class StrategyEditorContractResponse(BaseModel):
    operators: list[StrategyOperatorResponse]
    group_logics: list[StrategyGroupLogicResponse]
    timeframe_options: list[StrategyOperatorResponse]
    market_type_options: list[StrategyOperatorResponse]
    direction_options: list[StrategyOperatorResponse]
    blank_condition: StrategyConditionNodeResponse
    blank_group: StrategyGroupNodeResponse
    blank_config: StrategyTemplateConfigResponse
    run_defaults: BacktestRunDefaultsResponse


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

    def to_command(self) -> CreateStrategyVersionCommand:
        return CreateStrategyVersionCommand(
            key=self.key,
            name=self.name,
            template=self.template,
            category=self.category,
            description=self.description,
            config=self.config,
            parameter_space=self.parameter_space,
            notes=self.notes,
            make_default=self.make_default,
        )


class IndicatorDefinitionCreateRequest(BaseModel):
    key: str
    name: str
    engine_key: str
    description: str | None = None
    params: list[StrategyIndicatorParamResponse] = Field(default_factory=list)

    def to_command(self) -> CreateIndicatorDefinitionCommand:
        return CreateIndicatorDefinitionCommand(
            key=self.key,
            name=self.name,
            engine_key=self.engine_key,
            description=self.description,
            params=list(self.params),
        )


class StrategyTemplateCreateRequest(BaseModel):
    key: str
    name: str
    category: str
    description: str | None = None
    indicator_keys: list[str] = Field(default_factory=list)
    default_config: StrategyTemplateConfigResponse
    default_parameter_space: dict[str, list[Any]] = Field(default_factory=dict)

    def to_command(self) -> CreateStrategyTemplateCommand:
        return CreateStrategyTemplateCommand(
            key=self.key,
            name=self.name,
            category=self.category,
            description=self.description,
            indicator_keys=list(self.indicator_keys),
            default_config=self.default_config,
            default_parameter_space=self.default_parameter_space,
        )
