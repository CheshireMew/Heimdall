from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class MACDResponse(BaseModel):
    dif: float | None
    dea: float | None
    histogram: float | None


class IndicatorSummaryResponse(BaseModel):
    ema: float | None
    rsi: float | None
    macd: MACDResponse | None
    atr: float | None
    atr_pct: float | None = None
    realized_volatility_pct: float | None = None
    annualized_volatility_pct: float | None = None


class RealtimeResponse(BaseModel):
    symbol: str
    timestamp: str
    current_price: float
    indicators: IndicatorSummaryResponse
    ai_analysis: Any | None
    kline_data: list[list[float]]
    timeframe: str | None = None
    type: str | None = None


class TradeSetupResponseItem(BaseModel):
    side: str
    entry: float
    target: float
    stop: float
    risk_reward: float
    confidence: int
    risk_amount: float
    entry_time: int
    style: str
    strategy: str
    source: str


class TradeSetupResponse(BaseModel):
    symbol: str
    timeframe: str
    timestamp: str
    current_price: float | None
    setup: TradeSetupResponseItem | None
    reason: str
    source: str


class IndicatorHistoryPoint(BaseModel):
    date: str
    value: float


class MarketIndicatorResponse(BaseModel):
    indicator_id: str
    name: str
    category: str
    unit: str | None
    current_value: float | None
    last_updated: str | None
    history: list[IndicatorHistoryPoint]


class ApiStatusResponse(BaseModel):
    status: str
    version: str
    framework: str
    dependencies: str
    timestamp: str


class DisplayCurrencyResponse(BaseModel):
    code: str
    name: str
    symbol: str
    locale: str
    fraction_digits: int


class CurrencyRatesResponse(BaseModel):
    base: str
    rates: dict[str, float]
    supported: list[DisplayCurrencyResponse]
    updated_at: str
    source: str
    is_fallback: bool = False


class MarketIndexResponse(BaseModel):
    symbol: str
    name: str
    market: str
    currency: str
    pricing_symbol: str | None = None
    pricing_name: str | None = None
    pricing_currency: str | None = None


class MarketSymbolSearchResponse(BaseModel):
    symbol: str
    name: str
    asset_class: str
    market: str
    currency: str
    exchange: str | None = None
    aliases: list[str] = Field(default_factory=list)
    pricing_symbol: str | None = None
    pricing_name: str | None = None
    pricing_currency: str | None = None


class MarketIndexHistoryResponse(BaseModel):
    symbol: str
    name: str
    market: str
    currency: str
    native_currency: str | None = None
    timeframe: str
    source: str
    price_basis: str = "index"
    pricing_symbol: str | None = None
    pricing_name: str | None = None
    pricing_currency: str | None = None
    is_close_only: bool = False
    count: int
    data: list[list[float]]


class FundingRateSnapshotResponse(BaseModel):
    exchange: str
    market_type: str
    symbol: str
    funding_rate: float | None
    funding_rate_pct: float | None
    mark_price: float | None = None
    index_price: float | None = None
    interest_rate: float | None = None
    next_funding_time: str | None = None
    collected_at: str


class FundingRateHistoryPointResponse(BaseModel):
    funding_time: str
    funding_rate: float
    funding_rate_pct: float
    mark_price: float | None = None


class FundingRateHistoryResponse(BaseModel):
    exchange: str
    market_type: str
    symbol: str
    count: int
    items: list[FundingRateHistoryPointResponse]


class FundingRateSyncResponse(BaseModel):
    exchange: str
    market_type: str
    symbol: str
    fetched: int
    inserted: int
    total: int
    start_date: str
    end_date: str


class TechnicalMetricsResponse(BaseModel):
    symbol: str
    timeframe: str
    sample_size: int
    current_price: float
    atr: float | None = None
    atr_pct: float | None = None
    realized_volatility_pct: float | None = None
    annualized_volatility_pct: float | None = None


class CryptoIndexConstituentResponse(BaseModel):
    id: str
    symbol: str
    name: str
    image: str | None = None
    rank: int | None = None
    price: float | None = None
    market_cap: float | None = None
    market_cap_change_24h_pct: float | None = None
    price_change_24h_pct: float | None = None
    volume_24h: float | None = None


class CryptoIndexHistoryPointResponse(BaseModel):
    date: str
    timestamp: int
    market_cap: float
    index_value: float


class CryptoIndexSummaryResponse(BaseModel):
    current_basket_market_cap: float
    current_index_value: float
    basket_change_24h_pct: float
    btc_weight_pct: float
    eth_weight_pct: float
    common_start_date: str
    methodology: str


class CryptoIndexResponse(BaseModel):
    top_n: int
    days: int
    base_value: float
    constituents: list[CryptoIndexConstituentResponse]
    history: list[CryptoIndexHistoryPointResponse]
    summary: CryptoIndexSummaryResponse | None = None
    is_partial: bool = False
    resolved_constituents_count: int | None = None
    missing_symbols: list[str] = Field(default_factory=list)
