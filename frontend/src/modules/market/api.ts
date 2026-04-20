import request, { longTaskRequest } from '@/api/request'
import { API_QUERY_META, apiRoute, serializeApiQueryParams } from '@/api/routes'
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
} from './contracts'
import type {
  BatchFullHistoryParams,
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
  GetCurrentPriceBatchQueryParams,
  GetTradeSetupQueryParams,
  CryptoIndexParams,
  CurrentPriceParams,
  FullHistoryParams,
  HistoryParams,
  IndexHistoryParams,
  IndicatorParams,
  LatestKlineParams,
  RealtimeParams,
  TailKlineParams,
} from './contracts'
export const marketApi = {
  getSymbols(): Promise<AxiosResponse<MarketSymbolSearchResponse[]>> {
    return request.get(apiRoute('list_market_symbols'))
  },

  getRealtime(params: RealtimeParams): Promise<AxiosResponse<RealtimeResponse>> {
    return request.get(apiRoute('get_realtime_analysis'), { params })
  },

  getTradeSetup(params: GetTradeSetupQueryParams & {
    signal?: AbortSignal
  }): Promise<AxiosResponse<TradeSetupResponse>> {
    const client = params.mode === 'ai' ? longTaskRequest : request
    const { signal, ...query } = params
    return client.get(apiRoute('get_trade_setup'), {
      params: query,
      signal,
      timeout: params.mode === 'ai' ? 180000 : 15000,
    })
  },

  getIndicators(params: IndicatorParams): Promise<AxiosResponse<MarketIndicatorResponse[]>> {
    return request.get(apiRoute('get_market_indicators'), { params })
  },

  getPriceSeriesWindow(params: HistoryParams): Promise<AxiosResponse<MarketHistoryResponse>> {
    return request.get(apiRoute('get_market_history'), { params })
  },

  getLatestKlines(params: LatestKlineParams): Promise<AxiosResponse<MarketHistoryResponse>> {
    return request.get(apiRoute('get_latest_klines'), { params })
  },

  getPriceSeriesTail(params: TailKlineParams): Promise<AxiosResponse<KlineTailResponse>> {
    return request.get(apiRoute('get_kline_tail'), { params })
  },

  getCurrentPrice(params: CurrentPriceParams): Promise<AxiosResponse<CurrentPriceResponse>> {
    return request.get(apiRoute('get_current_price'), { params })
  },

  getCurrentPriceBatch(params: GetCurrentPriceBatchQueryParams): Promise<AxiosResponse<CurrentPriceBatchResponse>> {
    return request.get(apiRoute('get_current_price_batch'), {
      params,
      paramsSerializer: () => serializeApiQueryParams(params, API_QUERY_META.get_current_price_batch),
    })
  },

  getPriceHistory(params: FullHistoryParams): Promise<AxiosResponse<MarketHistoryResponse>> {
    return request.get(apiRoute('get_market_full_history'), { params })
  },

  getBatchPriceHistory(params: BatchFullHistoryParams): Promise<AxiosResponse<MarketHistoryBatchResponse>> {
    return request.get(apiRoute('get_market_full_history_batch'), {
      params,
      paramsSerializer: () => serializeApiQueryParams(params, API_QUERY_META.get_market_full_history_batch),
    })
  },

  getCryptoIndex(params: CryptoIndexParams): Promise<AxiosResponse<CryptoIndexResponse>> {
    return request.get(apiRoute('get_crypto_index'), { params })
  },

  getIndexHistory(params: IndexHistoryParams): Promise<AxiosResponse<MarketIndexHistoryResponse>> {
    return request.get(apiRoute('get_index_history'), { params })
  },

  getIndexPricingHistory(params: IndexHistoryParams): Promise<AxiosResponse<MarketIndexHistoryResponse>> {
    return request.get(apiRoute('get_index_pricing_history'), { params })
  },

  getBinanceSpotTicker24h(params: GetBinanceSpotTicker24hrQueryParams = {}): Promise<AxiosResponse<BinanceTickerStatsResponse>> {
    return request.get(apiRoute('get_binance_spot_ticker_24hr'), { params, paramsSerializer: () => serializeApiQueryParams(params, API_QUERY_META.get_binance_spot_ticker_24hr) })
  },

  getBinanceBreakoutMonitor(params: GetBinanceMarketBreakoutMonitorQueryParams = {}): Promise<AxiosResponse<BinanceBreakoutMonitorResponse>> {
    return request.get(apiRoute('get_binance_market_breakout_monitor'), { params })
  },

  getBinanceMarketPage(params: GetBinanceMarketPageQueryParams = {}): Promise<AxiosResponse<BinanceMarketPageResponse>> {
    return request.get(apiRoute('get_binance_market_page'), { params, timeout: 30000 })
  },

  getBinanceSpotPrice(params: GetBinanceSpotPriceQueryParams = {}): Promise<AxiosResponse<BinancePriceTickerResponse>> {
    return request.get(apiRoute('get_binance_spot_price'), { params, paramsSerializer: () => serializeApiQueryParams(params, API_QUERY_META.get_binance_spot_price) })
  },

  getBinanceUsdmTicker24h(params: GetBinanceUsdmTicker24hrQueryParams = {}): Promise<AxiosResponse<BinanceTickerStatsResponse>> {
    return request.get(apiRoute('get_binance_usdm_ticker_24hr'), { params })
  },

  getBinanceUsdmMarkPrice(params: GetBinanceUsdmMarkPriceQueryParams = {}): Promise<AxiosResponse<BinanceMarkPriceResponse>> {
    return request.get(apiRoute('get_binance_usdm_mark_price'), { params })
  },

  getBinanceUsdmTopTraderAccounts(params: GetBinanceUsdmTopTraderAccountsQueryParams): Promise<AxiosResponse<BinanceRatioSeriesResponse>> {
    return request.get(apiRoute('get_binance_usdm_top_trader_accounts'), { params })
  },

  getBinanceUsdmTopTraderPositions(params: GetBinanceUsdmTopTraderPositionsQueryParams): Promise<AxiosResponse<BinanceRatioSeriesResponse>> {
    return request.get(apiRoute('get_binance_usdm_top_trader_positions'), { params })
  },

  getBinanceWeb3SocialHype(params: GetBinanceWeb3SocialHypeQueryParams): Promise<AxiosResponse<BinanceWeb3SocialHypeResponse>> {
    return request.get(apiRoute('get_binance_web3_social_hype'), { params })
  },

  getBinanceWeb3UnifiedTokenRank(params: GetBinanceWeb3UnifiedTokenRankQueryParams): Promise<AxiosResponse<BinanceWeb3UnifiedTokenRankResponse>> {
    return request.get(apiRoute('get_binance_web3_unified_token_rank'), { params })
  },

  getBinanceWeb3SmartMoneyInflow(params: GetBinanceWeb3SmartMoneyInflowQueryParams): Promise<AxiosResponse<BinanceWeb3SmartMoneyInflowResponse>> {
    return request.get(apiRoute('get_binance_web3_smart_money_inflow'), { params })
  },

  getBinanceWeb3MemeRank(params: GetBinanceWeb3MemeRankQueryParams = {}): Promise<AxiosResponse<BinanceWeb3MemeRankResponse>> {
    return request.get(apiRoute('get_binance_web3_meme_rank'), { params })
  },

  getBinanceWeb3AddressPnlRank(params: GetBinanceWeb3AddressPnlRankQueryParams): Promise<AxiosResponse<BinanceWeb3AddressPnlResponse>> {
    return request.get(apiRoute('get_binance_web3_address_pnl_rank'), { params })
  },

  getBinanceWeb3HeatRank(params: GetBinanceWeb3HeatRankQueryParams = {}): Promise<AxiosResponse<BinanceWeb3HeatRankResponse>> {
    return request.get(apiRoute('get_binance_web3_heat_rank'), { params, timeout: 30000 })
  },

  getBinanceWeb3TokenDynamic(params: GetBinanceWeb3TokenDynamicQueryParams): Promise<AxiosResponse<BinanceWeb3TokenDynamicResponse>> {
    return request.get(apiRoute('get_binance_web3_token_dynamic'), { params })
  },

  getBinanceWeb3TokenKline(params: GetBinanceWeb3TokenKlineQueryParams): Promise<AxiosResponse<BinanceWeb3TokenKlineResponse>> {
    return request.get(apiRoute('get_binance_web3_token_kline'), {
      params,
      paramsSerializer: () => serializeApiQueryParams(params, API_QUERY_META.get_binance_web3_token_kline),
    })
  },

  getBinanceWeb3TokenAudit(params: GetBinanceWeb3TokenAuditQueryParams): Promise<AxiosResponse<BinanceWeb3TokenAuditResponse>> {
    return request.get(apiRoute('get_binance_web3_token_audit'), { params })
  },

  getBinanceRwaSymbols(params: GetBinanceRwaSymbolsQueryParams = {}): Promise<AxiosResponse<BinanceRwaSymbolListResponse>> {
    return request.get(apiRoute('get_binance_rwa_symbols'), { params })
  },

  getBinanceRwaMeta(params: GetBinanceRwaMetaQueryParams): Promise<AxiosResponse<BinanceRwaMetaResponse>> {
    return request.get(apiRoute('get_binance_rwa_meta'), { params })
  },

  getBinanceRwaMarketStatus(): Promise<AxiosResponse<BinanceRwaMarketStatusResponse>> {
    return request.get(apiRoute('get_binance_rwa_market_status'))
  },

  getBinanceRwaAssetMarketStatus(params: GetBinanceRwaAssetMarketStatusQueryParams): Promise<AxiosResponse<BinanceRwaMarketStatusResponse>> {
    return request.get(apiRoute('get_binance_rwa_asset_market_status'), { params })
  },

  getBinanceRwaDynamic(params: GetBinanceRwaDynamicQueryParams): Promise<AxiosResponse<BinanceRwaDynamicResponse>> {
    return request.get(apiRoute('get_binance_rwa_dynamic'), { params })
  },

  getBinanceRwaKline(params: GetBinanceRwaKlineQueryParams): Promise<AxiosResponse<BinanceRwaKlineResponse>> {
    return request.get(apiRoute('get_binance_rwa_kline'), { params })
  },

}
