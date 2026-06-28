import { defineStore } from 'pinia'
import { marketHistoryApi } from './api'
import type { OhlcvPointResponse } from './contracts'
import { isCacheFresh, MARKET_CACHE_TTL_MS, writeCacheEntry, type CacheEntry } from './cacheTypes'
import { createResourceCache } from './resourceCache'

interface KlineState {
  klineCache: Record<string, CacheEntry<OhlcvPointResponse[]>>
}

const klineResource = createResourceCache()

export const useKlineStore = defineStore('marketKline', {
  state: (): KlineState => ({
    klineCache: {},
  }),

  actions: {
    readKlineSlice(data: OhlcvPointResponse[] | null | undefined, limit: number): OhlcvPointResponse[] | null {
      if (!Array.isArray(data) || data.length === 0) return null
      if (limit <= 0 || data.length <= limit) return data
      return data.slice(-limit)
    },

    setKlineCache(key: string, data: OhlcvPointResponse[]) {
      writeCacheEntry(this.klineCache, key, data)
    },

    mergeKlines(...batches: Array<OhlcvPointResponse[] | null | undefined>): OhlcvPointResponse[] {
      const merged = new Map<number, OhlcvPointResponse>()
      batches.forEach((batch) => {
        if (!batch) return
        batch.forEach((row) => {
          if (typeof row?.timestamp === 'number') merged.set(row.timestamp, row)
        })
      })
      return Array.from(merged.values()).sort((left, right) => left.timestamp - right.timestamp)
    },

    setKlineHistory(
      symbol: string,
      timeframe: string,
      data: OhlcvPointResponse[],
      maxLength: number = 1000,
    ): OhlcvPointResponse[] {
      const key = `${symbol}:${timeframe}`
      const trimmed = this.mergeKlines(data).slice(-maxLength)
      this.setKlineCache(key, trimmed)
      return trimmed
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
        if (!forceRefresh && isCacheFresh(cachedParams, MARKET_CACHE_TTL_MS.klineLive, now) && cachedData.length >= limit) {
          return this.readKlineSlice(cachedData, limit)
        }
      }

      const fetchPromise = klineResource.load({
        cache: this.klineCache,
        key,
        pendingKey: `${key}:limit:${limit}`,
        ttlMs: MARKET_CACHE_TTL_MS.klineLive,
        force: true,
        load: async () => {
          const res = await marketHistoryApi.getLatestKlines({ symbol, timeframe, limit })
          const items = res.items || []
          return items.length ? items : null
        },
        onLoadError: (error) => {
          console.error('Kline fetch failed', error)
        },
      }).then((data) => this.readKlineSlice(data, limit))

      if (cachedData && !forceRefresh) {
        fetchPromise.then(() => {})
        return this.readKlineSlice(cachedData, limit)
      }
      const freshData = await fetchPromise
      return freshData || this.readKlineSlice(cachedData, limit)
    },

    applyKlineTail(
      symbol: string,
      timeframe: string,
      tail: OhlcvPointResponse[],
      maxLength: number = 1000,
    ): OhlcvPointResponse[] {
      const key = `${symbol}:${timeframe}`
      const current = this.klineCache[key]?.data || []
      const trimmed = this.mergeKlines(current, tail).slice(-maxLength)
      this.setKlineCache(key, trimmed)
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
      const trimmed = this.mergeKlines(history, current).slice(-maxLength)
      this.setKlineCache(key, trimmed)
      return trimmed
    },
  },
})
