import { defineStore } from 'pinia'
import { marketInsightApi } from './api'
import { resolveSentimentBucket } from './sentiment'
import type { MarketIndicatorResponse, SentimentCache, SentimentData } from './contracts'
import { isCacheFresh, MARKET_CACHE_TTL_MS, writeCacheEntry, type CacheEntry } from './cacheTypes'

interface MarketIndicatorState {
  sentimentCache: SentimentCache
  indicatorCache: Record<string, CacheEntry<MarketIndicatorResponse[]>>
  indicatorLoading: Record<string, boolean>
  indicatorErrors: Record<string, string>
}

const indicatorFetchPromises = new Map<string, Promise<MarketIndicatorResponse[] | null>>()
const indicatorKey = (category: string | null | undefined, days: number) => `category:${category || 'all'}:days:${days}`

export const useMarketIndicatorStore = defineStore('marketIndicators', {
  state: (): MarketIndicatorState => ({
    sentimentCache: {
      value: null,
      timestamp: 0,
    },
    indicatorCache: {},
    indicatorLoading: {},
    indicatorErrors: {},
  }),

  actions: {
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
      if (!options.force && isCacheFresh(this.indicatorCache[key], MARKET_CACHE_TTL_MS.marketIndicators)) {
        return this.indicatorCache[key].data
      }

      const pending = indicatorFetchPromises.get(key)
      if (pending) return pending

      this.indicatorLoading[key] = true
      this.indicatorErrors[key] = ''

      const request = (async (): Promise<MarketIndicatorResponse[] | null> => {
        try {
          const response = await marketInsightApi.getIndicators({ category: category || undefined, days })
          const data = Array.isArray(response) ? response : []
          writeCacheEntry(this.indicatorCache, key, data)
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

    async getSentiment(): Promise<SentimentData | null> {
      const now = Date.now()
      if (this.sentimentCache.value && isCacheFresh(this.sentimentCache, MARKET_CACHE_TTL_MS.sentimentFresh, now)) {
        if (!isCacheFresh(this.sentimentCache, MARKET_CACHE_TTL_MS.sentimentRefresh, now)) {
          this.fetchSentiment()
        }
        return this.sentimentCache.value
      }
      return await this.fetchSentiment()
    },

    async fetchSentiment(): Promise<SentimentData | null> {
      try {
        const res = await this.getMarketIndicators(null, 7)
        if (res && Array.isArray(res)) {
          const fearGreed = res.find((ind) => ind.indicator_id === 'FEAR_GREED')
          if (fearGreed && fearGreed.current_value !== null) {
            const sentimentData: SentimentData = {
              value: fearGreed.current_value,
              label: this.getSentimentLabel(fearGreed.current_value),
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

    getSentimentLabel(value: number): string {
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
