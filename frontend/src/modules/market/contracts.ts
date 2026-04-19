import type {
  BinanceBreakoutMonitorItemResponse,
  BinanceBreakoutMonitorResponse,
  BinanceExchangeInfoResponse,
  BinanceMarketPageResponse,
  BinanceMarkPriceItemResponse,
  BinanceMarkPriceResponse,
  BinancePriceTickerResponse,
  BinanceRatioSeriesResponse,
  BinanceRwaDynamicResponse,
  BinanceRwaKlineItemResponse,
  BinanceRwaKlineResponse,
  BinanceRwaMarketStatusResponse,
  BinanceRwaMetaResponse,
  BinanceRwaSymbolItemResponse,
  BinanceRwaSymbolListResponse,
  BinanceTickerStatsItemResponse,
  BinanceTickerStatsResponse,
  BinanceWeb3AddressPnlItemResponse,
  BinanceWeb3AddressPnlResponse,
  BinanceWeb3HeatRankItemResponse,
  BinanceWeb3HeatRankResponse,
  BinanceWeb3MemeRankItemResponse,
  BinanceWeb3MemeRankResponse,
  BinanceWeb3RankItemResponse,
  BinanceWeb3SmartMoneyInflowItemResponse,
  BinanceWeb3SmartMoneyInflowResponse,
  BinanceWeb3SocialHypeItemResponse,
  BinanceWeb3SocialHypeResponse,
  BinanceWeb3TokenAuditResponse,
  BinanceWeb3TokenDynamicResponse,
  BinanceWeb3TokenKlineItemResponse,
  BinanceWeb3TokenKlineResponse,
  BinanceWeb3UnifiedTokenRankResponse,
  CurrentPriceBatchResponse,
  CurrentPriceResponse,
  CryptoIndexConstituentResponse,
  CryptoIndexHistoryPointResponse,
  CryptoIndexResponse,
  KlineTailResponse,
  MarketHistoryBatchItemResponse,
  MarketHistoryBatchResponse,
  MarketHistoryResponse,
  MarketIndexHistoryResponse,
  MarketIndicatorResponse,
  MarketSymbolSearchResponse,
  OhlcvPointResponse,
  RealtimeResponse,
  TradeSetupResponse,
} from '@/types'

export type {
  BinanceBreakoutMonitorItemResponse,
  BinanceBreakoutMonitorResponse,
  BinanceExchangeInfoResponse,
  BinanceMarketPageResponse,
  BinanceMarkPriceItemResponse,
  BinanceMarkPriceResponse,
  BinancePriceTickerResponse,
  BinanceRatioSeriesResponse,
  BinanceRwaDynamicResponse,
  BinanceRwaKlineItemResponse,
  BinanceRwaKlineResponse,
  BinanceRwaMarketStatusResponse,
  BinanceRwaMetaResponse,
  BinanceRwaSymbolItemResponse,
  BinanceRwaSymbolListResponse,
  BinanceTickerStatsItemResponse,
  BinanceTickerStatsResponse,
  BinanceWeb3AddressPnlItemResponse,
  BinanceWeb3AddressPnlResponse,
  BinanceWeb3HeatRankItemResponse,
  BinanceWeb3HeatRankResponse,
  BinanceWeb3MemeRankItemResponse,
  BinanceWeb3MemeRankResponse,
  BinanceWeb3RankItemResponse,
  BinanceWeb3SmartMoneyInflowItemResponse,
  BinanceWeb3SmartMoneyInflowResponse,
  BinanceWeb3SocialHypeItemResponse,
  BinanceWeb3SocialHypeResponse,
  BinanceWeb3TokenAuditResponse,
  BinanceWeb3TokenDynamicResponse,
  BinanceWeb3TokenKlineItemResponse,
  BinanceWeb3TokenKlineResponse,
  BinanceWeb3UnifiedTokenRankResponse,
  CurrentPriceBatchResponse,
  CurrentPriceResponse,
  CryptoIndexResponse,
  KlineTailResponse,
  MarketHistoryBatchItemResponse,
  MarketHistoryBatchResponse,
  MarketHistoryResponse,
  MarketIndexHistoryResponse,
  MarketIndicatorResponse,
  MarketSymbolSearchResponse,
  OhlcvPointResponse,
  RealtimeResponse,
  TradeSetupResponse,
}

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

export type CryptoIndexConstituent = CryptoIndexConstituentResponse
export type CryptoIndexHistoryPoint = CryptoIndexHistoryPointResponse

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
