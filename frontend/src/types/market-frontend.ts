import type {
  CryptoIndexConstituentResponse,
  CryptoIndexHistoryPointResponse,
  MarketIndicatorResponse,
  MarketSymbolSearchResponse,
} from './market'

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
export type IndicatorItem = MarketIndicatorResponse
export type MarketSymbolSearchItem = MarketSymbolSearchResponse
export type CryptoIndexConstituent = CryptoIndexConstituentResponse
export type CryptoIndexHistoryPoint = CryptoIndexHistoryPointResponse

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
