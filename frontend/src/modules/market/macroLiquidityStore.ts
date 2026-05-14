import { defineStore } from 'pinia'
import { marketApi } from './api'
import type { DliLiquidityResponse } from './contracts'
import { isCacheFresh, MARKET_CACHE_TTL_MS, writeCacheEntry, type CacheEntry } from './cacheTypes'

interface MacroLiquidityState {
  dliLiquidityCache: Record<string, CacheEntry<DliLiquidityResponse>>
  dliLiquidityLoading: Record<string, boolean>
  dliLiquidityErrors: Record<string, string>
}

const dliLiquidityFetchPromises = new Map<string, Promise<DliLiquidityResponse | null>>()
const dliLiquidityKey = (days: number, changeDays: number) => `days:${days}:change_days:${changeDays}`

export const useMacroLiquidityStore = defineStore('macroLiquidity', {
  state: (): MacroLiquidityState => ({
    dliLiquidityCache: {},
    dliLiquidityLoading: {},
    dliLiquidityErrors: {},
  }),

  actions: {
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
      if (!options.force && isCacheFresh(this.dliLiquidityCache[key], MARKET_CACHE_TTL_MS.macroLiquidity)) {
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
            writeCacheEntry(this.dliLiquidityCache, key, response)
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
  },
})
