import { defineStore } from 'pinia'
import { marketApi } from './api'
import { resolveSentimentBucket } from './sentiment'
import type {
  CryptoIndexResponse,
  DliLiquidityResponse,
  MarketHistoryResponse,
  MarketIndicatorResponse,
  OhlcvPointResponse,
} from './contracts'
import type { KlineCacheEntry, SentimentCache, SentimentData } from './contracts'

interface CacheEntry<TData> {
  data: TData
  timestamp: number
}

interface DliLiquidityCacheEntry {
  data: DliLiquidityResponse
  timestamp: number
}

interface MarketState {
  klineCache: Record<string, KlineCacheEntry>
  sentimentCache: SentimentCache
  indicatorCache: Record<string, CacheEntry<MarketIndicatorResponse[]>>
  indicatorLoading: Record<string, boolean>
  indicatorErrors: Record<string, string>
  dliLiquidityCache: Record<string, DliLiquidityCacheEntry>
  dliLiquidityLoading: Record<string, boolean>
  dliLiquidityErrors: Record<string, string>
  cryptoIndexCache: Record<string, CacheEntry<CryptoIndexResponse>>
  cryptoIndexLoading: Record<string, boolean>
  cryptoIndexErrors: Record<string, string>
  priceHistoryCache: Record<string, CacheEntry<MarketHistoryResponse>>
  priceHistoryLoading: Record<string, boolean>
  priceHistoryErrors: Record<string, string>
}

const klineFetchPromises = new Map<string, Promise<OhlcvPointResponse[] | null>>()
const indicatorFetchPromises = new Map<string, Promise<MarketIndicatorResponse[] | null>>()
const dliLiquidityFetchPromises = new Map<string, Promise<DliLiquidityResponse | null>>()
const cryptoIndexFetchPromises = new Map<string, Promise<CryptoIndexResponse | null>>()
const priceHistoryFetchPromises = new Map<string, Promise<MarketHistoryResponse | null>>()

const indicatorKey = (category: string | null | undefined, days: number) => `category:${category || 'all'}:days:${days}`
const dliLiquidityKey = (days: number, changeDays: number) => `days:${days}:change_days:${changeDays}`
const cryptoIndexKey = (topN: number, days: number) => `top_n:${topN}:days:${days}`
const priceHistoryKey = (symbol: string, timeframe: string, startDate: string) => (
  `symbol:${symbol}:timeframe:${timeframe}:start_date:${startDate}`
)

export const useMarketStore = defineStore('market', {
  state: (): MarketState => ({
    klineCache: {},
    sentimentCache: {
      value: null,
      timestamp: 0,
    },
    indicatorCache: {},
    indicatorLoading: {},
    indicatorErrors: {},
    dliLiquidityCache: {},
    dliLiquidityLoading: {},
    dliLiquidityErrors: {},
    cryptoIndexCache: {},
    cryptoIndexLoading: {},
    cryptoIndexErrors: {},
    priceHistoryCache: {},
    priceHistoryLoading: {},
    priceHistoryErrors: {},
  }),

  actions: {
    _readKlineSlice(data: OhlcvPointResponse[] | null | undefined, limit: number): OhlcvPointResponse[] | null {
      if (!Array.isArray(data) || data.length === 0) return null
      if (limit <= 0 || data.length <= limit) return data
      return data.slice(-limit)
    },

    _setKlineCache(key: string, data: OhlcvPointResponse[]) {
      this.klineCache[key] = {
        data,
        timestamp: Date.now(),
      }
    },

    setKlineHistory(
      symbol: string,
      timeframe: string,
      data: OhlcvPointResponse[],
      maxLength: number = 1000,
    ): OhlcvPointResponse[] {
      const key = `${symbol}:${timeframe}`
      const trimmed = this._mergeKlines(data).slice(-maxLength)
      this._setKlineCache(key, trimmed)
      return trimmed
    },

    _mergeKlines(...batches: Array<OhlcvPointResponse[] | null | undefined>): OhlcvPointResponse[] {
      const merged = new Map<number, OhlcvPointResponse>()
      batches.forEach((batch) => {
        if (!batch) return
        batch.forEach((row) => {
          if (typeof row?.timestamp === 'number') merged.set(row.timestamp, row)
        })
      })
      return Array.from(merged.values()).sort((left, right) => left.timestamp - right.timestamp)
    },

    async getKlineData(
      symbol: string,
      timeframe: string,
      limit: number = 1000,
      options: { force?: boolean } = {},
    ): Promise<OhlcvPointResponse[] | null> {
      const key = `${symbol}:${timeframe}`
      const now = Date.now()
      const forceRefresh = Boolean(options.force)

      const cachedParams = this.klineCache[key]
      let cachedData: OhlcvPointResponse[] | null = null

      if (cachedParams) {
        cachedData = cachedParams.data
        if (!forceRefresh && now - cachedParams.timestamp < 10000 && cachedData.length >= limit) {
          return this._readKlineSlice(cachedData, limit)
        }
      }

      const fetchPromise = (async (): Promise<OhlcvPointResponse[] | null> => {
        const fetchKey = `${key}:${limit}`
        const pending = klineFetchPromises.get(fetchKey)
        if (pending) return pending
        const request = (async (): Promise<OhlcvPointResponse[] | null> => {
          try {
            const res = await marketApi.getLatestKlines({ symbol, timeframe, limit })
            const items = res.items || []
            if (items.length) {
              this._setKlineCache(key, items)
              return this._readKlineSlice(items, limit)
            }
          } catch (e) {
            console.error('Kline fetch failed', e)
          } finally {
            klineFetchPromises.delete(fetchKey)
          }
          return null
        })()
        klineFetchPromises.set(fetchKey, request)
        return request
      })()

      if (cachedData && !forceRefresh) {
        fetchPromise.then(() => {})
        return this._readKlineSlice(cachedData, limit)
      }
      const freshData = await fetchPromise
      return freshData || this._readKlineSlice(cachedData, limit)
    },

    applyKlineTail(
      symbol: string,
      timeframe: string,
      tail: OhlcvPointResponse[],
      maxLength: number = 1000,
    ): OhlcvPointResponse[] {
      const key = `${symbol}:${timeframe}`
      const current = this.klineCache[key]?.data || []
      const merged = this._mergeKlines(current, tail)
      const trimmed = merged.slice(-maxLength)
      this._setKlineCache(key, trimmed)
      return trimmed
    },

    prependKlineHistory(
      symbol: string,
      timeframe: string,
      history: OhlcvPointResponse[],
      maxLength: number = 5000,
    ): OhlcvPointResponse[] {
      const key = `${symbol}:${timeframe}`
      const current = this.klineCache[key]?.data || []
      const merged = this._mergeKlines(history, current)
      const trimmed = merged.slice(-maxLength)
      this._setKlineCache(key, trimmed)
      return trimmed
    },

    async getSentiment(): Promise<SentimentData | null> {
      const now = Date.now()
      if (this.sentimentCache.value && now - this.sentimentCache.timestamp < 300000) {
        if (now - this.sentimentCache.timestamp > 60000) {
          this._fetchSentiment()
        }
        return this.sentimentCache.value
      }
      return await this._fetchSentiment()
    },

    async _fetchSentiment(): Promise<SentimentData | null> {
      try {
        const res = await this.getMarketIndicators(null, 7)
        if (res && Array.isArray(res)) {
          const fearGreed = (res as MarketIndicatorResponse[]).find(ind => ind.indicator_id === 'FEAR_GREED')
          if (fearGreed && fearGreed.current_value !== null) {
            const sentimentData: SentimentData = {
              value: fearGreed.current_value,
              label: this._getSentimentLabel(fearGreed.current_value),
              last_updated: fearGreed.last_updated,
            }
            this.sentimentCache = {
              value: sentimentData,
              timestamp: Date.now(),
            }
            return sentimentData
          }
        }
      } catch (e) {
        console.error('Sentiment fetch error', e)
      }
      return null
    },

    getMarketIndicatorsCacheKey(category: string | null | undefined, days: number): string {
      return indicatorKey(category, days)
    },

    readMarketIndicators(category: string | null | undefined, days: number): MarketIndicatorResponse[] | null {
      return this.indicatorCache[this.getMarketIndicatorsCacheKey(category, days)]?.data || null
    },

    isMarketIndicatorsLoading(category: string | null | undefined, days: number): boolean {
      return Boolean(this.indicatorLoading[this.getMarketIndicatorsCacheKey(category, days)])
    },

    getMarketIndicatorsError(category: string | null | undefined, days: number): string {
      return this.indicatorErrors[this.getMarketIndicatorsCacheKey(category, days)] || ''
    },

    async getMarketIndicators(
      category: string | null | undefined,
      days: number,
      options: { force?: boolean } = {},
    ): Promise<MarketIndicatorResponse[] | null> {
      const key = this.getMarketIndicatorsCacheKey(category, days)
      if (!options.force && this.indicatorCache[key]) {
        return this.indicatorCache[key].data
      }

      const pending = indicatorFetchPromises.get(key)
      if (pending) return pending

      this.indicatorLoading[key] = true
      this.indicatorErrors[key] = ''

      const request = (async (): Promise<MarketIndicatorResponse[] | null> => {
        try {
          const response = await marketApi.getIndicators({ category: category || undefined, days })
          const data = Array.isArray(response) ? response : []
          this.indicatorCache[key] = {
            data,
            timestamp: Date.now(),
          }
          return data
        } catch (e) {
          console.error('Market indicators fetch failed', e)
          this.indicatorErrors[key] = '市场指标数据加载失败'
        } finally {
          this.indicatorLoading[key] = false
          indicatorFetchPromises.delete(key)
        }
        return this.indicatorCache[key]?.data || null
      })()

      indicatorFetchPromises.set(key, request)
      return request
    },

    getDliLiquidityCacheKey(days: number, changeDays: number = 30): string {
      return dliLiquidityKey(days, changeDays)
    },

    readDliLiquidity(days: number, changeDays: number = 30): DliLiquidityResponse | null {
      return this.dliLiquidityCache[this.getDliLiquidityCacheKey(days, changeDays)]?.data || null
    },

    isDliLiquidityLoading(days: number, changeDays: number = 30): boolean {
      return Boolean(this.dliLiquidityLoading[this.getDliLiquidityCacheKey(days, changeDays)])
    },

    getDliLiquidityError(days: number, changeDays: number = 30): string {
      return this.dliLiquidityErrors[this.getDliLiquidityCacheKey(days, changeDays)] || ''
    },

    async getDliLiquidity(
      days: number,
      changeDays: number = 30,
      options: { force?: boolean } = {},
    ): Promise<DliLiquidityResponse | null> {
      const key = this.getDliLiquidityCacheKey(days, changeDays)
      if (!options.force && this.dliLiquidityCache[key]) {
        return this.dliLiquidityCache[key].data
      }

      const pending = dliLiquidityFetchPromises.get(key)
      if (pending) return pending

      this.dliLiquidityLoading[key] = true
      this.dliLiquidityErrors[key] = ''

      const request = (async (): Promise<DliLiquidityResponse | null> => {
        try {
          const response = await marketApi.getDliLiquidity({ days, change_days: changeDays })
          if (response) {
            this.dliLiquidityCache[key] = {
              data: response,
              timestamp: Date.now(),
            }
            return response
          }
        } catch (e) {
          console.error('DLI liquidity fetch failed', e)
          this.dliLiquidityErrors[key] = '宏观流动性数据加载失败'
        } finally {
          this.dliLiquidityLoading[key] = false
          dliLiquidityFetchPromises.delete(key)
        }
        return this.dliLiquidityCache[key]?.data || null
      })()

      dliLiquidityFetchPromises.set(key, request)
      return request
    },

    getCryptoIndexCacheKey(topN: number, days: number): string {
      return cryptoIndexKey(topN, days)
    },

    readCryptoIndex(topN: number, days: number): CryptoIndexResponse | null {
      return this.cryptoIndexCache[this.getCryptoIndexCacheKey(topN, days)]?.data || null
    },

    isCryptoIndexLoading(topN: number, days: number): boolean {
      return Boolean(this.cryptoIndexLoading[this.getCryptoIndexCacheKey(topN, days)])
    },

    getCryptoIndexError(topN: number, days: number): string {
      return this.cryptoIndexErrors[this.getCryptoIndexCacheKey(topN, days)] || ''
    },

    async getCryptoIndex(
      topN: number,
      days: number,
      options: { force?: boolean } = {},
    ): Promise<CryptoIndexResponse | null> {
      const key = this.getCryptoIndexCacheKey(topN, days)
      if (!options.force && this.cryptoIndexCache[key]) {
        return this.cryptoIndexCache[key].data
      }

      const pending = cryptoIndexFetchPromises.get(key)
      if (pending) return pending

      this.cryptoIndexLoading[key] = true
      this.cryptoIndexErrors[key] = ''

      const request = (async (): Promise<CryptoIndexResponse | null> => {
        try {
          const response = await marketApi.getCryptoIndex({ top_n: topN, days })
          if (response) {
            this.cryptoIndexCache[key] = {
              data: response,
              timestamp: Date.now(),
            }
            return response
          }
        } catch (e) {
          console.error('Crypto index fetch failed', e)
          this.cryptoIndexErrors[key] = 'Failed to load crypto index data.'
        } finally {
          this.cryptoIndexLoading[key] = false
          cryptoIndexFetchPromises.delete(key)
        }
        return this.cryptoIndexCache[key]?.data || null
      })()

      cryptoIndexFetchPromises.set(key, request)
      return request
    },

    getPriceHistoryCacheKey(symbol: string, timeframe: string, startDate: string): string {
      return priceHistoryKey(symbol, timeframe, startDate)
    },

    readPriceHistory(symbol: string, timeframe: string, startDate: string): MarketHistoryResponse | null {
      return this.priceHistoryCache[this.getPriceHistoryCacheKey(symbol, timeframe, startDate)]?.data || null
    },

    isPriceHistoryLoading(symbol: string, timeframe: string, startDate: string): boolean {
      return Boolean(this.priceHistoryLoading[this.getPriceHistoryCacheKey(symbol, timeframe, startDate)])
    },

    getPriceHistoryError(symbol: string, timeframe: string, startDate: string): string {
      return this.priceHistoryErrors[this.getPriceHistoryCacheKey(symbol, timeframe, startDate)] || ''
    },

    async getPriceHistory(
      symbol: string,
      timeframe: string,
      startDate: string,
      options: { force?: boolean } = {},
    ): Promise<MarketHistoryResponse | null> {
      const key = this.getPriceHistoryCacheKey(symbol, timeframe, startDate)
      if (!options.force && this.priceHistoryCache[key]) {
        return this.priceHistoryCache[key].data
      }

      const pending = priceHistoryFetchPromises.get(key)
      if (pending) return pending

      this.priceHistoryLoading[key] = true
      this.priceHistoryErrors[key] = ''

      const request = (async (): Promise<MarketHistoryResponse | null> => {
        try {
          const response = await marketApi.getPriceHistory({ symbol, timeframe, start_date: startDate })
          if (response) {
            this.priceHistoryCache[key] = {
              data: response,
              timestamp: Date.now(),
            }
            if (response.items?.length) {
              this.setKlineHistory(symbol, timeframe, response.items, response.items.length)
            }
            return response
          }
        } catch (e) {
          console.error('Price history fetch failed', e)
          this.priceHistoryErrors[key] = '历史价格数据加载失败'
        } finally {
          this.priceHistoryLoading[key] = false
          priceHistoryFetchPromises.delete(key)
        }
        return this.priceHistoryCache[key]?.data || null
      })()

      priceHistoryFetchPromises.set(key, request)
      return request
    },

    _getSentimentLabel(value: number): string {
      const labels = {
        extremeFear: 'Extreme Fear',
        fear: 'Fear',
        neutral: 'Neutral',
        greed: 'Greed',
        extremeGreed: 'Extreme Greed',
      }
      return labels[resolveSentimentBucket(value)]
    },
  },
})

