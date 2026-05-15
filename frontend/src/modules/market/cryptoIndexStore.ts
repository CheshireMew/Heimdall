import { defineStore } from 'pinia'
import { marketInsightApi } from './api'
import type { CryptoIndexResponse } from './contracts'
import { isCacheFresh, MARKET_CACHE_TTL_MS, writeCacheEntry, type CacheEntry } from './cacheTypes'

interface CryptoIndexState {
  cryptoIndexCache: Record<string, CacheEntry<CryptoIndexResponse>>
  cryptoIndexLoading: Record<string, boolean>
  cryptoIndexErrors: Record<string, string>
}

const cryptoIndexFetchPromises = new Map<string, Promise<CryptoIndexResponse | null>>()
const cryptoIndexKey = (topN: number, days: number) => `top_n:${topN}:days:${days}`

export const useCryptoIndexStore = defineStore('cryptoIndex', {
  state: (): CryptoIndexState => ({
    cryptoIndexCache: {},
    cryptoIndexLoading: {},
    cryptoIndexErrors: {},
  }),

  actions: {
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
      if (!options.force && isCacheFresh(this.cryptoIndexCache[key], MARKET_CACHE_TTL_MS.cryptoIndex)) {
        return this.cryptoIndexCache[key].data
      }

      const pending = cryptoIndexFetchPromises.get(key)
      if (pending) return pending

      this.cryptoIndexLoading[key] = true
      this.cryptoIndexErrors[key] = ''

      const request = (async (): Promise<CryptoIndexResponse | null> => {
        try {
          const response = await marketInsightApi.getCryptoIndex({ top_n: topN, days })
          if (response) {
            writeCacheEntry(this.cryptoIndexCache, key, response)
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
  },
})
