// This file is generated from backend FastAPI route contracts.
// Do not edit manually.

export interface MarketSymbolSearchResponse {
  symbol: string
  name: string
  asset_class: string
  market: string
  currency: string
  exchange?: string | null
  aliases?: Array<string>
  pricing_symbol?: string | null
  pricing_name?: string | null
  pricing_currency?: string | null
}

export interface ApiStatusResponse {
  status: string
  version: string
  framework: string
  dependencies: string
  timestamp: string
}

export interface RealtimeResponse {
  symbol: string
  timestamp: string
  current_price: number
  indicators: IndicatorSummaryResponse
  ai_analysis: string | number | boolean | Array<string | number | boolean | null> | { [key: string]: string | number | boolean | null } | Array<{ [key: string]: string | number | boolean | null }> | { [key: string]: Array<string | number | boolean | null> } | null
  kline_data?: Array<OhlcvPointResponse>
  timeframe?: string | null
  type?: string | null
}

export interface MarketHistoryResponse {
  symbol: string
  timeframe: string
  items?: Array<OhlcvPointResponse>
}

export interface KlineTailResponse {
  symbol: string
  timeframe: string
  timestamp: string
  current_price: number | null
  kline_data?: Array<OhlcvPointResponse>
}

export interface CurrentPriceResponse {
  symbol: string
  timeframe: string
  timestamp: string
  current_price: number | null
}

export interface CurrentPriceBatchResponse {
  timeframe: string
  items?: Array<CurrentPriceBatchItemResponse>
}

export interface MarketHistoryBatchResponse {
  timeframe: string
  items?: Array<MarketHistoryBatchItemResponse>
}

export interface MarketIndexResponse {
  symbol: string
  name: string
  market: string
  currency: string
  pricing_symbol?: string | null
  pricing_name?: string | null
  pricing_currency?: string | null
}

export interface MarketIndexHistoryResponse {
  symbol: string
  name: string
  market: string
  currency: string
  native_currency?: string | null
  timeframe: string
  source: string
  price_basis?: string
  pricing_symbol?: string | null
  pricing_name?: string | null
  pricing_currency?: string | null
  is_close_only?: boolean
  count: number
  data?: Array<OhlcvPointResponse>
}

export interface FundingRateSnapshotResponse {
  exchange: string
  market_type: string
  symbol: string
  funding_rate: number | null
  funding_rate_pct: number | null
  mark_price?: number | null
  index_price?: number | null
  interest_rate?: number | null
  next_funding_time?: string | null
  collected_at: string
}

export interface FundingRateSyncResponse {
  exchange: string
  market_type: string
  symbol: string
  fetched: number
  inserted: number
  total: number
  start_date: string
  end_date: string
}

export interface FundingRateHistoryResponse {
  exchange: string
  market_type: string
  symbol: string
  count: number
  items: Array<FundingRateHistoryPointResponse>
}

export interface MarketIndicatorResponse {
  indicator_id: string
  name: string
  category: string
  unit: string | null
  current_value: number | null
  last_updated: string | null
  history: Array<IndicatorHistoryPoint>
}

export interface TechnicalMetricsResponse {
  symbol: string
  timeframe: string
  sample_size: number
  current_price: number
  atr?: number | null
  atr_pct?: number | null
  realized_volatility_pct?: number | null
  annualized_volatility_pct?: number | null
}

export interface TradeSetupResponse {
  symbol: string
  timeframe: string
  timestamp: string
  current_price: number | null
  setup: TradeSetupResponseItem | null
  reason: string
  source: string
}

export interface CryptoIndexResponse {
  top_n: number
  days: number
  base_value: number
  constituents: Array<CryptoIndexConstituentResponse>
  history: Array<CryptoIndexHistoryPointResponse>
  summary?: CryptoIndexSummaryResponse | null
  is_partial?: boolean
  resolved_constituents_count?: number | null
  missing_symbols?: Array<string>
}

export interface BinanceMarketPageResponse {
  exchange: string
  quote_asset: string
  updated_at: number
  monitor: BinanceBreakoutMonitorResponse
  spot_ticker: BinanceTickerStatsResponse
  usdm_ticker: BinanceTickerStatsResponse
  usdm_mark: BinanceMarkPriceResponse
  load_errors?: Array<string>
}

export interface BinanceBreakoutMonitorResponse {
  exchange: string
  min_rise_pct: number
  quote_asset: string
  updated_at: number
  summary?: BinanceBreakoutMonitorSummaryResponse
  items?: Array<BinanceBreakoutMonitorItemResponse>
}

export interface BinanceExchangeInfoResponse {
  exchange: string
  market: string
  timezone?: string | null
  server_time?: number | null
  symbols?: Array<BinanceSymbolSummaryResponse>
}

export interface BinanceTickerStatsResponse {
  exchange: string
  market: string
  items?: Array<BinanceTickerStatsItemResponse>
}

export interface BinancePriceTickerResponse {
  exchange: string
  market: string
  items?: Array<BinancePriceTickerItemResponse>
}

export interface BinanceBookTickerResponse {
  exchange: string
  market: string
  items?: Array<BinanceBookTickerItemResponse>
}

export interface BinanceOrderBookResponse {
  exchange: string
  market: string
  symbol: string
  last_update_id?: number | null
  bids?: Array<BinanceOrderBookLevelResponse>
  asks?: Array<BinanceOrderBookLevelResponse>
}

export interface BinanceTradeListResponse {
  exchange: string
  market: string
  symbol: string
  items?: Array<BinanceTradeItemResponse>
}

export interface BinanceKlineResponse {
  exchange: string
  market: string
  symbol: string
  interval: string
  items?: Array<BinanceKlineItemResponse>
}

export interface BinanceMarkPriceResponse {
  exchange: string
  market: string
  items?: Array<BinanceMarkPriceItemResponse>
}

export interface BinanceFundingInfoResponse {
  exchange: string
  market: string
  items?: Array<BinanceFundingInfoItemResponse>
}

export interface BinanceFundingHistoryListResponse {
  exchange: string
  market: string
  items?: Array<BinanceFundingHistoryItemResponse>
}

export interface BinanceOpenInterestSnapshotResponse {
  exchange: string
  market: string
  symbol?: string | null
  pair?: string | null
  open_interest?: number | null
  contract_type?: string | null
  time?: number | null
}

export interface BinanceOpenInterestStatsResponse {
  exchange: string
  market: string
  items?: Array<BinanceOpenInterestStatItemResponse>
}

export interface BinanceRatioSeriesResponse {
  exchange: string
  market: string
  items?: Array<BinanceRatioItemResponse>
}

export interface BinanceTakerVolumeResponse {
  exchange: string
  market: string
  items?: Array<BinanceTakerVolumeItemResponse>
}

export interface BinanceBasisResponse {
  exchange: string
  market: string
  items?: Array<BinanceBasisItemResponse>
}

export interface BinanceWeb3SocialHypeResponse {
  source: string
  leaderboard: string
  items?: Array<BinanceWeb3SocialHypeItemResponse>
}

export interface BinanceWeb3UnifiedTokenRankResponse {
  source: string
  leaderboard: string
  rank_type: number
  page: number
  size: number
  total?: number | null
  items?: Array<BinanceWeb3RankItemResponse>
}

export interface BinanceWeb3SmartMoneyInflowResponse {
  source: string
  leaderboard: string
  items?: Array<BinanceWeb3SmartMoneyInflowItemResponse>
}

export interface BinanceWeb3MemeRankResponse {
  source: string
  leaderboard: string
  items?: Array<BinanceWeb3MemeRankItemResponse>
}

export interface BinanceWeb3AddressPnlResponse {
  source: string
  leaderboard: string
  page: number
  size: number
  pages?: number | null
  items?: Array<BinanceWeb3AddressPnlItemResponse>
}

export interface BinanceWeb3HeatRankResponse {
  source: string
  leaderboard: string
  chain_id: string
  size: number
  items?: Array<BinanceWeb3HeatRankItemResponse>
  formula?: { [key: string]: Array<string> }
}

export interface BinanceRwaSymbolListResponse {
  source: string
  items?: Array<BinanceRwaSymbolItemResponse>
}

export interface BinanceRwaMetaResponse {
  source: string
  token_id?: string | null
  name?: string | null
  symbol?: string | null
  ticker?: string | null
  chain_id?: string | null
  chain_name?: string | null
  contract_address?: string | null
  decimals?: number | null
  icon_url?: string | null
  daily_attestation_report_url?: string | null
  monthly_attestation_report_url?: string | null
  company_info?: { [key: string]: string | number | boolean | Array<string | number | boolean | null> | { [key: string]: string | number | boolean | null } | Array<{ [key: string]: string | number | boolean | null }> | { [key: string]: Array<string | number | boolean | null> } | null }
  description?: string | null
}

export interface BinanceRwaMarketStatusResponse {
  source: string
  openState?: boolean | null
  reasonCode?: string | null
  reasonMsg?: string | null
  nextOpen?: string | null
  nextClose?: string | null
  nextOpenTime?: number | null
  nextCloseTime?: number | null
  marketStatus?: string | null
}

export interface BinanceRwaDynamicResponse {
  source: string
  symbol?: string | null
  ticker?: string | null
  token_info?: { [key: string]: string | number | boolean | Array<string | number | boolean | null> | { [key: string]: string | number | boolean | null } | Array<{ [key: string]: string | number | boolean | null }> | { [key: string]: Array<string | number | boolean | null> } | null }
  stock_info?: { [key: string]: string | number | boolean | Array<string | number | boolean | null> | { [key: string]: string | number | boolean | null } | Array<{ [key: string]: string | number | boolean | null }> | { [key: string]: Array<string | number | boolean | null> } | null }
  status_info?: { [key: string]: string | number | boolean | Array<string | number | boolean | null> | { [key: string]: string | number | boolean | null } | Array<{ [key: string]: string | number | boolean | null }> | { [key: string]: Array<string | number | boolean | null> } | null }
  limit_info?: { [key: string]: string | number | boolean | Array<string | number | boolean | null> | { [key: string]: string | number | boolean | null } | Array<{ [key: string]: string | number | boolean | null }> | { [key: string]: Array<string | number | boolean | null> } | null }
}

export interface BinanceRwaKlineResponse {
  source: string
  chain_id: string
  contract_address: string
  interval: string
  decimals?: number | null
  items?: Array<BinanceRwaKlineItemResponse>
}

export interface BinanceWeb3TokenDynamicResponse {
  source: string
  chain_id: string
  contract_address: string
  price?: number | null
  native_token_price?: number | null
  volume_24h?: number | null
  volume_24h_buy?: number | null
  volume_24h_sell?: number | null
  volume_4h?: number | null
  volume_1h?: number | null
  volume_5m?: number | null
  count_24h?: number | null
  count_24h_buy?: number | null
  count_24h_sell?: number | null
  percent_change_5m?: number | null
  percent_change_1h?: number | null
  percent_change_4h?: number | null
  percent_change_24h?: number | null
  market_cap?: number | null
  fdv?: number | null
  total_supply?: number | null
  circulating_supply?: number | null
  price_high_24h?: number | null
  price_low_24h?: number | null
  holders?: number | null
  liquidity?: number | null
  launch_time?: number | null
  top10_holders_percentage?: number | null
  kyc_holder_count?: number | null
  kol_holders?: number | null
  kol_holding_percent?: number | null
  pro_holders?: number | null
  pro_holding_percent?: number | null
  smart_money_holders?: number | null
  smart_money_holding_percent?: number | null
}

export interface BinanceWeb3TokenKlineResponse {
  source: string
  address: string
  platform: string
  interval: string
  items?: Array<BinanceWeb3TokenKlineItemResponse>
}

export interface BinanceWeb3TokenAuditResponse {
  source: string
  binance_chain_id: string
  contract_address: string
  has_result?: boolean
  is_supported?: boolean
  risk_level_enum?: string | null
  risk_level?: number | null
  buy_tax?: number | null
  sell_tax?: number | null
  is_verified?: boolean | null
  risk_items?: Array<{ [key: string]: string | number | boolean | Array<string | number | boolean | null> | { [key: string]: string | number | boolean | null } | Array<{ [key: string]: string | number | boolean | null }> | { [key: string]: Array<string | number | boolean | null> } | null }>
}

export interface BinanceBasisItemResponse {
  symbol?: string | null
  pair?: string | null
  contract_type?: string | null
  basis?: number | null
  basis_rate?: number | null
  annualized_basis_rate?: number | null
  futures_price?: number | null
  index_price?: number | null
  timestamp?: number | null
}

export interface BinanceBookTickerItemResponse {
  symbol?: string | null
  bid_price?: number | null
  bid_qty?: number | null
  ask_price?: number | null
  ask_qty?: number | null
}

export interface BinanceBreakoutMonitorItemResponse {
  market: string
  market_label: string
  symbol: string
  last_price?: number | null
  mark_price?: number | null
  price_change_pct?: number | null
  quote_volume?: number | null
  funding_rate_pct?: number | null
  change_15m_pct?: number | null
  change_1h_pct?: number | null
  change_4h_pct?: number | null
  pullback_from_high_pct?: number | null
  range_position_pct?: number | null
  ema20_gap_15m_pct?: number | null
  ema20_gap_1h_pct?: number | null
  rsi_15m?: number | null
  rsi_1h?: number | null
  macd_hist_15m?: number | null
  green_ratio_15m_pct?: number | null
  natural_score?: number
  momentum_score?: number
  structure_ok?: boolean
  momentum_ok?: boolean
  follow_status?: string
  verdict?: string
  reasons?: Array<string>
}

export interface BinanceBreakoutMonitorSummaryResponse {
  monitored_count?: number
  natural_count?: number
  momentum_count?: number
  focus_count?: number
  advancing_count?: number
  spot_count?: number
  contract_count?: number
}

export interface BinanceFundingHistoryItemResponse {
  symbol?: string | null
  funding_rate?: number | null
  mark_price?: number | null
  funding_time?: number | null
}

export interface BinanceFundingInfoItemResponse {
  symbol?: string | null
  adjusted_funding_rate_cap?: number | null
  adjusted_funding_rate_floor?: number | null
  funding_interval_hours?: number | null
  disclaimer?: boolean
}

export interface BinanceKlineItemResponse {
  open_time?: number | null
  open?: number | null
  high?: number | null
  low?: number | null
  close?: number | null
  volume?: number | null
  close_time?: number | null
  quote_volume?: number | null
  trade_count?: number | null
}

export interface BinanceMarkPriceItemResponse {
  symbol?: string | null
  pair?: string | null
  mark_price?: number | null
  index_price?: number | null
  estimated_settle_price?: number | null
  last_funding_rate?: number | null
  next_funding_time?: number | null
  interest_rate?: number | null
  time?: number | null
}

export interface BinanceOpenInterestStatItemResponse {
  symbol?: string | null
  pair?: string | null
  contract_type?: string | null
  sum_open_interest?: number | null
  sum_open_interest_value?: number | null
  timestamp?: number | null
}

export interface BinanceOrderBookLevelResponse {
  price?: number | null
  qty?: number | null
}

export interface BinancePriceTickerItemResponse {
  symbol?: string | null
  price?: number | null
}

export interface BinanceRatioItemResponse {
  symbol?: string | null
  pair?: string | null
  long_short_ratio?: number | null
  long_account?: number | null
  short_account?: number | null
  long_position?: number | null
  short_position?: number | null
  timestamp?: number | null
}

export interface BinanceRwaKlineItemResponse {
  open_time?: number | null
  open?: number | null
  high?: number | null
  low?: number | null
  close?: number | null
  close_time?: number | null
}

export interface BinanceRwaSymbolItemResponse {
  chain_id?: string | null
  contract_address?: string | null
  symbol?: string | null
  ticker?: string | null
  type?: number | null
  multiplier?: number | null
}

export interface BinanceSymbolSummaryResponse {
  symbol?: string | null
  status?: string | null
  pair?: string | null
  contract_type?: string | null
  base_asset?: string | null
  quote_asset?: string | null
  price_precision?: number | null
  quantity_precision?: number | null
  permissions?: Array<string>
}

export interface BinanceTakerVolumeItemResponse {
  symbol?: string | null
  pair?: string | null
  buy_sell_ratio?: number | null
  buy_vol?: number | null
  sell_vol?: number | null
  buy_vol_value?: number | null
  sell_vol_value?: number | null
  timestamp?: number | null
}

export interface BinanceTickerStatsItemResponse {
  symbol?: string | null
  price_change?: number | null
  price_change_pct?: number | null
  weighted_avg_price?: number | null
  last_price?: number | null
  last_qty?: number | null
  open_price?: number | null
  high_price?: number | null
  low_price?: number | null
  volume?: number | null
  quote_volume?: number | null
  open_time?: number | null
  close_time?: number | null
  count?: number | null
}

export interface BinanceTradeItemResponse {
  id?: number | null
  price?: number | null
  qty?: number | null
  quote_qty?: number | null
  time?: number | null
  is_buyer_maker?: boolean
}

export interface BinanceWeb3AddressPnlItemResponse {
  address?: string | null
  address_label?: string | null
  address_logo?: string | null
  tags?: Array<string>
  realized_pnl?: number | null
  realized_pnl_pct?: number | null
  win_rate?: number | null
  total_volume?: number | null
  total_tx_cnt?: number | null
  total_traded_tokens?: number | null
  last_activity?: number | null
}

export interface BinanceWeb3HeatRankItemResponse {
  rank?: number | null
  symbol?: string | null
  chain_id?: string | null
  contract_address?: string | null
  icon_url?: string | null
  platform?: string | null
  heat_score?: number
  ranks?: { [key: string]: number }
  components?: { [key: string]: number }
  penalties?: { [key: string]: number }
  metrics?: { [key: string]: string | number | boolean | Array<string | number | boolean | null> | { [key: string]: string | number | boolean | null } | Array<{ [key: string]: string | number | boolean | null }> | { [key: string]: Array<string | number | boolean | null> } | null }
  audit_info?: { [key: string]: string | number | boolean | Array<string | number | boolean | null> | { [key: string]: string | number | boolean | null } | Array<{ [key: string]: string | number | boolean | null }> | { [key: string]: Array<string | number | boolean | null> } | null }
  sentiment?: string | null
  summary?: string | null
}

export interface BinanceWeb3MemeRankItemResponse {
  symbol?: string | null
  chain_id?: string | null
  contract_address?: string | null
  rank?: number | null
  score?: number | null
  logo_url?: string | null
  price?: number | null
  price_change_pct?: number | null
  market_cap?: number | null
  liquidity?: number | null
  volume?: number | null
  holders?: number | null
  unique_trader_bn?: number | null
}

export interface BinanceWeb3RankItemResponse {
  symbol?: string | null
  chain_id?: string | null
  contract_address?: string | null
  icon_url?: string | null
  price?: number | null
  market_cap?: number | null
  liquidity?: number | null
  holders?: number | null
  launch_time?: number | null
  percent_change_1h?: number | null
  percent_change_24h?: number | null
  volume_1h?: number | null
  volume_4h?: number | null
  volume_24h?: number | null
  count_1h?: number | null
  count_24h?: number | null
  unique_trader_1h?: number | null
  unique_trader_24h?: number | null
  kyc_holders?: number | null
  audit_info?: { [key: string]: string | number | boolean | Array<string | number | boolean | null> | { [key: string]: string | number | boolean | null } | Array<{ [key: string]: string | number | boolean | null }> | { [key: string]: Array<string | number | boolean | null> } | null }
}

export interface BinanceWeb3SmartMoneyInflowItemResponse {
  symbol?: string | null
  chain_id?: string | null
  contract_address?: string | null
  logo_url?: string | null
  price?: number | null
  market_cap?: number | null
  liquidity?: number | null
  volume?: number | null
  price_change_pct?: number | null
  holders?: number | null
  traders?: number | null
  inflow?: number | null
  risk_level?: number | null
}

export interface BinanceWeb3SocialHypeItemResponse {
  symbol?: string | null
  chain_id?: string | null
  contract_address?: string | null
  logo_url?: string | null
  market_cap?: number | null
  price_change_pct?: number | null
  social_hype?: number | null
  sentiment?: string | null
  summary?: string | null
}

export interface BinanceWeb3TokenKlineItemResponse {
  open_time?: number | null
  open?: number | null
  high?: number | null
  low?: number | null
  close?: number | null
  volume?: number | null
  trade_count?: number | null
}

export interface CryptoIndexConstituentResponse {
  id: string
  symbol: string
  name: string
  image?: string | null
  rank?: number | null
  price?: number | null
  market_cap?: number | null
  market_cap_change_24h_pct?: number | null
  price_change_24h_pct?: number | null
  volume_24h?: number | null
}

export interface CryptoIndexHistoryPointResponse {
  date: string
  timestamp: number
  market_cap: number
  index_value: number
}

export interface CryptoIndexSummaryResponse {
  current_basket_market_cap: number
  current_index_value: number
  basket_change_24h_pct: number
  btc_weight_pct: number
  eth_weight_pct: number
  common_start_date: string
  methodology: string
}

export interface CurrentPriceBatchItemResponse {
  symbol: string
  timeframe: string
  timestamp: string
  current_price: number | null
  source: string
}

export interface FundingRateHistoryPointResponse {
  funding_time: string
  funding_rate: number
  funding_rate_pct: number
  mark_price?: number | null
}

export interface IndicatorHistoryPoint {
  date: string
  value: number
}

export interface IndicatorSummaryResponse {
  ema: number | null
  rsi: number | null
  macd: MACDResponse | null
  atr: number | null
  atr_pct?: number | null
  realized_volatility_pct?: number | null
  annualized_volatility_pct?: number | null
}

export interface MACDResponse {
  dif: number | null
  dea: number | null
  histogram: number | null
}

export interface MarketHistoryBatchItemResponse {
  symbol: string
  items?: Array<OhlcvPointResponse>
}

export interface OhlcvPointResponse {
  timestamp: number
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface TradeSetupResponseItem {
  side: string
  entry: number
  target: number
  stop: number
  risk_reward: number
  confidence: number
  risk_amount: number
  entry_time: number
  style: string
  strategy: string
  source: string
}

export interface GetBinanceMarketBreakoutMonitorQueryParams {
  min_rise_pct?: number
  limit?: number
  quote_asset?: string
}
export const GetBinanceMarketBreakoutMonitorQueryParamsMeta = {"defaults": {"min_rise_pct": 5.0, "limit": 18, "quote_asset": "USDT"}, "repeatedKeys": [], "aliases": {}} as const

export interface GetBinanceMarketPageQueryParams {
  min_rise_pct?: number
  limit?: number
  quote_asset?: string
}
export const GetBinanceMarketPageQueryParamsMeta = {"defaults": {"min_rise_pct": 5.0, "limit": 24, "quote_asset": "USDT"}, "repeatedKeys": [], "aliases": {}} as const

export interface GetBinanceRwaAssetMarketStatusQueryParams {
  chain_id: string
  contract_address: string
}
export const GetBinanceRwaAssetMarketStatusQueryParamsMeta = {"defaults": {}, "repeatedKeys": [], "aliases": {}} as const

export interface GetBinanceRwaDynamicQueryParams {
  chain_id: string
  contract_address: string
}
export const GetBinanceRwaDynamicQueryParamsMeta = {"defaults": {}, "repeatedKeys": [], "aliases": {}} as const

export interface GetBinanceRwaKlineQueryParams {
  chain_id: string
  contract_address: string
  interval?: string
  limit?: number
  start_time?: number | null
  end_time?: number | null
}
export const GetBinanceRwaKlineQueryParamsMeta = {"defaults": {"interval": "1d", "limit": 120}, "repeatedKeys": [], "aliases": {}} as const

export interface GetBinanceRwaMetaQueryParams {
  chain_id: string
  contract_address: string
}
export const GetBinanceRwaMetaQueryParamsMeta = {"defaults": {}, "repeatedKeys": [], "aliases": {}} as const

export interface GetBinanceRwaSymbolsQueryParams {
  platform_type?: number | null
}
export const GetBinanceRwaSymbolsQueryParamsMeta = {"defaults": {"platform_type": 1}, "repeatedKeys": [], "aliases": {}} as const

export interface GetBinanceSpotAggTradesQueryParams {
  symbol: string
  limit?: number
  start_time?: number | null
  end_time?: number | null
}
export const GetBinanceSpotAggTradesQueryParamsMeta = {"defaults": {"limit": 50}, "repeatedKeys": [], "aliases": {}} as const

export interface GetBinanceSpotBookTickerQueryParams {
  symbols?: Array<string> | null
}
export const GetBinanceSpotBookTickerQueryParamsMeta = {"defaults": {}, "repeatedKeys": ["symbols"], "aliases": {}} as const

export interface GetBinanceSpotDepthQueryParams {
  symbol: string
  limit?: number
}
export const GetBinanceSpotDepthQueryParamsMeta = {"defaults": {"limit": 20}, "repeatedKeys": [], "aliases": {}} as const

export interface GetBinanceSpotExchangeInfoQueryParams {
  symbols?: Array<string> | null
  permissions?: Array<string> | null
  symbol_status?: string | null
}
export const GetBinanceSpotExchangeInfoQueryParamsMeta = {"defaults": {}, "repeatedKeys": ["symbols", "permissions"], "aliases": {}} as const

export interface GetBinanceSpotKlinesQueryParams {
  symbol: string
  interval: string
  limit?: number
  start_time?: number | null
  end_time?: number | null
}
export const GetBinanceSpotKlinesQueryParamsMeta = {"defaults": {"limit": 200}, "repeatedKeys": [], "aliases": {}} as const

export interface GetBinanceSpotPriceQueryParams {
  symbols?: Array<string> | null
}
export const GetBinanceSpotPriceQueryParamsMeta = {"defaults": {}, "repeatedKeys": ["symbols"], "aliases": {}} as const

export interface GetBinanceSpotTicker24hrQueryParams {
  symbols?: Array<string> | null
}
export const GetBinanceSpotTicker24hrQueryParamsMeta = {"defaults": {}, "repeatedKeys": ["symbols"], "aliases": {}} as const

export interface GetBinanceSpotTickerWindowQueryParams {
  symbols?: Array<string> | null
  window_size?: string | null
}
export const GetBinanceSpotTickerWindowQueryParamsMeta = {"defaults": {}, "repeatedKeys": ["symbols"], "aliases": {}} as const

export interface GetBinanceSpotTradesQueryParams {
  symbol: string
  limit?: number
}
export const GetBinanceSpotTradesQueryParamsMeta = {"defaults": {"limit": 50}, "repeatedKeys": [], "aliases": {}} as const

export interface GetBinanceSpotUiKlinesQueryParams {
  symbol: string
  interval: string
  limit?: number
  start_time?: number | null
  end_time?: number | null
}
export const GetBinanceSpotUiKlinesQueryParamsMeta = {"defaults": {"limit": 200}, "repeatedKeys": [], "aliases": {}} as const

export interface GetBinanceUsdmBasisQueryParams {
  pair: string
  contract_type: string
  period: string
  limit?: number
}
export const GetBinanceUsdmBasisQueryParamsMeta = {"defaults": {"limit": 30}, "repeatedKeys": [], "aliases": {}} as const

export interface GetBinanceUsdmFundingHistoryQueryParams {
  symbol?: string | null
  limit?: number
  start_time?: number | null
  end_time?: number | null
}
export const GetBinanceUsdmFundingHistoryQueryParamsMeta = {"defaults": {"limit": 100}, "repeatedKeys": [], "aliases": {}} as const

export interface GetBinanceUsdmLongShortRatioQueryParams {
  symbol: string
  period: string
  limit?: number
}
export const GetBinanceUsdmLongShortRatioQueryParamsMeta = {"defaults": {"limit": 30}, "repeatedKeys": [], "aliases": {}} as const

export interface GetBinanceUsdmMarkPriceQueryParams {
  symbol?: string | null
}
export const GetBinanceUsdmMarkPriceQueryParamsMeta = {"defaults": {}, "repeatedKeys": [], "aliases": {}} as const

export interface GetBinanceUsdmOpenInterestQueryParams {
  symbol: string
}
export const GetBinanceUsdmOpenInterestQueryParamsMeta = {"defaults": {}, "repeatedKeys": [], "aliases": {}} as const

export interface GetBinanceUsdmOpenInterestStatsQueryParams {
  symbol: string
  period: string
  limit?: number
}
export const GetBinanceUsdmOpenInterestStatsQueryParamsMeta = {"defaults": {"limit": 30}, "repeatedKeys": [], "aliases": {}} as const

export interface GetBinanceUsdmTakerVolumeQueryParams {
  symbol: string
  period: string
  limit?: number
}
export const GetBinanceUsdmTakerVolumeQueryParamsMeta = {"defaults": {"limit": 30}, "repeatedKeys": [], "aliases": {}} as const

export interface GetBinanceUsdmTicker24hrQueryParams {
  symbol?: string | null
}
export const GetBinanceUsdmTicker24hrQueryParamsMeta = {"defaults": {}, "repeatedKeys": [], "aliases": {}} as const

export interface GetBinanceUsdmTopTraderAccountsQueryParams {
  symbol: string
  period: string
  limit?: number
}
export const GetBinanceUsdmTopTraderAccountsQueryParamsMeta = {"defaults": {"limit": 30}, "repeatedKeys": [], "aliases": {}} as const

export interface GetBinanceUsdmTopTraderPositionsQueryParams {
  symbol: string
  period: string
  limit?: number
}
export const GetBinanceUsdmTopTraderPositionsQueryParamsMeta = {"defaults": {"limit": 30}, "repeatedKeys": [], "aliases": {}} as const

export interface GetBinanceWeb3AddressPnlRankQueryParams {
  chain_id: string
  period?: string
  tag?: string
  page_no?: number
  page_size?: number
}
export const GetBinanceWeb3AddressPnlRankQueryParamsMeta = {"defaults": {"period": "30d", "tag": "ALL", "page_no": 1, "page_size": 25}, "repeatedKeys": [], "aliases": {}} as const

export interface GetBinanceWeb3HeatRankQueryParams {
  chain_id?: string
  size?: number
}
export const GetBinanceWeb3HeatRankQueryParamsMeta = {"defaults": {"chain_id": "56", "size": 30}, "repeatedKeys": [], "aliases": {}} as const

export interface GetBinanceWeb3MemeRankQueryParams {
  chain_id?: string
}
export const GetBinanceWeb3MemeRankQueryParamsMeta = {"defaults": {"chain_id": "56"}, "repeatedKeys": [], "aliases": {}} as const

export interface GetBinanceWeb3SmartMoneyInflowQueryParams {
  chain_id: string
  period?: string
  tag_type?: number
}
export const GetBinanceWeb3SmartMoneyInflowQueryParamsMeta = {"defaults": {"period": "24h", "tag_type": 2}, "repeatedKeys": [], "aliases": {}} as const

export interface GetBinanceWeb3SocialHypeQueryParams {
  chain_id: string
  target_language?: string
  time_range?: number
  sentiment?: string
  social_language?: string
}
export const GetBinanceWeb3SocialHypeQueryParamsMeta = {"defaults": {"target_language": "zh", "time_range": 1, "sentiment": "All", "social_language": "ALL"}, "repeatedKeys": [], "aliases": {}} as const

export interface GetBinanceWeb3TokenAuditQueryParams {
  binance_chain_id: string
  contract_address: string
}
export const GetBinanceWeb3TokenAuditQueryParamsMeta = {"defaults": {}, "repeatedKeys": [], "aliases": {}} as const

export interface GetBinanceWeb3TokenDynamicQueryParams {
  chain_id: string
  contract_address: string
}
export const GetBinanceWeb3TokenDynamicQueryParamsMeta = {"defaults": {}, "repeatedKeys": [], "aliases": {}} as const

export interface GetBinanceWeb3TokenKlineQueryParams {
  address: string
  platform: string
  interval?: string
  limit?: number
  from_time?: number | null
  to_time?: number | null
  pm?: string | null
}
export const GetBinanceWeb3TokenKlineQueryParamsMeta = {"defaults": {"interval": "15min", "limit": 240, "pm": "p"}, "repeatedKeys": [], "aliases": {"from_time": "from", "to_time": "to"}} as const

export interface GetBinanceWeb3UnifiedTokenRankQueryParams {
  rank_type?: number
  chain_id?: string | null
  period?: number
  sort_by?: number
  order_asc?: boolean
  page?: number
  size?: number
}
export const GetBinanceWeb3UnifiedTokenRankQueryParamsMeta = {"defaults": {"rank_type": 10, "period": 50, "sort_by": 0, "order_asc": false, "page": 1, "size": 20}, "repeatedKeys": [], "aliases": {}} as const

export interface GetCryptoIndexQueryParams {
  top_n?: number
  days?: number
}
export const GetCryptoIndexQueryParamsMeta = {"defaults": {"top_n": 20, "days": 90}, "repeatedKeys": [], "aliases": {}} as const

export interface GetCurrentFundingRateQueryParams {
  symbol: string
}
export const GetCurrentFundingRateQueryParamsMeta = {"defaults": {}, "repeatedKeys": [], "aliases": {}} as const

export interface GetCurrentPriceBatchQueryParams {
  symbols: Array<string>
  timeframe?: string
}
export const GetCurrentPriceBatchQueryParamsMeta = {"defaults": {"timeframe": "1d"}, "repeatedKeys": ["symbols"], "aliases": {}} as const

export interface GetCurrentPriceQueryParams {
  symbol: string
  timeframe?: string
}
export const GetCurrentPriceQueryParamsMeta = {"defaults": {"timeframe": "1d"}, "repeatedKeys": [], "aliases": {}} as const

export interface GetFundingRateHistoryQueryParams {
  symbol: string
  start_date?: string | null
  end_date?: string | null
  limit?: number | null
}
export const GetFundingRateHistoryQueryParamsMeta = {"defaults": {}, "repeatedKeys": [], "aliases": {}} as const

export interface GetIndexHistoryQueryParams {
  symbol: string
  timeframe?: string
  start_date?: string
  end_date?: string | null
}
export const GetIndexHistoryQueryParamsMeta = {"defaults": {"timeframe": "1d", "start_date": "2010-01-01"}, "repeatedKeys": [], "aliases": {}} as const

export interface GetIndexPricingHistoryQueryParams {
  symbol: string
  timeframe?: string
  start_date?: string
  end_date?: string | null
}
export const GetIndexPricingHistoryQueryParamsMeta = {"defaults": {"timeframe": "1d", "start_date": "2010-01-01"}, "repeatedKeys": [], "aliases": {}} as const

export interface GetKlineTailQueryParams {
  symbol: string
  timeframe: string
  limit?: number
}
export const GetKlineTailQueryParamsMeta = {"defaults": {"limit": 2}, "repeatedKeys": [], "aliases": {}} as const

export interface GetLatestIndexPricingQueryParams {
  symbol: string
}
export const GetLatestIndexPricingQueryParamsMeta = {"defaults": {}, "repeatedKeys": [], "aliases": {}} as const

export interface GetLatestIndexQueryParams {
  symbol: string
}
export const GetLatestIndexQueryParamsMeta = {"defaults": {}, "repeatedKeys": [], "aliases": {}} as const

export interface GetLatestKlinesQueryParams {
  symbol: string
  timeframe: string
  limit?: number
}
export const GetLatestKlinesQueryParamsMeta = {"defaults": {"limit": 1000}, "repeatedKeys": [], "aliases": {}} as const

export interface GetMarketFullHistoryBatchQueryParams {
  symbols: Array<string>
  timeframe?: string
  start_date?: string
  fetch_policy?: "cache_only" | "hydrate"
}
export const GetMarketFullHistoryBatchQueryParamsMeta = {"defaults": {"timeframe": "1d", "start_date": "2010-01-01", "fetch_policy": "hydrate"}, "repeatedKeys": ["symbols"], "aliases": {}} as const

export interface GetMarketFullHistoryQueryParams {
  symbol: string
  timeframe?: string
  start_date?: string
  fetch_policy?: "cache_only" | "hydrate"
}
export const GetMarketFullHistoryQueryParamsMeta = {"defaults": {"timeframe": "1d", "start_date": "2010-01-01", "fetch_policy": "hydrate"}, "repeatedKeys": [], "aliases": {}} as const

export interface GetMarketHistoryQueryParams {
  symbol: string
  timeframe: string
  end_ts: number
  limit?: number
}
export const GetMarketHistoryQueryParamsMeta = {"defaults": {"limit": 500}, "repeatedKeys": [], "aliases": {}} as const

export interface GetMarketIndicatorsQueryParams {
  category?: string | null
  days?: number
}
export const GetMarketIndicatorsQueryParamsMeta = {"defaults": {"days": 30}, "repeatedKeys": [], "aliases": {}} as const

export interface GetRealtimeAnalysisQueryParams {
  symbol: string
  timeframe?: string | null
  limit?: number | null
}
export const GetRealtimeAnalysisQueryParamsMeta = {"defaults": {}, "repeatedKeys": [], "aliases": {}} as const

export interface GetTechnicalMetricsQueryParams {
  symbol: string
  timeframe?: string
  limit?: number
  atr_period?: number
  volatility_period?: number
}
export const GetTechnicalMetricsQueryParamsMeta = {"defaults": {"timeframe": "1d", "limit": 120, "atr_period": 14, "volatility_period": 20}, "repeatedKeys": [], "aliases": {}} as const

export interface GetTradeSetupQueryParams {
  symbol: string
  timeframe?: string
  limit?: number
  account_size?: number
  style?: string
  strategy?: string
  mode?: string
}
export const GetTradeSetupQueryParamsMeta = {"defaults": {"timeframe": "1h", "limit": 120, "account_size": 1000, "style": "Scalping", "strategy": "最大收益", "mode": "rules"}, "repeatedKeys": [], "aliases": {}} as const

export interface SyncFundingRateHistoryQueryParams {
  symbol: string
  start_date?: string
  end_date?: string | null
}
export const SyncFundingRateHistoryQueryParamsMeta = {"defaults": {"start_date": "2019-09-01"}, "repeatedKeys": [], "aliases": {}} as const
