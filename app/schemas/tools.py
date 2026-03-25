from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DCARequestSchema(BaseModel):
    symbol: str = 'BTC/USDT'
    amount: float = Field(100.0, gt=0, le=1_000_000)
    start_date: str | None = None
    investment_time: str = '23:00'
    timezone: str = 'Asia/Shanghai'
    days: int | None = Field(None, gt=0, le=3650)
    strategy: str = 'standard'
    strategy_params: dict[str, Any] | None = {}


class PairCompareRequestSchema(BaseModel):
    symbol_a: str = 'BTC'
    symbol_b: str = 'ETH'
    days: int = Field(7, gt=0, le=3650)
    timeframe: str = '1h'


class DynamicToolResponse(BaseModel):
    model_config = ConfigDict(extra='allow')
