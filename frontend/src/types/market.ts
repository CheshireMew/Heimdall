/**
 * Heimdall shared type definitions
 * Mirrors backend app/infra/db/schema.py data contracts
 */

// ==========================================
// K-Line / OHLCV
// ==========================================

/** Raw OHLCV array from exchange: [timestamp_ms, open, high, low, close, volume] */
export type OHLCVRaw = [number, number, number, number, number, number]

/** Formatted candlestick for lightweight-charts */
export interface CandlestickData {
  time: number
  open: number
  high: number
  low: number
  close: number
}

/** Formatted volume bar for lightweight-charts */
export interface VolumeData {
  time: number
  value: number
  color: string
}

// ==========================================
// API Parameters
// ==========================================

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

export interface FullHistoryParams {
  symbol: string
  timeframe?: string
  start_date?: string
}

export interface BatchFullHistoryParams {
  symbols: string[]
  timeframe?: string
  start_date?: string
}

export interface IndicatorParams {
  category?: string
  days?: number
}

export interface CryptoIndexParams {
  top_n?: number
  days?: number
}

export type BatchFullHistoryResponse = Record<string, OHLCVRaw[]>

// ==========================================
// API Response Types
// ==========================================

export interface RealtimeResponse {
  symbol: string
  timestamp: string
  current_price: number
  indicators: {
    ema: number | null
    rsi: number | null
    macd: {
      dif: number | null
      dea: number | null
      histogram: number | null
    } | null
    atr: number | null
  }
  ai_analysis: Record<string, unknown> | null
  kline_data: OHLCVRaw[]
  timeframe?: string | null
  type?: string | null
}

export interface IndicatorItem {
  indicator_id: string
  name: string
  category: string
  unit: string
  current_value: number | null
  last_updated: string | null
  history: Array<{ date: string; value: number }>
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

export interface CryptoIndexResponse {
  top_n: number
  days: number
  base_value: number
  constituents: CryptoIndexConstituent[]
  history: CryptoIndexHistoryPoint[]
  summary: {
    current_basket_market_cap: number
    current_index_value: number
    basket_change_24h_pct: number
    btc_weight_pct: number
    eth_weight_pct: number
    common_start_date: string
    methodology: string
  }
  is_partial?: boolean
  resolved_constituents_count?: number | null
  missing_symbols?: string[]
}

export interface SentimentData {
  value: number
  label: string
  last_updated: string | null
}

// ==========================================
// Store Types
// ==========================================

export interface KlineCacheEntry {
  data: OHLCVRaw[]
  timestamp: number
}

export interface SentimentCache {
  value: SentimentData | null
  timestamp: number
}
