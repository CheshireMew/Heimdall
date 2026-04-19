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
    _readKlineSlice(data: OHLCVRaw[] | null | undefined, limit: number): OHLCVRaw[] | null {
      if (!Array.isArray(data) || data.length === 0) return null
      if (limit <= 0 || data.length <= limit) return data
      return data.slice(-limit)
    },

    _setKlineCache(key: string, data: OHLCVRaw[]) {
      this.klineCache[key] = {
        data,
        timestamp: Date.now(),
      }
    },

    setKlineHistory(
      symbol: string,
      timeframe: string,
      data: OHLCVRaw[],
      maxLength: number = 1000,
    ): OHLCVRaw[] {
      const key = `${symbol}:${timeframe}`
      const trimmed = this._mergeKlines(data).slice(-maxLength)
      this._setKlineCache(key, trimmed)
      return trimmed
    },

    _mergeKlines(...batches: Array<OHLCVRaw[] | null | undefined>): OHLCVRaw[] {
      const merged = new Map<number, OHLCVRaw>()
      batches.forEach((batch) => {
        if (!batch) return
        batch.forEach((row) => {
          if (Array.isArray(row) && row.length >= 6) merged.set(row[0], row)
        })
      })
      return Array.from(merged.values()).sort((left, right) => left[0] - right[0])
    },

    async getKlineData(
      symbol: string,
      timeframe: string,
      limit: number = 1000,
      options: { force?: boolean } = {},
    ): Promise<OHLCVRaw[] | null> {
      const key = `${symbol}:${timeframe}`
      const now = Date.now()
      const forceRefresh = Boolean(options.force)

      const cachedParams = this.klineCache[key]
      let cachedData: OHLCVRaw[] | null = null

      if (cachedParams) {
        cachedData = cachedParams.data
        if (!forceRefresh && now - cachedParams.timestamp < 10000 && cachedData.length >= limit) {
          return this._readKlineSlice(cachedData, limit)
        }
      }

      const fetchPromise = (async (): Promise<OHLCVRaw[] | null> => {
        try {
          const res = await marketApi.getLatestKlines({ symbol, timeframe, limit })
          if (Array.isArray(res.data) && res.data.length) {
            this._setKlineCache(key, res.data)
            return this._readKlineSlice(res.data, limit)
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
      tail: OHLCVRaw[],
      maxLength: number = 1000,
    ): OHLCVRaw[] {
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
      history: OHLCVRaw[],
      maxLength: number = 5000,
    ): OHLCVRaw[] {
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
