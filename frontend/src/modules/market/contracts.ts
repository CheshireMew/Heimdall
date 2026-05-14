import type {
  BinanceBreakoutMonitorItemResponse,
  BinanceContractResearchDetailResponse,
  BinanceWeb3HeatRankItemResponse,
  BinanceWeb3TokenAuditResponse,
  BinanceWeb3TokenDynamicResponse,
  MarketSymbolSearchResponse,
  OhlcvPointResponse,
} from './generatedContracts'
export type * from './generatedContracts'

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

export interface SentimentCache {
  value: SentimentData | null
  timestamp: number
}

export type BinanceBreakoutMonitorItem = BinanceBreakoutMonitorItemResponse
export type BinanceContractResearchDetail = BinanceContractResearchDetailResponse
export type BinanceWeb3HeatRankItem = BinanceWeb3HeatRankItemResponse
export type BinanceWeb3TokenAudit = BinanceWeb3TokenAuditResponse
export type BinanceWeb3TokenDynamic = BinanceWeb3TokenDynamicResponse
export type MarketSymbolSearchItem = MarketSymbolSearchResponse

