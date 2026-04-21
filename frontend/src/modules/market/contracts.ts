import type { OhlcvPointResponse } from '../../types/market'

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

export interface SentimentData {
  value: number
  label: string
  last_updated: string | null
}

export interface KlineCacheEntry {
  data: OhlcvPointResponse[]
  timestamp: number
}

export interface SentimentCache {
  value: SentimentData | null
  timestamp: number
}
