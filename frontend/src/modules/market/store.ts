import { defineStore } from 'pinia'
import { marketApi } from './api'
import { resolveSentimentBucket } from './sentiment'
import type { OHLCVRaw, KlineCacheEntry, SentimentCache, SentimentData, IndicatorItem } from '@/types'

interface MarketState {
  klineCache: Record<string, KlineCacheEntry>
  sentimentCache: SentimentCache
}

export const useMarketStore = defineStore('market', {
  state: (): MarketState => ({
    klineCache: {},
    sentimentCache: {
      value: null,
      timestamp: 0,
    },
  }),

  actions: {
    init() {
      try {
        const stored = localStorage.getItem('heimdall_market_cache')
        if (stored) {
          const parsed = JSON.parse(stored) as Partial<MarketState>
          this.klineCache = parsed.klineCache || {}
          this.sentimentCache = parsed.sentimentCache || { value: null, timestamp: 0 }
          this.cleanup()
        }
      } catch (e) {
        console.warn('Failed to load market cache', e)
      }
    },

    save() {
      try {
        localStorage.setItem(
          'heimdall_market_cache',
          JSON.stringify({
            klineCache: this.klineCache,
            sentimentCache: this.sentimentCache,
          })
        )
      } catch (e) {
        console.warn('Failed to save market cache', e)
      }
    },

    cleanup() {
      const now = Date.now()
      const oneWeek = 7 * 24 * 60 * 60 * 1000

      let changed = false
      for (const key in this.klineCache) {
        if (now - this.klineCache[key].timestamp > oneWeek) {
          delete this.klineCache[key]
          changed = true
        }
      }
      if (changed) this.save()
    },

    async getKlineData(symbol: string, timeframe: string, limit: number = 1000): Promise<OHLCVRaw[] | null> {
      const key = `${symbol}:${timeframe}`
      const now = Date.now()

      const cachedParams = this.klineCache[key]
      let cachedData: OHLCVRaw[] | null = null

      if (cachedParams) {
        cachedData = cachedParams.data
        if (now - cachedParams.timestamp < 10000) {
          return cachedData
        }
      }

      const fetchPromise = (async (): Promise<OHLCVRaw[] | null> => {
        try {
          const res = await marketApi.getLatestKlines({ symbol, timeframe, limit })
          if (Array.isArray(res.data) && res.data.length) {
            this.klineCache[key] = {
              data: res.data,
              timestamp: Date.now(),
            }
            this.save()
            return res.data
          }
        } catch (e) {
          console.error('Background fetch failed', e)
        }
        return null
      })()

      if (cachedData) {
        fetchPromise.then(() => {})
        return cachedData
      }
      return await fetchPromise
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
        const res = await marketApi.getIndicators({ days: 7 })
        if (res.data && Array.isArray(res.data)) {
          const fearGreed = (res.data as IndicatorItem[]).find(ind => ind.indicator_id === 'FEAR_GREED')
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
            this.save()
            return sentimentData
          }
        }
      } catch (e) {
        console.error('Sentiment fetch error', e)
      }
      return null
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
