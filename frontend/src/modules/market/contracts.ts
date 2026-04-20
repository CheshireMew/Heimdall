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
  GetBinanceMarketBreakoutMonitorQueryParams,
  GetBinanceMarketPageQueryParams,
  GetBinanceRwaAssetMarketStatusQueryParams,
  GetBinanceRwaDynamicQueryParams,
  GetBinanceRwaKlineQueryParams,
  GetBinanceRwaMetaQueryParams,
  GetBinanceRwaSymbolsQueryParams,
  GetBinanceSpotPriceQueryParams,
  GetBinanceSpotTicker24hrQueryParams,
  GetBinanceUsdmMarkPriceQueryParams,
  GetBinanceUsdmTopTraderAccountsQueryParams,
  GetBinanceUsdmTopTraderPositionsQueryParams,
  GetBinanceUsdmTicker24hrQueryParams,
  GetBinanceWeb3AddressPnlRankQueryParams,
  GetBinanceWeb3HeatRankQueryParams,
  GetBinanceWeb3MemeRankQueryParams,
  GetBinanceWeb3SmartMoneyInflowQueryParams,
  GetBinanceWeb3SocialHypeQueryParams,
  GetBinanceWeb3TokenAuditQueryParams,
  GetBinanceWeb3TokenDynamicQueryParams,
  GetBinanceWeb3TokenKlineQueryParams,
  GetBinanceWeb3UnifiedTokenRankQueryParams,
  GetCryptoIndexQueryParams,
  GetCurrentPriceBatchQueryParams,
  GetCurrentPriceQueryParams,
  GetIndexHistoryQueryParams,
  GetIndexPricingHistoryQueryParams,
  GetKlineTailQueryParams,
  GetLatestKlinesQueryParams,
  GetMarketFullHistoryBatchQueryParams,
  GetMarketFullHistoryQueryParams,
  GetMarketHistoryQueryParams,
  GetMarketIndicatorsQueryParams,
  GetRealtimeAnalysisQueryParams,
  GetTechnicalMetricsQueryParams,
  GetTradeSetupQueryParams,
} from '@/types/market'
import {
  GetBinanceSpotPriceQueryParamsMeta,
  GetBinanceSpotTicker24hrQueryParamsMeta,
  GetBinanceWeb3TokenKlineQueryParamsMeta,
  GetCurrentPriceBatchQueryParamsMeta,
  GetMarketFullHistoryBatchQueryParamsMeta,
} from '@/types/market'

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
  GetBinanceMarketBreakoutMonitorQueryParams,
  GetBinanceMarketPageQueryParams,
  GetBinanceRwaAssetMarketStatusQueryParams,
  GetBinanceRwaDynamicQueryParams,
  GetBinanceRwaKlineQueryParams,
  GetBinanceRwaMetaQueryParams,
  GetBinanceRwaSymbolsQueryParams,
  GetBinanceSpotPriceQueryParams,
  GetBinanceSpotTicker24hrQueryParams,
  GetBinanceUsdmMarkPriceQueryParams,
  GetBinanceUsdmTopTraderAccountsQueryParams,
  GetBinanceUsdmTopTraderPositionsQueryParams,
  GetBinanceUsdmTicker24hrQueryParams,
  GetBinanceWeb3AddressPnlRankQueryParams,
  GetBinanceWeb3HeatRankQueryParams,
  GetBinanceWeb3MemeRankQueryParams,
  GetBinanceWeb3SmartMoneyInflowQueryParams,
  GetBinanceWeb3SocialHypeQueryParams,
  GetBinanceWeb3TokenAuditQueryParams,
  GetBinanceWeb3TokenDynamicQueryParams,
  GetBinanceWeb3TokenKlineQueryParams,
  GetBinanceWeb3UnifiedTokenRankQueryParams,
  GetCryptoIndexQueryParams,
  GetCurrentPriceBatchQueryParams,
  GetCurrentPriceQueryParams,
  GetIndexHistoryQueryParams,
  GetIndexPricingHistoryQueryParams,
  GetKlineTailQueryParams,
  GetLatestKlinesQueryParams,
  GetMarketFullHistoryBatchQueryParams,
  GetMarketFullHistoryQueryParams,
  GetMarketHistoryQueryParams,
  GetMarketIndicatorsQueryParams,
  GetRealtimeAnalysisQueryParams,
  GetTechnicalMetricsQueryParams,
  GetTradeSetupQueryParams,
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

export type RealtimeParams = GetRealtimeAnalysisQueryParams
export type HistoryParams = GetMarketHistoryQueryParams
export type LatestKlineParams = GetLatestKlinesQueryParams
export type TailKlineParams = GetKlineTailQueryParams
export type CurrentPriceParams = GetCurrentPriceQueryParams
export type FullHistoryParams = GetMarketFullHistoryQueryParams
export type BatchFullHistoryParams = GetMarketFullHistoryBatchQueryParams
export type IndicatorParams = GetMarketIndicatorsQueryParams
export type CryptoIndexParams = GetCryptoIndexQueryParams
export type IndexHistoryParams = GetIndexHistoryQueryParams

export const CURRENT_PRICE_BATCH_QUERY_META = GetCurrentPriceBatchQueryParamsMeta
export const FULL_HISTORY_BATCH_QUERY_META = GetMarketFullHistoryBatchQueryParamsMeta
export const BINANCE_SPOT_TICKER_24HR_QUERY_META = GetBinanceSpotTicker24hrQueryParamsMeta
export const BINANCE_SPOT_PRICE_QUERY_META = GetBinanceSpotPriceQueryParamsMeta
export const BINANCE_WEB3_TOKEN_KLINE_QUERY_META = GetBinanceWeb3TokenKlineQueryParamsMeta

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
