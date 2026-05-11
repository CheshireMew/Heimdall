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

export const marketApi = {
  getSymbols(): Promise<MarketSymbolSearchResponse[]> {
    return apiGet('list_market_symbols')
  },

  getRealtime(params: GetRealtimeAnalysisQueryParams): Promise<RealtimeResponse> {
    return apiGet('get_realtime_analysis', { query: params })
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
      timeout: params.mode === 'ai' ? 180000 : 15000,
    })
  },

  getIndicators(params: GetMarketIndicatorsQueryParams): Promise<MarketIndicatorResponse[]> {
    return apiGet('get_market_indicators', { query: params })
  },

  getDliLiquidity(params: GetDliLiquidityQueryParams): Promise<DliLiquidityResponse> {
    return apiGet('get_dli_liquidity', { query: params })
  },

  getPriceSeriesWindow(params: GetMarketHistoryQueryParams): Promise<MarketHistoryResponse> {
    return apiGet('get_market_history', { query: params })
  },

  getLatestKlines(params: GetLatestKlinesQueryParams): Promise<MarketHistoryResponse> {
    return apiGet('get_latest_klines', { query: params })
  },

  getPriceSeriesTail(params: GetKlineTailQueryParams): Promise<KlineTailResponse> {
    return apiGet('get_kline_tail', { query: params })
  },

  getCurrentPrice(params: GetCurrentPriceQueryParams): Promise<CurrentPriceResponse> {
    return apiGet('get_current_price', { query: params })
  },

  getCurrentPriceBatch(params: GetCurrentPriceBatchQueryParams): Promise<CurrentPriceBatchResponse> {
    return apiGet('get_current_price_batch', { query: params })
  },

  getPriceHistory(params: GetMarketFullHistoryQueryParams): Promise<MarketHistoryResponse> {
    return apiGet('get_market_full_history', { query: params })
  },

  getBatchPriceHistory(params: GetMarketFullHistoryBatchQueryParams): Promise<MarketHistoryBatchResponse> {
    return apiGet('get_market_full_history_batch', { query: params })
  },

  getCryptoIndex(params: GetCryptoIndexQueryParams): Promise<CryptoIndexResponse> {
    return apiGet('get_crypto_index', { query: params })
  },

  getIndexHistory(params: GetIndexHistoryQueryParams): Promise<MarketIndexHistoryResponse> {
    return apiGet('get_index_history', { query: params })
  },

  getIndexPricingHistory(params: GetIndexHistoryQueryParams): Promise<MarketIndexHistoryResponse> {
    return apiGet('get_index_pricing_history', { query: params })
  },

  getBinanceSpotTicker24h(params: GetBinanceSpotTicker24hrQueryParams = {}): Promise<BinanceTickerStatsResponse> {
    return apiGet('get_binance_spot_ticker_24hr', { query: params })
  },

  getBinanceMarketContractDetail(params: GetBinanceMarketContractDetailQueryParams): Promise<BinanceContractResearchDetailResponse> {
    return apiGet('get_binance_market_contract_detail', { query: params, timeout: 30000 })
  },

  getBinanceMarketPage(params: GetBinanceMarketPageQueryParams = {}): Promise<BinanceMarketPageResponse> {
    return apiGet('get_binance_market_page', { query: params, timeout: 30000 })
  },

  getBinanceSpotPrice(params: GetBinanceSpotPriceQueryParams = {}): Promise<BinancePriceTickerResponse> {
    return apiGet('get_binance_spot_price', { query: params })
  },

  getBinanceUsdmTicker24h(params: GetBinanceUsdmTicker24hrQueryParams = {}): Promise<BinanceTickerStatsResponse> {
    return apiGet('get_binance_usdm_ticker_24hr', { query: params })
  },

  getBinanceUsdmMarkPrice(params: GetBinanceUsdmMarkPriceQueryParams = {}): Promise<BinanceMarkPriceResponse> {
    return apiGet('get_binance_usdm_mark_price', { query: params })
  },

  getBinanceUsdmTopTraderAccounts(params: GetBinanceUsdmTopTraderAccountsQueryParams): Promise<BinanceRatioSeriesResponse> {
    return apiGet('get_binance_usdm_top_trader_accounts', { query: params })
  },

  getBinanceUsdmTopTraderPositions(params: GetBinanceUsdmTopTraderPositionsQueryParams): Promise<BinanceRatioSeriesResponse> {
    return apiGet('get_binance_usdm_top_trader_positions', { query: params })
  },

  getBinanceWeb3SocialHype(params: GetBinanceWeb3SocialHypeQueryParams): Promise<BinanceWeb3SocialHypeResponse> {
    return apiGet('get_binance_web3_social_hype', { query: params })
  },

  getBinanceWeb3UnifiedTokenRank(params: GetBinanceWeb3UnifiedTokenRankQueryParams): Promise<BinanceWeb3UnifiedTokenRankResponse> {
    return apiGet('get_binance_web3_unified_token_rank', { query: params })
  },

  getBinanceWeb3SmartMoneyInflow(params: GetBinanceWeb3SmartMoneyInflowQueryParams): Promise<BinanceWeb3SmartMoneyInflowResponse> {
    return apiGet('get_binance_web3_smart_money_inflow', { query: params })
  },

  getBinanceWeb3MemeRank(params: GetBinanceWeb3MemeRankQueryParams = {}): Promise<BinanceWeb3MemeRankResponse> {
    return apiGet('get_binance_web3_meme_rank', { query: params })
  },

  getBinanceWeb3AddressPnlRank(params: GetBinanceWeb3AddressPnlRankQueryParams): Promise<BinanceWeb3AddressPnlResponse> {
    return apiGet('get_binance_web3_address_pnl_rank', { query: params })
  },

  getBinanceWeb3HeatRank(params: GetBinanceWeb3HeatRankQueryParams = {}): Promise<BinanceWeb3HeatRankResponse> {
    return apiGet('get_binance_web3_heat_rank', { query: params, timeout: 30000 })
  },

  getBinanceWeb3HeatRankBoards(params: GetBinanceWeb3HeatRankBoardsQueryParams = {}): Promise<BinanceWeb3HeatRankBoardsResponse> {
    return apiGet('get_binance_web3_heat_rank_boards', { query: params, timeout: 30000 })
  },

  getBinanceWeb3TokenDynamic(params: GetBinanceWeb3TokenDynamicQueryParams): Promise<BinanceWeb3TokenDynamicResponse> {
    return apiGet('get_binance_web3_token_dynamic', { query: params })
  },

  getBinanceWeb3TokenKline(params: GetBinanceWeb3TokenKlineQueryParams): Promise<BinanceWeb3TokenKlineResponse> {
    return apiGet('get_binance_web3_token_kline', { query: params })
  },

  getBinanceWeb3TokenAudit(params: GetBinanceWeb3TokenAuditQueryParams): Promise<BinanceWeb3TokenAuditResponse> {
    return apiGet('get_binance_web3_token_audit', { query: params })
  },

  getBinanceRwaSymbols(params: GetBinanceRwaSymbolsQueryParams = {}): Promise<BinanceRwaSymbolListResponse> {
    return apiGet('get_binance_rwa_symbols', { query: params })
  },

  getBinanceRwaMeta(params: GetBinanceRwaMetaQueryParams): Promise<BinanceRwaMetaResponse> {
    return apiGet('get_binance_rwa_meta', { query: params })
  },

  getBinanceRwaMarketStatus(): Promise<BinanceRwaMarketStatusResponse> {
    return apiGet('get_binance_rwa_market_status')
  },

  getBinanceRwaAssetMarketStatus(params: GetBinanceRwaAssetMarketStatusQueryParams): Promise<BinanceRwaMarketStatusResponse> {
    return apiGet('get_binance_rwa_asset_market_status', { query: params })
  },

  getBinanceRwaDynamic(params: GetBinanceRwaDynamicQueryParams): Promise<BinanceRwaDynamicResponse> {
    return apiGet('get_binance_rwa_dynamic', { query: params })
  },

  getBinanceRwaKline(params: GetBinanceRwaKlineQueryParams): Promise<BinanceRwaKlineResponse> {
    return apiGet('get_binance_rwa_kline', { query: params })
  },

}


