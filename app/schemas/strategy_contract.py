from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class StrategyIndicatorOutputResponse(BaseModel):
    key: str
    label: str


class StrategyIndicatorParamResponse(BaseModel):
    key: str
    label: str
    type: Literal["int", "float", "bool"]
    default: float | bool
    min: float | None = None
    max: float | None = None
    step: float | None = None


class StrategyRuleSourceResponse(BaseModel):
    kind: str
    field: str | None = None
    indicator: str | None = None
    output: str | None = None
    bars_ago: int | None = None
    value: float | None = None
    multiplier: float | None = None
    base_indicator: str | None = None
    base_output: str | None = None
    offset_indicator: str | None = None
    offset_output: str | None = None
    offset_multiplier: float | None = None


class StrategyConditionNodeResponse(BaseModel):
    id: str
    node_type: Literal["condition"] = "condition"
    label: str
    left: StrategyRuleSourceResponse
    operator: Literal["gt", "gte", "lt", "lte"]
    right: StrategyRuleSourceResponse
    enabled: bool = True


class StrategyGroupNodeResponse(BaseModel):
    id: str
    node_type: Literal["group"] = "group"
    label: str
    logic: Literal["and", "or"]
    enabled: bool = True
    children: list["StrategyConditionNodeResponse | StrategyGroupNodeResponse"] = Field(
        default_factory=list
    )


class StrategyIndicatorConfigResponse(BaseModel):
    label: str
    type: str
    timeframe: str = "base"
    params: dict[str, float | bool] = Field(default_factory=dict)


class StrategyExecutionConfigResponse(BaseModel):
    market_type: Literal["spot", "futures"] = "spot"
    direction: Literal["long_only", "long_short"] = "long_only"


class StrategyStateBranchResponse(BaseModel):
    id: str
    label: str
    enabled: bool = True
    regime: StrategyGroupNodeResponse
    long_entry: StrategyGroupNodeResponse
    long_exit: StrategyGroupNodeResponse
    short_entry: StrategyGroupNodeResponse
    short_exit: StrategyGroupNodeResponse


class StrategyRoiTargetResponse(BaseModel):
    id: str
    minutes: int
    profit: float
    enabled: bool = True


class StrategyPartialExitResponse(BaseModel):
    id: str
    profit: float
    size_pct: float
    enabled: bool = True


class StrategyTrailingConfigResponse(BaseModel):
    enabled: bool = False
    positive: float
    offset: float
    only_offset_reached: bool = True


class StrategyTradePlanConfigResponse(BaseModel):
    enabled: bool = False
    stop_multiplier: float = 1.0
    min_stop_pct: float = 0.01
    reward_multiplier: float = 2.0
    atr_indicator: str = ""
    support_indicator: str = ""
    resistance_indicator: str = ""


class StrategyRiskConfigResponse(BaseModel):
    stoploss: float
    roi_targets: list[StrategyRoiTargetResponse] = Field(default_factory=list)
    trailing: StrategyTrailingConfigResponse
    partial_exits: list[StrategyPartialExitResponse] = Field(default_factory=list)
    trade_plan: StrategyTradePlanConfigResponse = Field(
        default_factory=StrategyTradePlanConfigResponse
    )


class StrategyTemplateConfigResponse(BaseModel):
    indicators: dict[str, StrategyIndicatorConfigResponse] = Field(default_factory=dict)
    execution: StrategyExecutionConfigResponse
    regime_priority: list[Literal["trend", "range"]] = Field(
        default_factory=lambda: ["trend", "range"]
    )
    trend: StrategyStateBranchResponse
    range: StrategyStateBranchResponse
    risk: StrategyRiskConfigResponse


StrategyGroupNodeResponse.model_rebuild()
