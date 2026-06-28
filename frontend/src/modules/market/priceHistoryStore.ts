import { defineStore } from 'pinia'
import { marketHistoryApi } from './api'
import { useKlineStore } from './klineStore'
import type { MarketHistoryResponse } from './contracts'
import { MARKET_CACHE_TTL_MS, type CacheEntry } from './cacheTypes'
import { createResourceCache } from './resourceCache'

interface PriceHistoryState {
  priceHistoryCache: Record<string, CacheEntry<MarketHistoryResponse>>
  priceHistoryLoading: Record<string, boolean>
  priceHistoryErrors: Record<string, string>
}

const priceHistoryResource = createResourceCache()
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
      return priceHistoryResource.load({
        cache: this.priceHistoryCache,
        key,
        ttlMs: MARKET_CACHE_TTL_MS.priceHistory,
        force: options.force,
        load: () => marketHistoryApi.getPriceHistory({ symbol, timeframe, start_date: startDate }),
        onLoadStart: () => {
          this.priceHistoryLoading[key] = true
          this.priceHistoryErrors[key] = ''
        },
        onLoadEnd: () => {
          this.priceHistoryLoading[key] = false
        },
        onLoadError: (error) => {
          console.error('Price history fetch failed', error)
          this.priceHistoryErrors[key] = '历史价格数据加载失败'
        },
        onWrite: (response) => {
          if (response.items?.length) {
            useKlineStore().setKlineHistory(symbol, timeframe, response.items, response.items.length)
          }
        }
      })
    },
  },
})
