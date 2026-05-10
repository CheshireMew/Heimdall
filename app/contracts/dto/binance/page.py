from __future__ import annotations

from pydantic import BaseModel, Field

from app.contracts.dto.binance.common import BinanceTickerStatsResponse
from app.contracts.dto.binance.usdm import BinanceMarkPriceResponse

class BinanceBreakoutMonitorSummaryResponse(BaseModel):
    monitored_count: int = 0
    natural_count: int = 0
    momentum_count: int = 0
    focus_count: int = 0
    advancing_count: int = 0
    spot_count: int = 0
    contract_count: int = 0


class BinanceBreakoutMonitorItemResponse(BaseModel):
    market: str
    market_label: str
    symbol: str
    last_price: float | None = None
    mark_price: float | None = None
    price_change_pct: float | None = None
    quote_volume: float | None = None
    funding_rate_pct: float | None = None
    change_15m_pct: float | None = None
    change_1h_pct: float | None = None
    change_4h_pct: float | None = None
    pullback_from_high_pct: float | None = None
    range_position_pct: float | None = None
    ema20_gap_15m_pct: float | None = None
    ema20_gap_1h_pct: float | None = None
    rsi_15m: float | None = None
    rsi_1h: float | None = None
    macd_hist_15m: float | None = None
    green_ratio_15m_pct: float | None = None
    natural_score: int = 0
    momentum_score: int = 0
    structure_ok: bool = False
    momentum_ok: bool = False
    follow_status: str = "只做观察"
    verdict: str = "只做观察"
    reasons: list[str] = Field(default_factory=list)


class BinanceBreakoutMonitorResponse(BaseModel):
    exchange: str
    min_rise_pct: float
    quote_asset: str
    updated_at: int
    summary: BinanceBreakoutMonitorSummaryResponse = Field(default_factory=BinanceBreakoutMonitorSummaryResponse)
    items: list[BinanceBreakoutMonitorItemResponse] = Field(default_factory=list)


class BinanceContractBoardItemResponse(BaseModel):
    market: str = "usdm"
    market_label: str = "U 鏈綅"
    symbol: str | None = None
    price_change_pct: float | None = None
    last_price: float | None = None
    quote_volume: float | None = None
    mark_price: float | None = None
    index_price: float | None = None
    funding_rate_pct: float | None = None
    open_interest: float | None = None
    open_interest_value: float | None = None
    oi_change_1h_pct: float | None = None
    oi_change_4h_pct: float | None = None
    oi_change_24h_pct: float | None = None


class BinanceContractBoardResponse(BaseModel):
    exchange: str
    market: str
    items: list[BinanceContractBoardItemResponse] = Field(default_factory=list)


class BinanceMarketPageRefreshStatusResponse(BaseModel):
    snapshot_ready: bool = False
    boards_ready: bool = False
    monitor_ready: bool = False
    refreshing: bool = False
    oi_ready_count: int = 0
    oi_requested_count: int = 0
    last_refresh_started_at: int | None = None
    last_refresh_completed_at: int | None = None
    last_refresh_error: str | None = None


class BinanceMarketPageResponse(BaseModel):
    exchange: str
    quote_asset: str
    updated_at: int
    monitor: BinanceBreakoutMonitorResponse
    spot_boards: dict[str, BinanceTickerStatsResponse] = Field(default_factory=dict)
    contract_boards: dict[str, BinanceContractBoardResponse] = Field(default_factory=dict)
    load_errors: list[str] = Field(default_factory=list)
    refresh_status: BinanceMarketPageRefreshStatusResponse = Field(default_factory=BinanceMarketPageRefreshStatusResponse)


class BinanceMarketSourceSnapshotResponse(BaseModel):
    spot_ticker: BinanceTickerStatsResponse
    usdm_ticker: BinanceTickerStatsResponse
    usdm_mark: BinanceMarkPriceResponse
    load_errors: list[str] = Field(default_factory=list)
    updated_at: int = 0


