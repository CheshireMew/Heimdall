from __future__ import annotations

from pydantic import BaseModel, Field

class BinanceSymbolSummaryResponse(BaseModel):
    symbol: str | None = None
    status: str | None = None
    pair: str | None = None
    contract_type: str | None = None
    base_asset: str | None = None
    quote_asset: str | None = None
    price_precision: int | None = None
    quantity_precision: int | None = None
    permissions: list[str] = Field(default_factory=list)


class BinanceExchangeInfoResponse(BaseModel):
    exchange: str
    market: str
    timezone: str | None = None
    server_time: int | None = None
    symbols: list[BinanceSymbolSummaryResponse] = Field(default_factory=list)


class BinanceTickerStatsItemResponse(BaseModel):
    symbol: str | None = None
    price_change: float | None = None
    price_change_pct: float | None = None
    weighted_avg_price: float | None = None
    last_price: float | None = None
    last_qty: float | None = None
    open_price: float | None = None
    high_price: float | None = None
    low_price: float | None = None
    volume: float | None = None
    quote_volume: float | None = None
    open_time: int | None = None
    close_time: int | None = None
    count: int | None = None


class BinanceTickerStatsResponse(BaseModel):
    exchange: str
    market: str
    items: list[BinanceTickerStatsItemResponse] = Field(default_factory=list)


class BinancePriceTickerItemResponse(BaseModel):
    symbol: str | None = None
    price: float | None = None


class BinancePriceTickerResponse(BaseModel):
    exchange: str
    market: str
    items: list[BinancePriceTickerItemResponse] = Field(default_factory=list)


class BinanceBookTickerItemResponse(BaseModel):
    symbol: str | None = None
    bid_price: float | None = None
    bid_qty: float | None = None
    ask_price: float | None = None
    ask_qty: float | None = None


class BinanceBookTickerResponse(BaseModel):
    exchange: str
    market: str
    items: list[BinanceBookTickerItemResponse] = Field(default_factory=list)


class BinanceOrderBookLevelResponse(BaseModel):
    price: float | None = None
    qty: float | None = None


class BinanceOrderBookResponse(BaseModel):
    exchange: str
    market: str
    symbol: str
    last_update_id: int | None = None
    bids: list[BinanceOrderBookLevelResponse] = Field(default_factory=list)
    asks: list[BinanceOrderBookLevelResponse] = Field(default_factory=list)


class BinanceTradeItemResponse(BaseModel):
    id: int | None = None
    price: float | None = None
    qty: float | None = None
    quote_qty: float | None = None
    time: int | None = None
    is_buyer_maker: bool = False


class BinanceTradeListResponse(BaseModel):
    exchange: str
    market: str
    symbol: str
    items: list[BinanceTradeItemResponse] = Field(default_factory=list)


class BinanceKlineItemResponse(BaseModel):
    open_time: int | None = None
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None
    volume: float | None = None
    close_time: int | None = None
    quote_volume: float | None = None
    trade_count: int | None = None


class BinanceKlineResponse(BaseModel):
    exchange: str
    market: str
    symbol: str
    interval: str
    items: list[BinanceKlineItemResponse] = Field(default_factory=list)


