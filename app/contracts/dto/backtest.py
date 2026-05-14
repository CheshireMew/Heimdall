from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from app.contracts.strategy import (
    StrategyConditionNodeResponse,
    StrategyGroupNodeResponse,
    StrategyIndicatorOutputResponse,
    StrategyIndicatorParamResponse,
    StrategyTemplateConfigResponse,
)
from app.contracts.json_types import JsonObject, JsonValue
from app.contracts.backtest import (
    BacktestPreviewCommand,
    BacktestPortfolioConfig,
    BacktestResearchConfig,
    BacktestEquityPointRecord,
    BacktestStartCommand,
    BacktestTradeRecord,
    CreateIndicatorDefinitionCommand,
    CreateStrategyTemplateCommand,
    CreateStrategyVersionCommand,
    EvolveStrategyFromBacktestCommand,
    PaperStartCommand,
)
from app.contracts.dto.market import MarketHistoryCoverageResponse, OhlcvPointResponse
from app.contracts.backtest_result import (
    BacktestReportResponse,
    BacktestRunMetadataContractResponse,
)
from app.contracts.backtest_defaults import (
    DEFAULT_FEE_RATE,
    DEFAULT_HISTORY_MODE,
    DEFAULT_INITIAL_CASH,
    DEFAULT_RANGE_DAYS,
    DEFAULT_STRATEGY_KEY,
    DEFAULT_TIMEFRAME,
    OPTIMIZE_METRIC_OPTIONS,
    default_backtest_dates,
)


class BacktestPreviewRequest(BaseModel):
    strategy_key: str = DEFAULT_STRATEGY_KEY
    strategy_version: int | None = None
    timeframe: str = DEFAULT_TIMEFRAME
    start_date: date = Field(default_factory=lambda: default_backtest_dates()[0])
    end_date: date = Field(default_factory=lambda: default_backtest_dates()[1])
    initial_cash: float = Field(default=DEFAULT_INITIAL_CASH, gt=0)
    fee_rate: float = Field(default=DEFAULT_FEE_RATE, ge=0, le=100)
    portfolio: BacktestPortfolioConfig = Field(
        default_factory=BacktestPortfolioConfig
    )
    research: BacktestResearchConfig = Field(default_factory=BacktestResearchConfig)

    @model_validator(mode="after")
    def validate_range(self) -> "BacktestPreviewRequest":
        if self.start_date >= self.end_date:
            raise ValueError("开始日期必须早于结束日期")
        if (self.end_date - self.start_date).days < 7:
            raise ValueError("回测区间至少需要 7 天")
        if (self.end_date - self.start_date).days > 3650:
            raise ValueError("回测区间不能超过 3650 天")
        return self

    def to_preview_command(self) -> BacktestPreviewCommand:
        from datetime import datetime, time, timezone

        return BacktestPreviewCommand(
            strategy_key=self.strategy_key,
            strategy_version=self.strategy_version,
            timeframe=self.timeframe,
            start_date=datetime.combine(self.start_date, time.min, tzinfo=timezone.utc),
            end_date=datetime.combine(self.end_date, time.max, tzinfo=timezone.utc),
            initial_cash=self.initial_cash,
            fee_rate=self.fee_rate,
            portfolio=self.portfolio.model_copy(deep=True),
            research=self.research.model_copy(deep=True),
        )


class BacktestStartRequest(BacktestPreviewRequest):
    preview_id: str
    approved_fingerprint: str

    def to_command(self) -> BacktestStartCommand:
        preview_command = self.to_preview_command()
        return BacktestStartCommand(
            strategy_key=preview_command.strategy_key,
            strategy_version=preview_command.strategy_version,
            timeframe=preview_command.timeframe,
            start_date=preview_command.start_date,
            end_date=preview_command.end_date,
            initial_cash=preview_command.initial_cash,
            fee_rate=preview_command.fee_rate,
            portfolio=preview_command.portfolio,
            research=preview_command.research,
            preview_id=self.preview_id,
            approved_fingerprint=self.approved_fingerprint,
        )


class BacktestStartResponse(BaseModel):
    success: bool
    backtest_id: int
    message: str


class StrategyPreviewMarkerResponse(BaseModel):
    symbol: str
    time: int
    price: float
    kind: Literal["long_entry", "long_exit", "short_entry", "short_exit"]
    side: Literal["long", "short"]
    label: str
    active_regime: str | None = None
    indicators: JsonObject = Field(default_factory=dict)


class StrategyPreviewIndicatorPointResponse(BaseModel):
    time: int
    value: float


class StrategyPreviewIndicatorSeriesResponse(BaseModel):
    symbol: str
    indicator_id: str
    output: str
    label: str
    points: list[StrategyPreviewIndicatorPointResponse] = Field(default_factory=list)


class StrategyPreviewDiagnosticResponse(BaseModel):
    severity: Literal["info", "warning", "critical"]
    title: str
    message: str


class BacktestPreviewResponse(BaseModel):
    preview_id: str
    fingerprint: str
    strategy_key: str
    strategy_name: str
    strategy_version: int
    strategy_template: str
    timeframe: str
    symbols: list[str]
    start_date: str
    end_date: str
    candles: dict[str, list[OhlcvPointResponse]] = Field(default_factory=dict)
    markers: dict[str, list[StrategyPreviewMarkerResponse]] = Field(default_factory=dict)
    indicator_series: dict[str, list[StrategyPreviewIndicatorSeriesResponse]] = Field(default_factory=dict)
    coverage: dict[str, MarketHistoryCoverageResponse] = Field(default_factory=dict)
    diagnostics: list[StrategyPreviewDiagnosticResponse] = Field(default_factory=list)


class PaperStartRequest(BaseModel):
    strategy_key: str = DEFAULT_STRATEGY_KEY
    strategy_version: int | None = None
    timeframe: str = DEFAULT_TIMEFRAME
    initial_cash: float = Field(default=DEFAULT_INITIAL_CASH, gt=0)
    fee_rate: float = Field(default=DEFAULT_FEE_RATE, ge=0, le=100)
    portfolio: BacktestPortfolioConfig = Field(
        default_factory=BacktestPortfolioConfig
    )

    def to_command(self) -> PaperStartCommand:
        return PaperStartCommand(
            strategy_key=self.strategy_key,
            strategy_version=self.strategy_version,
            timeframe=self.timeframe,
            initial_cash=self.initial_cash,
            fee_rate=self.fee_rate,
            portfolio=self.portfolio.model_copy(deep=True),
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
    indicators: JsonObject | None = None
    reasoning: str | None = None


class BacktestTradeResponse(BacktestTradeRecord):
    id: int
    pair: str
    opened_at: str | None
    closed_at: str | None


class BacktestEquityPointResponse(BacktestEquityPointRecord):
    id: int
    timestamp: str | None


class BacktestRunResponse(BaseModel):
    id: int
    symbol: str
    timeframe: str
    start_date: str | None
    end_date: str | None
    status: str
    metadata: BacktestRunMetadataContractResponse | None = None
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
    id: int | None
    version: int
    name: str
    notes: str | None = None
    is_default: bool
    config: StrategyTemplateConfigResponse
    parameter_space: dict[str, list[JsonValue]]
    runtime: "StrategyRunProfileResponse"


class StrategyTemplateCapabilitiesResponse(BaseModel):
    paper: bool = True
    version_editing: bool = True


class StrategyTemplateRuntimeResponse(BaseModel):
    builder_kind: str = "rules"
    capabilities: StrategyTemplateCapabilitiesResponse = Field(
        default_factory=StrategyTemplateCapabilitiesResponse
    )


class StrategyDefinitionResponse(BaseModel):
    key: str
    name: str
    template: str
    category: str
    description: str | None = None
    is_active: bool
    template_runtime: StrategyTemplateRuntimeResponse = Field(
        default_factory=StrategyTemplateRuntimeResponse
    )
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
    template_runtime: StrategyTemplateRuntimeResponse = Field(
        default_factory=StrategyTemplateRuntimeResponse
    )
    indicator_keys: list[str] = Field(default_factory=list)
    indicator_registry: list[StrategyIndicatorRegistryResponse]
    operators: list[StrategyOperatorResponse]
    group_logics: list[StrategyGroupLogicResponse]
    default_config: StrategyTemplateConfigResponse
    default_parameter_space: dict[str, list[JsonValue]]


class BacktestRunDefaultsResponse(BaseModel):
    strategy_key: str = DEFAULT_STRATEGY_KEY
    timeframe: str = DEFAULT_TIMEFRAME
    start_date: str = Field(
        default_factory=lambda: default_backtest_dates()[0].isoformat()
    )
    end_date: str = Field(
        default_factory=lambda: default_backtest_dates()[1].isoformat()
    )
    initial_cash: float = DEFAULT_INITIAL_CASH
    fee_rate: float = DEFAULT_FEE_RATE
    portfolio: BacktestPortfolioConfig = Field(
        default_factory=BacktestPortfolioConfig
    )
    research: BacktestResearchConfig = Field(default_factory=BacktestResearchConfig)
    history_mode: Literal["backtest", "paper"] = DEFAULT_HISTORY_MODE
    optimize_metric_options: list[StrategyOperatorResponse] = Field(
        default_factory=lambda: [
            StrategyOperatorResponse(**item) for item in OPTIMIZE_METRIC_OPTIONS
        ]
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
    parameter_space: dict[str, list[JsonValue]] = Field(default_factory=dict)
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


class StrategyEvolutionRequest(BaseModel):
    version_name: str | None = None
    notes: str | None = None
    make_default: bool = True
    dry_run: bool = False

    def to_command(self, backtest_id: int) -> EvolveStrategyFromBacktestCommand:
        return EvolveStrategyFromBacktestCommand(
            backtest_id=backtest_id,
            version_name=self.version_name,
            notes=self.notes,
            make_default=self.make_default,
            dry_run=self.dry_run,
        )


class StrategyEvolutionDefectResponse(BaseModel):
    key: str
    severity: Literal["info", "warning", "critical"]
    title: str
    evidence: list[str] = Field(default_factory=list)
    recommendation: str


class StrategyEvolutionChangeResponse(BaseModel):
    path: str
    before: JsonValue | None = None
    after: JsonValue | None = None
    reason: str


class StrategyEvolutionResponse(BaseModel):
    source_backtest_id: int
    strategy_key: str
    source_version: int | None = None
    created: bool
    message: str
    defects: list[StrategyEvolutionDefectResponse] = Field(default_factory=list)
    changes: list[StrategyEvolutionChangeResponse] = Field(default_factory=list)
    evolved_version: StrategyVersionResponse | None = None
    base_config: StrategyTemplateConfigResponse
    evolved_config: StrategyTemplateConfigResponse


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
    default_parameter_space: dict[str, list[JsonValue]] = Field(default_factory=dict)

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
