from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.contracts.json_types import JsonObject


DCA_STRATEGY_KEYS = (
    "standard",
    "ema_deviation",
    "rsi_dynamic",
    "ahr999",
    "fear_greed",
    "value_averaging",
)


DcaStrategyKey = Literal[
    "standard",
    "ema_deviation",
    "rsi_dynamic",
    "ahr999",
    "fear_greed",
    "value_averaging",
]


class SimulateDcaCommand(BaseModel):
    symbol: str = "BTC/USDT"
    amount: float = Field(100.0, gt=0, le=1_000_000)
    start_date: str | None = None
    investment_time: str = "23:00"
    timezone: str = "Asia/Shanghai"
    days: int | None = Field(None, gt=0, le=3650)
    strategy: DcaStrategyKey = "standard"
    strategy_params: JsonObject = Field(default_factory=dict)


class ComparePairsCommand(BaseModel):
    symbol_a: str = "BTC"
    symbol_b: str = "ETH"
    days: int = Field(7, gt=0, le=3650)
    timeframe: str = "1h"
