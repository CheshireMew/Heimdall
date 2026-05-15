import { defineStore } from 'pinia'
import { marketHistoryApi } from './api'
import type { OhlcvPointResponse } from './contracts'
import { isCacheFresh, MARKET_CACHE_TTL_MS, writeCacheEntry, type CacheEntry } from './cacheTypes'

interface KlineState {
  klineCache: Record<string, CacheEntry<OhlcvPointResponse[]>>
}

const klineFetchPromises = new Map<string, Promise<OhlcvPointResponse[] | null>>()

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

      const fetchKey = `${key}:${limit}`
      const pending = klineFetchPromises.get(fetchKey)
      const fetchPromise = pending || (async (): Promise<OhlcvPointResponse[] | null> => {
        try {
          const res = await marketHistoryApi.getLatestKlines({ symbol, timeframe, limit })
          const items = res.items || []
          if (items.length) {
            this.setKlineCache(key, items)
            return this.readKlineSlice(items, limit)
          }
        } catch (e) {
          console.error('Kline fetch failed', e)
        } finally {
          klineFetchPromises.delete(fetchKey)
        }
        return null
      })()
      if (!pending) klineFetchPromises.set(fetchKey, fetchPromise)

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
