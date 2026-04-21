import { apiGet, longTaskRequest } from '@/api/request'
import type { AxiosResponse } from 'axios'
import type {
  BinanceBreakoutMonitorResponse,
  BinanceExchangeInfoResponse,
  BinanceMarkPriceResponse,
  BinanceMarketPageResponse,
  BinancePriceTickerResponse,
  BinanceRatioSeriesResponse,
  BinanceRwaDynamicResponse,
  BinanceRwaKlineResponse,
  BinanceRwaMarketStatusResponse,
  BinanceRwaMetaResponse,
  BinanceRwaSymbolListResponse,
  BinanceTickerStatsResponse,
  BinanceWeb3AddressPnlResponse,
  BinanceWeb3HeatRankResponse,
  BinanceWeb3MemeRankResponse,
  BinanceWeb3SmartMoneyInflowResponse,
  BinanceWeb3SocialHypeResponse,
  BinanceWeb3TokenAuditResponse,
  BinanceWeb3TokenDynamicResponse,
  BinanceWeb3TokenKlineResponse,
  BinanceWeb3UnifiedTokenRankResponse,
  CurrentPriceBatchResponse,
  CurrentPriceResponse,
  RealtimeResponse,
  KlineTailResponse,
  TradeSetupResponse,
  MarketHistoryResponse,
  MarketHistoryBatchResponse,
  MarketIndicatorResponse,
  CryptoIndexResponse,
  MarketIndexHistoryResponse,
  MarketSymbolSearchResponse,
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
  GetBinanceUsdmTicker24hrQueryParams,
  GetBinanceUsdmTopTraderAccountsQueryParams,
  GetBinanceUsdmTopTraderPositionsQueryParams,
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
  GetKlineTailQueryParams,
  GetLatestKlinesQueryParams,
  GetMarketFullHistoryBatchQueryParams,
  GetMarketFullHistoryQueryParams,
  GetMarketHistoryQueryParams,
  GetMarketIndicatorsQueryParams,
  GetRealtimeAnalysisQueryParams,
  GetTradeSetupQueryParams,
} from '../../types/market'

export const marketApi = {
  getSymbols(): Promise<AxiosResponse<MarketSymbolSearchResponse[]>> {
    return apiGet('list_market_symbols')
  },

  getRealtime(params: GetRealtimeAnalysisQueryParams): Promise<AxiosResponse<RealtimeResponse>> {
    return apiGet('get_realtime_analysis', { query: params })
  },

  getTradeSetup(params: GetTradeSetupQueryParams & {
    signal?: AbortSignal
  }): Promise<AxiosResponse<TradeSetupResponse>> {
    const client = params.mode === 'ai' ? longTaskRequest : undefined
    const { signal, ...query } = params
    return apiGet('get_trade_setup', {
      client,
      query,
      signal,
      timeout: params.mode === 'ai' ? 180000 : 15000,
    })
  },

  getIndicators(params: GetMarketIndicatorsQueryParams): Promise<AxiosResponse<MarketIndicatorResponse[]>> {
    return apiGet('get_market_indicators', { query: params })
  },

  getPriceSeriesWindow(params: GetMarketHistoryQueryParams): Promise<AxiosResponse<MarketHistoryResponse>> {
    return apiGet('get_market_history', { query: params })
  },

  getLatestKlines(params: GetLatestKlinesQueryParams): Promise<AxiosResponse<MarketHistoryResponse>> {
    return apiGet('get_latest_klines', { query: params })
  },

  getPriceSeriesTail(params: GetKlineTailQueryParams): Promise<AxiosResponse<KlineTailResponse>> {
    return apiGet('get_kline_tail', { query: params })
  },

  getCurrentPrice(params: GetCurrentPriceQueryParams): Promise<AxiosResponse<CurrentPriceResponse>> {
    return apiGet('get_current_price', { query: params })
  },

  getCurrentPriceBatch(params: GetCurrentPriceBatchQueryParams): Promise<AxiosResponse<CurrentPriceBatchResponse>> {
    return apiGet('get_current_price_batch', { query: params })
  },

  getPriceHistory(params: GetMarketFullHistoryQueryParams): Promise<AxiosResponse<MarketHistoryResponse>> {
    return apiGet('get_market_full_history', { query: params })
  },

  getBatchPriceHistory(params: GetMarketFullHistoryBatchQueryParams): Promise<AxiosResponse<MarketHistoryBatchResponse>> {
    return apiGet('get_market_full_history_batch', { query: params })
  },

  getCryptoIndex(params: GetCryptoIndexQueryParams): Promise<AxiosResponse<CryptoIndexResponse>> {
    return apiGet('get_crypto_index', { query: params })
  },

  getIndexHistory(params: GetIndexHistoryQueryParams): Promise<AxiosResponse<MarketIndexHistoryResponse>> {
    return apiGet('get_index_history', { query: params })
  },

  getIndexPricingHistory(params: GetIndexHistoryQueryParams): Promise<AxiosResponse<MarketIndexHistoryResponse>> {
    return apiGet('get_index_pricing_history', { query: params })
  },

  getBinanceSpotTicker24h(params: GetBinanceSpotTicker24hrQueryParams = {}): Promise<AxiosResponse<BinanceTickerStatsResponse>> {
    return apiGet('get_binance_spot_ticker_24hr', { query: params })
  },

  getBinanceBreakoutMonitor(params: GetBinanceMarketBreakoutMonitorQueryParams = {}): Promise<AxiosResponse<BinanceBreakoutMonitorResponse>> {
    return apiGet('get_binance_market_breakout_monitor', { query: params })
  },

  getBinanceMarketPage(params: GetBinanceMarketPageQueryParams = {}): Promise<AxiosResponse<BinanceMarketPageResponse>> {
    return apiGet('get_binance_market_page', { query: params, timeout: 30000 })
  },

  getBinanceSpotPrice(params: GetBinanceSpotPriceQueryParams = {}): Promise<AxiosResponse<BinancePriceTickerResponse>> {
    return apiGet('get_binance_spot_price', { query: params })
  },

  getBinanceUsdmTicker24h(params: GetBinanceUsdmTicker24hrQueryParams = {}): Promise<AxiosResponse<BinanceTickerStatsResponse>> {
    return apiGet('get_binance_usdm_ticker_24hr', { query: params })
  },

  getBinanceUsdmMarkPrice(params: GetBinanceUsdmMarkPriceQueryParams = {}): Promise<AxiosResponse<BinanceMarkPriceResponse>> {
    return apiGet('get_binance_usdm_mark_price', { query: params })
  },

  getBinanceUsdmTopTraderAccounts(params: GetBinanceUsdmTopTraderAccountsQueryParams): Promise<AxiosResponse<BinanceRatioSeriesResponse>> {
    return apiGet('get_binance_usdm_top_trader_accounts', { query: params })
  },

  getBinanceUsdmTopTraderPositions(params: GetBinanceUsdmTopTraderPositionsQueryParams): Promise<AxiosResponse<BinanceRatioSeriesResponse>> {
    return apiGet('get_binance_usdm_top_trader_positions', { query: params })
  },

  getBinanceWeb3SocialHype(params: GetBinanceWeb3SocialHypeQueryParams): Promise<AxiosResponse<BinanceWeb3SocialHypeResponse>> {
    return apiGet('get_binance_web3_social_hype', { query: params })
  },

  getBinanceWeb3UnifiedTokenRank(params: GetBinanceWeb3UnifiedTokenRankQueryParams): Promise<AxiosResponse<BinanceWeb3UnifiedTokenRankResponse>> {
    return apiGet('get_binance_web3_unified_token_rank', { query: params })
  },

  getBinanceWeb3SmartMoneyInflow(params: GetBinanceWeb3SmartMoneyInflowQueryParams): Promise<AxiosResponse<BinanceWeb3SmartMoneyInflowResponse>> {
    return apiGet('get_binance_web3_smart_money_inflow', { query: params })
  },

  getBinanceWeb3MemeRank(params: GetBinanceWeb3MemeRankQueryParams = {}): Promise<AxiosResponse<BinanceWeb3MemeRankResponse>> {
    return apiGet('get_binance_web3_meme_rank', { query: params })
  },

  getBinanceWeb3AddressPnlRank(params: GetBinanceWeb3AddressPnlRankQueryParams): Promise<AxiosResponse<BinanceWeb3AddressPnlResponse>> {
    return apiGet('get_binance_web3_address_pnl_rank', { query: params })
  },

  getBinanceWeb3HeatRank(params: GetBinanceWeb3HeatRankQueryParams = {}): Promise<AxiosResponse<BinanceWeb3HeatRankResponse>> {
    return apiGet('get_binance_web3_heat_rank', { query: params, timeout: 30000 })
  },

  getBinanceWeb3TokenDynamic(params: GetBinanceWeb3TokenDynamicQueryParams): Promise<AxiosResponse<BinanceWeb3TokenDynamicResponse>> {
    return apiGet('get_binance_web3_token_dynamic', { query: params })
  },

  getBinanceWeb3TokenKline(params: GetBinanceWeb3TokenKlineQueryParams): Promise<AxiosResponse<BinanceWeb3TokenKlineResponse>> {
    return apiGet('get_binance_web3_token_kline', { query: params })
  },

  getBinanceWeb3TokenAudit(params: GetBinanceWeb3TokenAuditQueryParams): Promise<AxiosResponse<BinanceWeb3TokenAuditResponse>> {
    return apiGet('get_binance_web3_token_audit', { query: params })
  },

  getBinanceRwaSymbols(params: GetBinanceRwaSymbolsQueryParams = {}): Promise<AxiosResponse<BinanceRwaSymbolListResponse>> {
    return apiGet('get_binance_rwa_symbols', { query: params })
  },

  getBinanceRwaMeta(params: GetBinanceRwaMetaQueryParams): Promise<AxiosResponse<BinanceRwaMetaResponse>> {
    return apiGet('get_binance_rwa_meta', { query: params })
  },

  getBinanceRwaMarketStatus(): Promise<AxiosResponse<BinanceRwaMarketStatusResponse>> {
    return apiGet('get_binance_rwa_market_status')
  },

  getBinanceRwaAssetMarketStatus(params: GetBinanceRwaAssetMarketStatusQueryParams): Promise<AxiosResponse<BinanceRwaMarketStatusResponse>> {
    return apiGet('get_binance_rwa_asset_market_status', { query: params })
  },

  getBinanceRwaDynamic(params: GetBinanceRwaDynamicQueryParams): Promise<AxiosResponse<BinanceRwaDynamicResponse>> {
    return apiGet('get_binance_rwa_dynamic', { query: params })
  },

  getBinanceRwaKline(params: GetBinanceRwaKlineQueryParams): Promise<AxiosResponse<BinanceRwaKlineResponse>> {
    return apiGet('get_binance_rwa_kline', { query: params })
  },

}
