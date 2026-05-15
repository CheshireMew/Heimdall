import { defineStore } from 'pinia'
import { marketHistoryApi } from './api'
import { useKlineStore } from './klineStore'
import type { MarketHistoryResponse } from './contracts'
import { isCacheFresh, MARKET_CACHE_TTL_MS, writeCacheEntry, type CacheEntry } from './cacheTypes'

interface PriceHistoryState {
  priceHistoryCache: Record<string, CacheEntry<MarketHistoryResponse>>
  priceHistoryLoading: Record<string, boolean>
  priceHistoryErrors: Record<string, string>
}

const priceHistoryFetchPromises = new Map<string, Promise<MarketHistoryResponse | null>>()
const priceHistoryKey = (symbol: string, timeframe: string, startDate: string) => (
  `symbol:${symbol}:timeframe:${timeframe}:start_date:${startDate}`
)

export const usePriceHistoryStore = defineStore('priceHistory', {
  state: (): PriceHistoryState => ({
    priceHistoryCache: {},
    priceHistoryLoading: {},
    priceHistoryErrors: {},
  }),

  actions: {
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
      if (!options.force && isCacheFresh(this.priceHistoryCache[key], MARKET_CACHE_TTL_MS.priceHistory)) {
        return this.priceHistoryCache[key].data
      }

      const pending = priceHistoryFetchPromises.get(key)
      if (pending) return pending

      this.priceHistoryLoading[key] = true
      this.priceHistoryErrors[key] = ''

      const request = (async (): Promise<MarketHistoryResponse | null> => {
        try {
          const response = await marketHistoryApi.getPriceHistory({ symbol, timeframe, start_date: startDate })
          if (response) {
            writeCacheEntry(this.priceHistoryCache, key, response)
            if (response.items?.length) {
              useKlineStore().setKlineHistory(symbol, timeframe, response.items, response.items.length)
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
  },
})
