// This file is generated from backend Pydantic schemas.
// Do not edit manually.

export interface RealtimeResponse {
  symbol: string
  timestamp: string
  current_price: number
  indicators: IndicatorSummaryResponse
  ai_analysis: unknown | null
  kline_data: Array<OHLCVRaw>
  timeframe?: string | null
  type?: string | null
}

export interface KlineTailResponse {
  symbol: string
  timeframe: string
  timestamp: string
  current_price: number | null
  kline_data: Array<OHLCVRaw>
}

export interface CurrentPriceResponse {
  symbol: string
  timeframe: string
  timestamp: string
  current_price: number | null
}

export interface IndicatorItem {
  indicator_id: string
  name: string
  category: string
  unit: string | null
  current_value: number | null
  last_updated: string | null
  history: Array<IndicatorHistoryPoint>
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

export interface MarketSymbolSearchItem {
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
  data: Array<OHLCVRaw>
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

export interface FundingRateHistoryPointResponse {
  funding_time: string
  funding_rate: number
  funding_rate_pct: number
  mark_price?: number | null
}

export interface FundingRateHistoryResponse {
  exchange: string
  market_type: string
  symbol: string
  count: number
  items: Array<FundingRateHistoryPointResponse>
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

export interface TradeSetupResponse {
  symbol: string
  timeframe: string
  timestamp: string
  current_price: number | null
  setup: TradeSetupResponseItem | null
  reason: string
  source: string
}

export interface ApiStatusResponse {
  status: string
  version: string
  framework: string
  dependencies: string
  timestamp: string
}

export interface DisplayCurrencyResponse {
  code: string
  name: string
  symbol: string
  locale: string
  fraction_digits: number
}

export interface CurrencyRatesResponse {
  base: string
  rates: { [key: string]: number }
  supported: Array<DisplayCurrencyResponse>
  updated_at: string
  source: string
  is_fallback?: boolean
}

export interface CryptoIndexConstituent {
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

export interface CryptoIndexHistoryPoint {
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

export interface CryptoIndexResponse {
  top_n: number
  days: number
  base_value: number
  constituents: Array<CryptoIndexConstituent>
  history: Array<CryptoIndexHistoryPoint>
  summary?: CryptoIndexSummaryResponse | null
  is_partial?: boolean
  resolved_constituents_count?: number | null
  missing_symbols?: Array<string>
}

export interface MACDResponse {
  dif: number | null
  dea: number | null
  histogram: number | null
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

export interface BinanceExchangeInfoResponse {
  exchange: string
  market: string
  timezone?: string | null
  server_time?: number | null
  symbols?: Array<BinanceSymbolSummaryResponse>
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

export interface BinanceTickerStatsResponse {
  exchange: string
  market: string
  items?: Array<BinanceTickerStatsItemResponse>
}

export interface BinancePriceTickerItemResponse {
  symbol?: string | null
  price?: number | null
}

export interface BinancePriceTickerResponse {
  exchange: string
  market: string
  items?: Array<BinancePriceTickerItemResponse>
}

export interface BinanceBookTickerItemResponse {
  symbol?: string | null
  bid_price?: number | null
  bid_qty?: number | null
  ask_price?: number | null
  ask_qty?: number | null
}

export interface BinanceBookTickerResponse {
  exchange: string
  market: string
  items?: Array<BinanceBookTickerItemResponse>
}

export interface BinanceOrderBookLevelResponse {
  price?: number | null
  qty?: number | null
}

export interface BinanceOrderBookResponse {
  exchange: string
  market: string
  symbol: string
  last_update_id?: number | null
  bids?: Array<BinanceOrderBookLevelResponse>
  asks?: Array<BinanceOrderBookLevelResponse>
}

export interface BinanceTradeItemResponse {
  id?: number | null
  price?: number | null
  qty?: number | null
  quote_qty?: number | null
  time?: number | null
  is_buyer_maker?: boolean
}

export interface BinanceTradeListResponse {
  exchange: string
  market: string
  symbol: string
  items?: Array<BinanceTradeItemResponse>
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

export interface BinanceKlineResponse {
  exchange: string
  market: string
  symbol: string
  interval: string
  items?: Array<BinanceKlineItemResponse>
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

export interface BinanceMarkPriceResponse {
  exchange: string
  market: string
  items?: Array<BinanceMarkPriceItemResponse>
}

export interface BinanceFundingInfoItemResponse {
  symbol?: string | null
  adjusted_funding_rate_cap?: number | null
  adjusted_funding_rate_floor?: number | null
  funding_interval_hours?: number | null
  disclaimer?: boolean
}

export interface BinanceFundingInfoResponse {
  exchange: string
  market: string
  items?: Array<BinanceFundingInfoItemResponse>
}

export interface BinanceFundingHistoryItemResponse {
  symbol?: string | null
  funding_rate?: number | null
  mark_price?: number | null
  funding_time?: number | null
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

export interface BinanceOpenInterestStatItemResponse {
  symbol?: string | null
  pair?: string | null
  contract_type?: string | null
  sum_open_interest?: number | null
  sum_open_interest_value?: number | null
  timestamp?: number | null
}

export interface BinanceOpenInterestStatsResponse {
  exchange: string
  market: string
  items?: Array<BinanceOpenInterestStatItemResponse>
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

export interface BinanceRatioSeriesResponse {
  exchange: string
  market: string
  items?: Array<BinanceRatioItemResponse>
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
  volume_24h?: number | null
  unique_trader_24h?: number | null
  kyc_holders?: number | null
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

export interface BinanceWeb3SocialHypeResponse {
  source: string
  leaderboard: string
  items?: Array<BinanceWeb3SocialHypeItemResponse>
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

export interface BinanceWeb3SmartMoneyInflowResponse {
  source: string
  leaderboard: string
  items?: Array<BinanceWeb3SmartMoneyInflowItemResponse>
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

export interface BinanceWeb3MemeRankResponse {
  source: string
  leaderboard: string
  items?: Array<BinanceWeb3MemeRankItemResponse>
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

export interface BinanceWeb3AddressPnlResponse {
  source: string
  leaderboard: string
  page: number
  size: number
  pages?: number | null
  items?: Array<BinanceWeb3AddressPnlItemResponse>
}

export interface BinanceRwaSymbolItemResponse {
  chain_id?: string | null
  contract_address?: string | null
  symbol?: string | null
  ticker?: string | null
  type?: number | null
  multiplier?: number | null
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
  company_info?: { [key: string]: unknown }
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
  token_info?: { [key: string]: unknown }
  stock_info?: { [key: string]: unknown }
  status_info?: { [key: string]: unknown }
  limit_info?: { [key: string]: unknown }
}

export interface BinanceRwaKlineItemResponse {
  open_time?: number | null
  open?: number | null
  high?: number | null
  low?: number | null
  close?: number | null
  close_time?: number | null
}

export interface BinanceRwaKlineResponse {
  source: string
  chain_id: string
  contract_address: string
  interval: string
  decimals?: number | null
  items?: Array<BinanceRwaKlineItemResponse>
}

export interface BinanceReservedFeatureResponse {
  source: string
  feature: string
  status: string
  message: string
  skill_name?: string | null
  skill_version?: string | null
  supported_chains?: Array<{ [key: string]: string }>
  reserved_endpoints?: Array<{ [key: string]: unknown }>
  response_fields?: Array<string>
  notes?: Array<string>
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

export interface IndicatorHistoryPoint {
  date: string
  value: number
}

export type OHLCVRaw = [number, number, number, number, number, number]

export interface CandlestickData {
  time: number
  open: number
  high: number
  low: number
  close: number
}

export interface VolumeData {
  time: number
  value: number
  color: string
}

export interface RealtimeParams {
  symbol: string
  timeframe?: string
  limit?: number
}

export interface HistoryParams {
  symbol: string
  timeframe: string
  end_ts: number
  limit?: number
}

export interface LatestKlineParams {
  symbol: string
  timeframe: string
  limit?: number
}

export interface TailKlineParams {
  symbol: string
  timeframe: string
  limit?: number
}

export interface CurrentPriceParams {
  symbol: string
  timeframe?: string
}

export interface FullHistoryParams {
  symbol: string
  timeframe?: string
  start_date?: string
  fetch_policy?: 'cache_only' | 'hydrate'
}

export interface BatchFullHistoryParams {
  symbols: string[]
  timeframe?: string
  start_date?: string
  fetch_policy?: 'cache_only' | 'hydrate'
}

export interface IndicatorParams {
  category?: string
  days?: number
}

export interface CryptoIndexParams {
  top_n?: number
  days?: number
}

export interface IndexHistoryParams {
  symbol: string
  timeframe?: string
  start_date?: string
  end_date?: string
}

export type BatchFullHistoryResponse = Record<string, OHLCVRaw[]>

export interface SentimentData {
  value: number
  label: string
  last_updated: string | null
}

export interface KlineCacheEntry {
  data: OHLCVRaw[]
  timestamp: number
}

export interface SentimentCache {
  value: SentimentData | null
  timestamp: number
}
