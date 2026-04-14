import request from '@/api/request'
import type { AxiosResponse } from 'axios'
import type {
  BinanceExchangeInfoResponse,
  BinanceMarkPriceResponse,
  BinancePriceTickerResponse,
  BinanceRatioSeriesResponse,
  BinanceReservedFeatureResponse,
  BinanceRwaDynamicResponse,
  BinanceRwaKlineResponse,
  BinanceRwaMarketStatusResponse,
  BinanceRwaMetaResponse,
  BinanceRwaSymbolListResponse,
  BinanceTickerStatsResponse,
  BinanceWeb3AddressPnlResponse,
  BinanceWeb3MemeRankResponse,
  BinanceWeb3SmartMoneyInflowResponse,
  BinanceWeb3SocialHypeResponse,
  BinanceWeb3UnifiedTokenRankResponse,
  RealtimeParams,
  RealtimeResponse,
  TradeSetupResponse,
  HistoryParams,
  LatestKlineParams,
  FullHistoryParams,
  BatchFullHistoryParams,
  BatchFullHistoryResponse,
  IndicatorParams,
  IndicatorItem,
  OHLCVRaw,
  CryptoIndexParams,
  CryptoIndexResponse,
  IndexHistoryParams,
  MarketIndexHistoryResponse,
  MarketSymbolSearchItem,
} from '@/types'

const serializeBatchFullHistoryParams = (params: BatchFullHistoryParams) => {
  const query = new URLSearchParams()
  params.symbols.forEach((symbol) => {
    query.append('symbols', symbol)
  })
  if (params.timeframe) query.set('timeframe', params.timeframe)
  if (params.start_date) query.set('start_date', params.start_date)
  return query.toString()
}

const HISTORY_RESPONSE_CACHE_LIMIT = 120
const historyResponseCache = new Map<string, Promise<AxiosResponse<any>>>()

const rememberHistoryResponse = <T>(key: string, loader: () => Promise<AxiosResponse<T>>): Promise<AxiosResponse<T>> => {
  let promise = historyResponseCache.get(key) as Promise<AxiosResponse<T>> | undefined
  if (!promise) {
    promise = loader()
    historyResponseCache.set(key, promise)
    promise.catch(() => {
      if (historyResponseCache.get(key) === promise) historyResponseCache.delete(key)
    })
    if (historyResponseCache.size > HISTORY_RESPONSE_CACHE_LIMIT) {
      const oldestKey = historyResponseCache.keys().next().value
      if (oldestKey) historyResponseCache.delete(oldestKey)
    }
  }
  return promise
}

const historyKey = (scope: string, params: Record<string, unknown>) => {
  const query = new URLSearchParams()
  Object.entries(params)
    .sort(([left], [right]) => left.localeCompare(right))
    .forEach(([key, value]) => {
      if (value === null || value === undefined || value === '') return
      if (Array.isArray(value)) {
        value.slice().sort().forEach((item) => query.append(key, String(item)))
        return
      }
      query.set(key, String(value))
    })
  return `${scope}:${query.toString()}`
}

const serializeArrayParams = (params: Record<string, unknown>) => {
  const query = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value === null || value === undefined || value === '') return
    if (Array.isArray(value)) {
      value.forEach((item) => {
        if (item !== null && item !== undefined && item !== '') query.append(key, String(item))
      })
      return
    }
    query.set(key, String(value))
  })
  return query.toString()
}

export const marketApi = {
  getSymbols(): Promise<AxiosResponse<MarketSymbolSearchItem[]>> {
    return request.get('/symbols')
  },

  getRealtime(params: RealtimeParams): Promise<AxiosResponse<RealtimeResponse>> {
    return request.get('/realtime', { params })
  },

  getTradeSetup(params: {
    symbol: string
    timeframe?: string
    limit?: number
    account_size?: number
    style?: string
    strategy?: string
    mode?: string
  }): Promise<AxiosResponse<TradeSetupResponse>> {
    return request.get('/trade-setup', { params })
  },

  getIndicators(params: IndicatorParams): Promise<AxiosResponse<IndicatorItem[]>> {
    return request.get('/indicators', { params })
  },

  getHistory(params: HistoryParams): Promise<AxiosResponse<OHLCVRaw[]>> {
    return request.get('/history', { params })
  },

  getLatestKlines(params: LatestKlineParams): Promise<AxiosResponse<OHLCVRaw[]>> {
    return request.get('/klines/latest', { params })
  },

  getFullHistory(params: FullHistoryParams): Promise<AxiosResponse<OHLCVRaw[]>> {
    return rememberHistoryResponse(
      historyKey('full_history', params as Record<string, unknown>),
      () => request.get('/full_history', { params }),
    )
  },

  getBatchFullHistory(params: BatchFullHistoryParams): Promise<AxiosResponse<BatchFullHistoryResponse>> {
    return rememberHistoryResponse(
      historyKey('full_history_batch', { ...params, symbols: params.symbols }),
      () => request.get('/full_history/batch', {
        params,
        paramsSerializer: () => serializeBatchFullHistoryParams(params),
      }),
    )
  },

  getCryptoIndex(params: CryptoIndexParams): Promise<AxiosResponse<CryptoIndexResponse>> {
    return request.get('/crypto_index', { params })
  },

  getIndexHistory(params: IndexHistoryParams): Promise<AxiosResponse<MarketIndexHistoryResponse>> {
    return rememberHistoryResponse(
      historyKey('indexes_history', params as Record<string, unknown>),
      () => request.get('/indexes/history', { params }),
    )
  },

  getIndexPricingHistory(params: IndexHistoryParams): Promise<AxiosResponse<MarketIndexHistoryResponse>> {
    return rememberHistoryResponse(
      historyKey('indexes_pricing_history', params as Record<string, unknown>),
      () => request.get('/indexes/pricing/history', { params }),
    )
  },

  getBinanceSpotTicker24h(params = {}): Promise<AxiosResponse<BinanceTickerStatsResponse>> {
    return request.get('/binance/spot/ticker_24hr', { params, paramsSerializer: () => serializeArrayParams(params) })
  },

  getBinanceSpotPrice(params = {}): Promise<AxiosResponse<BinancePriceTickerResponse>> {
    return request.get('/binance/spot/price', { params, paramsSerializer: () => serializeArrayParams(params) })
  },

  getBinanceUsdmTicker24h(params = {}): Promise<AxiosResponse<BinanceTickerStatsResponse>> {
    return request.get('/binance/futures/usdm/ticker_24hr', { params })
  },

  getBinanceUsdmMarkPrice(params = {}): Promise<AxiosResponse<BinanceMarkPriceResponse>> {
    return request.get('/binance/futures/usdm/mark_price', { params })
  },

  getBinanceCoinmTicker24h(params = {}): Promise<AxiosResponse<BinanceTickerStatsResponse>> {
    return request.get('/binance/futures/coinm/ticker_24hr', { params })
  },

  getBinanceCoinmMarkPrice(params = {}): Promise<AxiosResponse<BinanceMarkPriceResponse>> {
    return request.get('/binance/futures/coinm/mark_price', { params })
  },

  getBinanceUsdmTopTraderAccounts(params: { symbol: string; period: string; limit?: number }): Promise<AxiosResponse<BinanceRatioSeriesResponse>> {
    return request.get('/binance/futures/usdm/top_trader_accounts', { params })
  },

  getBinanceUsdmTopTraderPositions(params: { symbol: string; period: string; limit?: number }): Promise<AxiosResponse<BinanceRatioSeriesResponse>> {
    return request.get('/binance/futures/usdm/top_trader_positions', { params })
  },

  getBinanceCoinmTopTraderAccounts(params: { symbol: string; period: string; limit?: number }): Promise<AxiosResponse<BinanceRatioSeriesResponse>> {
    return request.get('/binance/futures/coinm/top_trader_accounts', { params })
  },

  getBinanceCoinmTopTraderPositions(params: { pair: string; period: string; limit?: number }): Promise<AxiosResponse<BinanceRatioSeriesResponse>> {
    return request.get('/binance/futures/coinm/top_trader_positions', { params })
  },

  getBinanceWeb3SocialHype(params: { chain_id: string; target_language?: string; time_range?: number; sentiment?: string; social_language?: string }): Promise<AxiosResponse<BinanceWeb3SocialHypeResponse>> {
    return request.get('/binance/web3/social_hype', { params })
  },

  getBinanceWeb3UnifiedTokenRank(params: { rank_type?: number; chain_id?: string; period?: number; sort_by?: number; order_asc?: boolean; page?: number; size?: number }): Promise<AxiosResponse<BinanceWeb3UnifiedTokenRankResponse>> {
    return request.get('/binance/web3/unified_token_rank', { params })
  },

  getBinanceWeb3SmartMoneyInflow(params: { chain_id: string; period?: string; tag_type?: number }): Promise<AxiosResponse<BinanceWeb3SmartMoneyInflowResponse>> {
    return request.get('/binance/web3/smart_money_inflow', { params })
  },

  getBinanceWeb3MemeRank(params: { chain_id?: string } = {}): Promise<AxiosResponse<BinanceWeb3MemeRankResponse>> {
    return request.get('/binance/web3/meme_rank', { params })
  },

  getBinanceWeb3AddressPnlRank(params: { chain_id: string; period?: string; tag?: string; page_no?: number; page_size?: number }): Promise<AxiosResponse<BinanceWeb3AddressPnlResponse>> {
    return request.get('/binance/web3/address_pnl_rank', { params })
  },

  getBinanceRwaSymbols(params: { platform_type?: number | null } = {}): Promise<AxiosResponse<BinanceRwaSymbolListResponse>> {
    return request.get('/binance/rwa/symbols', { params })
  },

  getBinanceRwaMeta(params: { chain_id: string; contract_address: string }): Promise<AxiosResponse<BinanceRwaMetaResponse>> {
    return request.get('/binance/rwa/meta', { params })
  },

  getBinanceRwaMarketStatus(): Promise<AxiosResponse<BinanceRwaMarketStatusResponse>> {
    return request.get('/binance/rwa/market_status')
  },

  getBinanceRwaAssetMarketStatus(params: { chain_id: string; contract_address: string }): Promise<AxiosResponse<BinanceRwaMarketStatusResponse>> {
    return request.get('/binance/rwa/asset_market_status', { params })
  },

  getBinanceRwaDynamic(params: { chain_id: string; contract_address: string }): Promise<AxiosResponse<BinanceRwaDynamicResponse>> {
    return request.get('/binance/rwa/dynamic', { params })
  },

  getBinanceRwaKline(params: { chain_id: string; contract_address: string; interval?: string; limit?: number }): Promise<AxiosResponse<BinanceRwaKlineResponse>> {
    return request.get('/binance/rwa/kline', { params })
  },

  getReservedBinanceTokenInfoSearch(params: { keyword?: string; chainIds?: string; orderBy?: string } = {}): Promise<AxiosResponse<BinanceReservedFeatureResponse>> {
    return request.get('/binance/web3/token_info/search', { params })
  },

  getReservedBinanceTokenInfoMetadata(params: { chainId?: string; contractAddress?: string } = {}): Promise<AxiosResponse<BinanceReservedFeatureResponse>> {
    return request.get('/binance/web3/token_info/metadata', { params })
  },

  getReservedBinanceTokenInfoDynamic(params: { chainId?: string; contractAddress?: string } = {}): Promise<AxiosResponse<BinanceReservedFeatureResponse>> {
    return request.get('/binance/web3/token_info/dynamic', { params })
  },

  getReservedBinanceTokenInfoKline(params: { address?: string; platform?: string; interval?: string; limit?: number; from?: number; to?: number; pm?: string } = {}): Promise<AxiosResponse<BinanceReservedFeatureResponse>> {
    return request.get('/binance/web3/token_info/kline', { params })
  },

  getReservedBinanceTokenAudit(params: { binanceChainId?: string; contractAddress?: string } = {}): Promise<AxiosResponse<BinanceReservedFeatureResponse>> {
    return request.get('/binance/web3/token_audit', { params })
  },
}
