import request, { longTaskRequest } from '@/api/request'
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

const serializeBatchFullHistoryParams = (params: BatchFullHistoryParams) => {
  const query = new URLSearchParams()
  params.symbols.forEach((symbol) => {
    query.append('symbols', symbol)
  })
  if (params.timeframe) query.set('timeframe', params.timeframe)
  if (params.start_date) query.set('start_date', params.start_date)
  if (params.fetch_policy) query.set('fetch_policy', params.fetch_policy)
  return query.toString()
}

const normalizePriceHistoryParams = <T extends FullHistoryParams | BatchFullHistoryParams>(params: T): T => ({
  ...params,
  fetch_policy: params.fetch_policy ?? 'hydrate',
})

const HISTORY_RESPONSE_CACHE_LIMIT = 120
const HISTORY_CACHE_TTL_MS = 30_000
type CacheableHistoryPayload = MarketHistoryResponse | MarketHistoryBatchResponse | MarketIndexHistoryResponse
const historyResponseCache = new Map<string, {
  createdAt: number
  promise: Promise<AxiosResponse<CacheableHistoryPayload>>
}>()

const rememberHistoryResponse = <T extends CacheableHistoryPayload>(key: string, loader: () => Promise<AxiosResponse<T>>): Promise<AxiosResponse<T>> => {
  const now = Date.now()
  const cached = historyResponseCache.get(key) as { createdAt: number; promise: Promise<AxiosResponse<T>> } | undefined
  if (cached && now - cached.createdAt < HISTORY_CACHE_TTL_MS) {
    return cached.promise
  }

  const promise = loader()
  historyResponseCache.set(key, {
    createdAt: now,
    promise,
  })
  promise.catch(() => {
    const current = historyResponseCache.get(key)
    if (current?.promise === promise) historyResponseCache.delete(key)
  })
  if (historyResponseCache.size > HISTORY_RESPONSE_CACHE_LIMIT) {
    const oldestKey = historyResponseCache.keys().next().value
    if (oldestKey) historyResponseCache.delete(oldestKey)
  }
  return promise
}

const loadHistoryResponse = <T extends CacheableHistoryPayload>(
  key: string,
  loader: () => Promise<AxiosResponse<T>>,
  useCache: boolean,
): Promise<AxiosResponse<T>> => {
  if (!useCache) {
    return loader().catch((error) => {
      historyResponseCache.delete(key)
      throw error
    })
  }
  return rememberHistoryResponse(key, loader)
}

const historyKey = (scope: string, params: object) => {
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
  getSymbols(): Promise<AxiosResponse<MarketSymbolSearchResponse[]>> {
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
    signal?: AbortSignal
  }): Promise<AxiosResponse<TradeSetupResponse>> {
    const client = params.mode === 'ai' ? longTaskRequest : request
    const { signal, ...query } = params
    return client.get('/trade-setup', {
      params: query,
      signal,
      timeout: params.mode === 'ai' ? 180000 : 15000,
    })
  },

  getIndicators(params: IndicatorParams): Promise<AxiosResponse<MarketIndicatorResponse[]>> {
    return request.get('/indicators', { params })
  },

  getPriceSeriesWindow(params: HistoryParams): Promise<AxiosResponse<MarketHistoryResponse>> {
    return request.get('/history', { params })
  },

  getLatestKlines(params: LatestKlineParams): Promise<AxiosResponse<MarketHistoryResponse>> {
    return request.get('/klines/latest', { params })
  },

  getPriceSeriesTail(params: TailKlineParams): Promise<AxiosResponse<KlineTailResponse>> {
    return request.get('/klines/tail', { params })
  },

  getCurrentPrice(params: CurrentPriceParams): Promise<AxiosResponse<CurrentPriceResponse>> {
    return request.get('/price/current', { params })
  },

  getCurrentPriceBatch(params: { symbols: string[]; timeframe?: string }): Promise<AxiosResponse<CurrentPriceBatchResponse>> {
    return request.get('/price/current/batch', {
      params,
      paramsSerializer: () => serializeArrayParams(params),
    })
  },

  getPriceHistory(params: FullHistoryParams): Promise<AxiosResponse<MarketHistoryResponse>> {
    const query = normalizePriceHistoryParams(params)
    const key = historyKey('full_history', query)
    return loadHistoryResponse(
      key,
      () => request.get('/full_history', { params: query }),
      query.fetch_policy === 'cache_only',
    )
  },

  getBatchPriceHistory(params: BatchFullHistoryParams): Promise<AxiosResponse<MarketHistoryBatchResponse>> {
    const query = normalizePriceHistoryParams(params)
    const key = historyKey('full_history_batch', { ...query, symbols: query.symbols })
    return loadHistoryResponse(
      key,
      () => request.get('/full_history/batch', {
        params: query,
        paramsSerializer: () => serializeBatchFullHistoryParams(query),
      }),
      query.fetch_policy === 'cache_only',
    )
  },

  getCryptoIndex(params: CryptoIndexParams): Promise<AxiosResponse<CryptoIndexResponse>> {
    return request.get('/crypto_index', { params })
  },

  getIndexHistory(params: IndexHistoryParams): Promise<AxiosResponse<MarketIndexHistoryResponse>> {
    const key = historyKey('indexes_history', params)
    return loadHistoryResponse(
      key,
      () => request.get('/indexes/history', { params }),
      true,
    )
  },

  getIndexPricingHistory(params: IndexHistoryParams): Promise<AxiosResponse<MarketIndexHistoryResponse>> {
    const key = historyKey('indexes_pricing_history', params)
    return loadHistoryResponse(
      key,
      () => request.get('/indexes/pricing/history', { params }),
      true,
    )
  },

  getBinanceSpotTicker24h(params = {}): Promise<AxiosResponse<BinanceTickerStatsResponse>> {
    return request.get('/binance/spot/ticker_24hr', { params, paramsSerializer: () => serializeArrayParams(params) })
  },

  getBinanceBreakoutMonitor(params: { min_rise_pct?: number; limit?: number; quote_asset?: string } = {}): Promise<AxiosResponse<BinanceBreakoutMonitorResponse>> {
    return request.get('/binance/market/breakout_monitor', { params })
  },

  getBinanceMarketPage(params: { min_rise_pct?: number; limit?: number; quote_asset?: string } = {}): Promise<AxiosResponse<BinanceMarketPageResponse>> {
    return request.get('/binance/market/page', { params, timeout: 30000 })
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

  getBinanceUsdmTopTraderAccounts(params: { symbol: string; period: string; limit?: number }): Promise<AxiosResponse<BinanceRatioSeriesResponse>> {
    return request.get('/binance/futures/usdm/top_trader_accounts', { params })
  },

  getBinanceUsdmTopTraderPositions(params: { symbol: string; period: string; limit?: number }): Promise<AxiosResponse<BinanceRatioSeriesResponse>> {
    return request.get('/binance/futures/usdm/top_trader_positions', { params })
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

  getBinanceWeb3HeatRank(params: { chain_id?: string; size?: number } = {}): Promise<AxiosResponse<BinanceWeb3HeatRankResponse>> {
    return request.get('/binance/web3/heat_rank', { params, timeout: 30000 })
  },

  getBinanceWeb3TokenDynamic(params: { chain_id: string; contract_address: string }): Promise<AxiosResponse<BinanceWeb3TokenDynamicResponse>> {
    return request.get('/binance/web3/token_dynamic', { params })
  },

  getBinanceWeb3TokenKline(params: { address: string; platform: string; interval?: string; limit?: number; from?: number; to?: number; pm?: string }): Promise<AxiosResponse<BinanceWeb3TokenKlineResponse>> {
    return request.get('/binance/web3/token_kline', { params })
  },

  getBinanceWeb3TokenAudit(params: { binance_chain_id: string; contract_address: string }): Promise<AxiosResponse<BinanceWeb3TokenAuditResponse>> {
    return request.get('/binance/web3/token_audit', { params })
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

}
