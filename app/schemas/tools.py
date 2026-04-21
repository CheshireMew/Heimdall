from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.json_types import JsonObject


DcaStrategyKey = Literal[
    "standard",
    "ema_deviation",
    "rsi_dynamic",
    "ahr999",
    "fear_greed",
    "value_averaging",
]


class DCARequestSchema(BaseModel):
    symbol: str = 'BTC/USDT'
    amount: float = Field(100.0, gt=0, le=1_000_000)
    start_date: str | None = None
    investment_time: str = '23:00'
    timezone: str = 'Asia/Shanghai'
    days: int | None = Field(None, gt=0, le=3650)
    strategy: DcaStrategyKey = 'standard'
    strategy_params: JsonObject | None = Field(default_factory=dict)


class PairCompareRequestSchema(BaseModel):
    symbol_a: str = 'BTC'
    symbol_b: str = 'ETH'
    days: int = Field(7, gt=0, le=3650)
    timeframe: str = '1h'


class DCAHistoryPointResponse(BaseModel):
    date: str
    price: float
    invested: float
    value: float
    coins: float
    roi: float
    avg_cost: float


class DCAResponse(BaseModel):
    symbol: str
    asset_class: str | None = None
    price_basis: str | None = None
    pricing_symbol: str | None = None
    pricing_name: str | None = None
    pricing_currency: str | None = None
    start_date: str
    end_date: str
    target_time: str
    total_days: int
    total_invested: float
    final_value: float
    total_coins: float
    roi: float
    average_cost: float
    profit_loss: float
    current_price: float
    history: list[DCAHistoryPointResponse]
    profit_pct: float | None = None


class ToolCandlestickPointResponse(BaseModel):
    time: int
    open: float
    high: float
    low: float
    close: float


class PairCompareToolResponse(BaseModel):
    symbol_a: str
    symbol_b: str
    data_a: list[ToolCandlestickPointResponse]
    data_b: list[ToolCandlestickPointResponse]
    ratio_ohlc: list[ToolCandlestickPointResponse]
    ratio_symbol: str
    timeframe: str | None = None
    relative_strength: float | None = None


class ToolsPageContractResponse(BaseModel):
    dca_defaults: DCARequestSchema
    dca_strategies: list[DcaStrategyKey]
    dca_multiplier_default: float
    compare_defaults: PairCompareRequestSchema
