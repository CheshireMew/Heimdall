import { apiGet } from '@/api/request'
import type {
  BinanceContractResearchDetailResponse,
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
  BinanceWeb3HeatRankBoardsResponse,
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
  DliLiquidityResponse,
  MarketIndicatorResponse,
  CryptoIndexResponse,
  MarketIndexHistoryResponse,
  MarketSymbolSearchResponse,
  GetBinanceMarketContractDetailQueryParams,
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
  GetBinanceWeb3HeatRankBoardsQueryParams,
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
  GetDliLiquidityQueryParams,
  GetMarketIndicatorsQueryParams,
  GetRealtimeAnalysisQueryParams,
  GetTradeSetupQueryParams,
} from './contracts'

const MARKET_API_TIMEOUT_MS = {
  standard: 15000,
  liveMarket: 30000,
  history: 30000,
  macroLiquidity: 60000,
  externalMarket: 30000,
  aiTradeSetup: 180000,
} as const

export const marketApi = {
  getSymbols(): Promise<MarketSymbolSearchResponse[]> {
    return apiGet('list_market_symbols')
  },

  getRealtime(params: GetRealtimeAnalysisQueryParams): Promise<RealtimeResponse> {
    return apiGet('get_realtime_analysis', { query: params, timeout: MARKET_API_TIMEOUT_MS.liveMarket })
  },

  getTradeSetup(params: GetTradeSetupQueryParams & {
    signal?: AbortSignal
  }): Promise<TradeSetupResponse> {
    const client = params.mode === 'ai' ? 'longTask' : undefined
    const { signal, ...query } = params
    return apiGet('get_trade_setup', {
      client,
      query,
      signal,
      timeout: params.mode === 'ai' ? MARKET_API_TIMEOUT_MS.aiTradeSetup : MARKET_API_TIMEOUT_MS.standard,
    })
  },

  getIndicators(params: GetMarketIndicatorsQueryParams): Promise<MarketIndicatorResponse[]> {
    return apiGet('get_market_indicators', { query: params })
  },

  getDliLiquidity(params: GetDliLiquidityQueryParams): Promise<DliLiquidityResponse> {
    return apiGet('get_dli_liquidity', { query: params, timeout: MARKET_API_TIMEOUT_MS.macroLiquidity })
  },

  getPriceSeriesWindow(params: GetMarketHistoryQueryParams): Promise<MarketHistoryResponse> {
    return apiGet('get_market_history', { query: params, timeout: MARKET_API_TIMEOUT_MS.history })
  },

  getLatestKlines(params: GetLatestKlinesQueryParams): Promise<MarketHistoryResponse> {
    return apiGet('get_latest_klines', { query: params, timeout: MARKET_API_TIMEOUT_MS.liveMarket })
  },

  getPriceSeriesTail(params: GetKlineTailQueryParams): Promise<KlineTailResponse> {
    return apiGet('get_kline_tail', { query: params, timeout: MARKET_API_TIMEOUT_MS.liveMarket })
  },

  getCurrentPrice(params: GetCurrentPriceQueryParams): Promise<CurrentPriceResponse> {
    return apiGet('get_current_price', { query: params, timeout: MARKET_API_TIMEOUT_MS.liveMarket })
  },

  getCurrentPriceBatch(params: GetCurrentPriceBatchQueryParams): Promise<CurrentPriceBatchResponse> {
    return apiGet('get_current_price_batch', { query: params, timeout: MARKET_API_TIMEOUT_MS.liveMarket })
  },

  getPriceHistory(params: GetMarketFullHistoryQueryParams): Promise<MarketHistoryResponse> {
    return apiGet('get_market_full_history', { query: params, timeout: MARKET_API_TIMEOUT_MS.history })
  },

  getBatchPriceHistory(params: GetMarketFullHistoryBatchQueryParams): Promise<MarketHistoryBatchResponse> {
    return apiGet('get_market_full_history_batch', { query: params, timeout: MARKET_API_TIMEOUT_MS.history })
  },

  getCryptoIndex(params: GetCryptoIndexQueryParams): Promise<CryptoIndexResponse> {
    return apiGet('get_crypto_index', { query: params, timeout: MARKET_API_TIMEOUT_MS.externalMarket })
  },

  getIndexHistory(params: GetIndexHistoryQueryParams): Promise<MarketIndexHistoryResponse> {
    return apiGet('get_index_history', { query: params, timeout: MARKET_API_TIMEOUT_MS.history })
  },

  getIndexPricingHistory(params: GetIndexHistoryQueryParams): Promise<MarketIndexHistoryResponse> {
    return apiGet('get_index_pricing_history', { query: params, timeout: MARKET_API_TIMEOUT_MS.history })
  },

  getBinanceSpotTicker24h(params: GetBinanceSpotTicker24hrQueryParams = {}): Promise<BinanceTickerStatsResponse> {
    return apiGet('get_binance_spot_ticker_24hr', { query: params, timeout: MARKET_API_TIMEOUT_MS.externalMarket })
  },

  getBinanceMarketContractDetail(params: GetBinanceMarketContractDetailQueryParams): Promise<BinanceContractResearchDetailResponse> {
    return apiGet('get_binance_market_contract_detail', { query: params, timeout: MARKET_API_TIMEOUT_MS.externalMarket })
  },

  getBinanceMarketPage(params: GetBinanceMarketPageQueryParams = {}): Promise<BinanceMarketPageResponse> {
    return apiGet('get_binance_market_page', { query: params, timeout: MARKET_API_TIMEOUT_MS.externalMarket })
  },

  getBinanceSpotPrice(params: GetBinanceSpotPriceQueryParams = {}): Promise<BinancePriceTickerResponse> {
    return apiGet('get_binance_spot_price', { query: params, timeout: MARKET_API_TIMEOUT_MS.externalMarket })
  },

  getBinanceUsdmTicker24h(params: GetBinanceUsdmTicker24hrQueryParams = {}): Promise<BinanceTickerStatsResponse> {
    return apiGet('get_binance_usdm_ticker_24hr', { query: params, timeout: MARKET_API_TIMEOUT_MS.externalMarket })
  },

  getBinanceUsdmMarkPrice(params: GetBinanceUsdmMarkPriceQueryParams = {}): Promise<BinanceMarkPriceResponse> {
    return apiGet('get_binance_usdm_mark_price', { query: params, timeout: MARKET_API_TIMEOUT_MS.externalMarket })
  },

  getBinanceUsdmTopTraderAccounts(params: GetBinanceUsdmTopTraderAccountsQueryParams): Promise<BinanceRatioSeriesResponse> {
    return apiGet('get_binance_usdm_top_trader_accounts', { query: params, timeout: MARKET_API_TIMEOUT_MS.externalMarket })
  },

  getBinanceUsdmTopTraderPositions(params: GetBinanceUsdmTopTraderPositionsQueryParams): Promise<BinanceRatioSeriesResponse> {
    return apiGet('get_binance_usdm_top_trader_positions', { query: params, timeout: MARKET_API_TIMEOUT_MS.externalMarket })
  },

  getBinanceWeb3SocialHype(params: GetBinanceWeb3SocialHypeQueryParams): Promise<BinanceWeb3SocialHypeResponse> {
    return apiGet('get_binance_web3_social_hype', { query: params, timeout: MARKET_API_TIMEOUT_MS.externalMarket })
  },

  getBinanceWeb3UnifiedTokenRank(params: GetBinanceWeb3UnifiedTokenRankQueryParams): Promise<BinanceWeb3UnifiedTokenRankResponse> {
    return apiGet('get_binance_web3_unified_token_rank', { query: params, timeout: MARKET_API_TIMEOUT_MS.externalMarket })
  },

  getBinanceWeb3SmartMoneyInflow(params: GetBinanceWeb3SmartMoneyInflowQueryParams): Promise<BinanceWeb3SmartMoneyInflowResponse> {
    return apiGet('get_binance_web3_smart_money_inflow', { query: params, timeout: MARKET_API_TIMEOUT_MS.externalMarket })
  },

  getBinanceWeb3MemeRank(params: GetBinanceWeb3MemeRankQueryParams = {}): Promise<BinanceWeb3MemeRankResponse> {
    return apiGet('get_binance_web3_meme_rank', { query: params, timeout: MARKET_API_TIMEOUT_MS.externalMarket })
  },

  getBinanceWeb3AddressPnlRank(params: GetBinanceWeb3AddressPnlRankQueryParams): Promise<BinanceWeb3AddressPnlResponse> {
    return apiGet('get_binance_web3_address_pnl_rank', { query: params, timeout: MARKET_API_TIMEOUT_MS.externalMarket })
  },

  getBinanceWeb3HeatRank(params: GetBinanceWeb3HeatRankQueryParams = {}): Promise<BinanceWeb3HeatRankResponse> {
    return apiGet('get_binance_web3_heat_rank', { query: params, timeout: MARKET_API_TIMEOUT_MS.externalMarket })
  },

  getBinanceWeb3HeatRankBoards(params: GetBinanceWeb3HeatRankBoardsQueryParams = {}): Promise<BinanceWeb3HeatRankBoardsResponse> {
    return apiGet('get_binance_web3_heat_rank_boards', { query: params, timeout: MARKET_API_TIMEOUT_MS.externalMarket })
  },

  getBinanceWeb3TokenDynamic(params: GetBinanceWeb3TokenDynamicQueryParams): Promise<BinanceWeb3TokenDynamicResponse> {
    return apiGet('get_binance_web3_token_dynamic', { query: params, timeout: MARKET_API_TIMEOUT_MS.externalMarket })
  },

  getBinanceWeb3TokenKline(params: GetBinanceWeb3TokenKlineQueryParams): Promise<BinanceWeb3TokenKlineResponse> {
    return apiGet('get_binance_web3_token_kline', { query: params, timeout: MARKET_API_TIMEOUT_MS.externalMarket })
  },

  getBinanceWeb3TokenAudit(params: GetBinanceWeb3TokenAuditQueryParams): Promise<BinanceWeb3TokenAuditResponse> {
    return apiGet('get_binance_web3_token_audit', { query: params, timeout: MARKET_API_TIMEOUT_MS.externalMarket })
  },

  getBinanceRwaSymbols(params: GetBinanceRwaSymbolsQueryParams = {}): Promise<BinanceRwaSymbolListResponse> {
    return apiGet('get_binance_rwa_symbols', { query: params, timeout: MARKET_API_TIMEOUT_MS.externalMarket })
  },

  getBinanceRwaMeta(params: GetBinanceRwaMetaQueryParams): Promise<BinanceRwaMetaResponse> {
    return apiGet('get_binance_rwa_meta', { query: params, timeout: MARKET_API_TIMEOUT_MS.externalMarket })
  },

  getBinanceRwaMarketStatus(): Promise<BinanceRwaMarketStatusResponse> {
    return apiGet('get_binance_rwa_market_status', { timeout: MARKET_API_TIMEOUT_MS.externalMarket })
  },

  getBinanceRwaAssetMarketStatus(params: GetBinanceRwaAssetMarketStatusQueryParams): Promise<BinanceRwaMarketStatusResponse> {
    return apiGet('get_binance_rwa_asset_market_status', { query: params, timeout: MARKET_API_TIMEOUT_MS.externalMarket })
  },

  getBinanceRwaDynamic(params: GetBinanceRwaDynamicQueryParams): Promise<BinanceRwaDynamicResponse> {
    return apiGet('get_binance_rwa_dynamic', { query: params, timeout: MARKET_API_TIMEOUT_MS.externalMarket })
  },

  getBinanceRwaKline(params: GetBinanceRwaKlineQueryParams): Promise<BinanceRwaKlineResponse> {
    return apiGet('get_binance_rwa_kline', { query: params, timeout: MARKET_API_TIMEOUT_MS.externalMarket })
  },

}


