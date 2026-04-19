import { defineStore } from 'pinia'
import { marketApi } from './api'
import { resolveSentimentBucket } from './sentiment'
import type { MarketIndicatorResponse, OhlcvPointResponse } from './contracts'
import type { KlineCacheEntry, SentimentCache, SentimentData } from './contracts'

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
        try {
          const res = await marketApi.getLatestKlines({ symbol, timeframe, limit })
          const items = res.data.items || []
          if (items.length) {
            this._setKlineCache(key, items)
            return this._readKlineSlice(items, limit)
          }
        } catch (e) {
          console.error('Background fetch failed', e)
        }
        return null
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
        const res = await marketApi.getIndicators({ days: 7 })
        if (res.data && Array.isArray(res.data)) {
          const fearGreed = (res.data as MarketIndicatorResponse[]).find(ind => ind.indicator_id === 'FEAR_GREED')
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
