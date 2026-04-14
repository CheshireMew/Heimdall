from __future__ import annotations

from typing import Any

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


class BinanceMarkPriceItemResponse(BaseModel):
    symbol: str | None = None
    pair: str | None = None
    mark_price: float | None = None
    index_price: float | None = None
    estimated_settle_price: float | None = None
    last_funding_rate: float | None = None
    next_funding_time: int | None = None
    interest_rate: float | None = None
    time: int | None = None


class BinanceMarkPriceResponse(BaseModel):
    exchange: str
    market: str
    items: list[BinanceMarkPriceItemResponse] = Field(default_factory=list)


class BinanceFundingInfoItemResponse(BaseModel):
    symbol: str | None = None
    adjusted_funding_rate_cap: float | None = None
    adjusted_funding_rate_floor: float | None = None
    funding_interval_hours: int | None = None
    disclaimer: bool = False


class BinanceFundingInfoResponse(BaseModel):
    exchange: str
    market: str
    items: list[BinanceFundingInfoItemResponse] = Field(default_factory=list)


class BinanceFundingHistoryItemResponse(BaseModel):
    symbol: str | None = None
    funding_rate: float | None = None
    mark_price: float | None = None
    funding_time: int | None = None


class BinanceFundingHistoryListResponse(BaseModel):
    exchange: str
    market: str
    items: list[BinanceFundingHistoryItemResponse] = Field(default_factory=list)


class BinanceOpenInterestSnapshotResponse(BaseModel):
    exchange: str
    market: str
    symbol: str | None = None
    pair: str | None = None
    open_interest: float | None = None
    contract_type: str | None = None
    time: int | None = None


class BinanceOpenInterestStatItemResponse(BaseModel):
    symbol: str | None = None
    pair: str | None = None
    contract_type: str | None = None
    sum_open_interest: float | None = None
    sum_open_interest_value: float | None = None
    timestamp: int | None = None


class BinanceOpenInterestStatsResponse(BaseModel):
    exchange: str
    market: str
    items: list[BinanceOpenInterestStatItemResponse] = Field(default_factory=list)


class BinanceRatioItemResponse(BaseModel):
    symbol: str | None = None
    pair: str | None = None
    long_short_ratio: float | None = None
    long_account: float | None = None
    short_account: float | None = None
    long_position: float | None = None
    short_position: float | None = None
    timestamp: int | None = None


class BinanceRatioSeriesResponse(BaseModel):
    exchange: str
    market: str
    items: list[BinanceRatioItemResponse] = Field(default_factory=list)


class BinanceTakerVolumeItemResponse(BaseModel):
    symbol: str | None = None
    pair: str | None = None
    buy_sell_ratio: float | None = None
    buy_vol: float | None = None
    sell_vol: float | None = None
    buy_vol_value: float | None = None
    sell_vol_value: float | None = None
    timestamp: int | None = None


class BinanceTakerVolumeResponse(BaseModel):
    exchange: str
    market: str
    items: list[BinanceTakerVolumeItemResponse] = Field(default_factory=list)


class BinanceBasisItemResponse(BaseModel):
    symbol: str | None = None
    pair: str | None = None
    contract_type: str | None = None
    basis: float | None = None
    basis_rate: float | None = None
    annualized_basis_rate: float | None = None
    futures_price: float | None = None
    index_price: float | None = None
    timestamp: int | None = None


class BinanceBasisResponse(BaseModel):
    exchange: str
    market: str
    items: list[BinanceBasisItemResponse] = Field(default_factory=list)


class BinanceWeb3RankItemResponse(BaseModel):
    symbol: str | None = None
    chain_id: str | None = None
    contract_address: str | None = None
    icon_url: str | None = None
    price: float | None = None
    market_cap: float | None = None
    liquidity: float | None = None
    holders: int | None = None
    launch_time: int | None = None
    percent_change_1h: float | None = None
    percent_change_24h: float | None = None
    volume_24h: float | None = None
    unique_trader_24h: int | None = None
    kyc_holders: int | None = None


class BinanceWeb3UnifiedTokenRankResponse(BaseModel):
    source: str
    leaderboard: str
    rank_type: int
    page: int
    size: int
    total: int | None = None
    items: list[BinanceWeb3RankItemResponse] = Field(default_factory=list)


class BinanceWeb3SocialHypeItemResponse(BaseModel):
    symbol: str | None = None
    chain_id: str | None = None
    contract_address: str | None = None
    logo_url: str | None = None
    market_cap: float | None = None
    price_change_pct: float | None = None
    social_hype: float | None = None
    sentiment: str | None = None
    summary: str | None = None


class BinanceWeb3SocialHypeResponse(BaseModel):
    source: str
    leaderboard: str
    items: list[BinanceWeb3SocialHypeItemResponse] = Field(default_factory=list)


class BinanceWeb3SmartMoneyInflowItemResponse(BaseModel):
    symbol: str | None = None
    chain_id: str | None = None
    contract_address: str | None = None
    logo_url: str | None = None
    price: float | None = None
    market_cap: float | None = None
    liquidity: float | None = None
    volume: float | None = None
    price_change_pct: float | None = None
    holders: int | None = None
    traders: int | None = None
    inflow: float | None = None
    risk_level: int | None = None


class BinanceWeb3SmartMoneyInflowResponse(BaseModel):
    source: str
    leaderboard: str
    items: list[BinanceWeb3SmartMoneyInflowItemResponse] = Field(default_factory=list)


class BinanceWeb3MemeRankItemResponse(BaseModel):
    symbol: str | None = None
    chain_id: str | None = None
    contract_address: str | None = None
    rank: int | None = None
    score: float | None = None
    logo_url: str | None = None
    price: float | None = None
    price_change_pct: float | None = None
    market_cap: float | None = None
    liquidity: float | None = None
    volume: float | None = None
    holders: int | None = None
    unique_trader_bn: int | None = None


class BinanceWeb3MemeRankResponse(BaseModel):
    source: str
    leaderboard: str
    items: list[BinanceWeb3MemeRankItemResponse] = Field(default_factory=list)


class BinanceWeb3AddressPnlItemResponse(BaseModel):
    address: str | None = None
    address_label: str | None = None
    address_logo: str | None = None
    tags: list[str] = Field(default_factory=list)
    realized_pnl: float | None = None
    realized_pnl_pct: float | None = None
    win_rate: float | None = None
    total_volume: float | None = None
    total_tx_cnt: int | None = None
    total_traded_tokens: int | None = None
    last_activity: int | None = None


class BinanceWeb3AddressPnlResponse(BaseModel):
    source: str
    leaderboard: str
    page: int
    size: int
    pages: int | None = None
    items: list[BinanceWeb3AddressPnlItemResponse] = Field(default_factory=list)


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
    company_info: dict[str, Any] = Field(default_factory=dict)
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
    token_info: dict[str, Any] = Field(default_factory=dict)
    stock_info: dict[str, Any] = Field(default_factory=dict)
    status_info: dict[str, Any] = Field(default_factory=dict)
    limit_info: dict[str, Any] = Field(default_factory=dict)


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


class BinanceReservedFeatureResponse(BaseModel):
    source: str
    feature: str
    status: str
    message: str
    skill_name: str | None = None
    skill_version: str | None = None
    supported_chains: list[dict[str, str]] = Field(default_factory=list)
    reserved_endpoints: list[dict[str, Any]] = Field(default_factory=list)
    response_fields: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
