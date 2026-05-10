from __future__ import annotations

from pydantic import BaseModel, Field

from app.contracts.json_types import JsonObject

class BinanceRwaSymbolItemResponse(BaseModel):
    chain_id: str | None = None
    contract_address: str | None = None
    symbol: str | None = None
    ticker: str | None = None
    type: int | None = None
    multiplier: float | None = None


class BinanceRwaSymbolListResponse(BaseModel):
    source: str
    items: list[BinanceRwaSymbolItemResponse] = Field(default_factory=list)


class BinanceRwaMetaResponse(BaseModel):
    source: str
    token_id: str | None = None
    name: str | None = None
    symbol: str | None = None
    ticker: str | None = None
    chain_id: str | None = None
    chain_name: str | None = None
    contract_address: str | None = None
    decimals: int | None = None
    icon_url: str | None = None
    daily_attestation_report_url: str | None = None
    monthly_attestation_report_url: str | None = None
    company_info: JsonObject = Field(default_factory=dict)
    description: str | None = None


class BinanceRwaMarketStatusResponse(BaseModel):
    source: str
    openState: bool | None = None
    reasonCode: str | None = None
    reasonMsg: str | None = None
    nextOpen: str | None = None
    nextClose: str | None = None
    nextOpenTime: int | None = None
    nextCloseTime: int | None = None
    marketStatus: str | None = None


class BinanceRwaDynamicResponse(BaseModel):
    source: str
    symbol: str | None = None
    ticker: str | None = None
    token_info: JsonObject = Field(default_factory=dict)
    stock_info: JsonObject = Field(default_factory=dict)
    status_info: JsonObject = Field(default_factory=dict)
    limit_info: JsonObject = Field(default_factory=dict)


class BinanceRwaKlineItemResponse(BaseModel):
    open_time: int | None = None
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None
    close_time: int | None = None


class BinanceRwaKlineResponse(BaseModel):
    source: str
    chain_id: str
    contract_address: str
    interval: str
    decimals: int | None = None
    items: list[BinanceRwaKlineItemResponse] = Field(default_factory=list)

