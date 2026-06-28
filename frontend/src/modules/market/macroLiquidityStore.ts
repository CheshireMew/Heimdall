import { defineStore } from 'pinia'
import { marketInsightApi } from './api'
import type { DliLiquidityResponse } from './contracts'
import { MARKET_CACHE_TTL_MS, type CacheEntry } from './cacheTypes'
import { createResourceCache } from './resourceCache'

interface MacroLiquidityState {
  dliLiquidityCache: Record<string, CacheEntry<DliLiquidityResponse>>
  dliLiquidityLoading: Record<string, boolean>
  dliLiquidityErrors: Record<string, string>
}

const dliLiquidityResource = createResourceCache()
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
      return dliLiquidityResource.load({
        cache: this.dliLiquidityCache,
        key,
        ttlMs: MARKET_CACHE_TTL_MS.macroLiquidity,
        force: options.force,
        load: () => marketInsightApi.getDliLiquidity({ days, change_days: changeDays }),
        onLoadStart: () => {
          this.dliLiquidityLoading[key] = true
          this.dliLiquidityErrors[key] = ''
        },
        onLoadEnd: () => {
          this.dliLiquidityLoading[key] = false
        },
        onLoadError: (error) => {
          console.error('DLI liquidity fetch failed', error)
          this.dliLiquidityErrors[key] = '宏观流动性数据加载失败'
        }
      })
    },
  },
})
