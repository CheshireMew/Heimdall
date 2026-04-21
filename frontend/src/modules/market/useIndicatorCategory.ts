import { ref, watch, type ComputedRef } from 'vue'
import { marketApi } from './api'
import type { MarketIndicatorResponse } from '../../types/market'

export function useIndicatorCategory(category: ComputedRef<string>, days: number = 90) {
  const indicators = ref<MarketIndicatorResponse[]>([])
  const loading = ref(true)
  const error = ref('')

  const load = async () => {
    loading.value = true
    error.value = ''
    try {
      const res = await marketApi.getIndicators({ category: category.value, days })
      indicators.value = res?.data || []
    } catch (e) {
      console.error(`Failed to fetch ${category.value} indicators:`, e)
      error.value = 'Failed to load indicators.'
      indicators.value = []
    } finally {
      loading.value = false
    }
  }

  watch(category, () => {
    load()
  })

  return {
    indicators,
    loading,
    error,
    load,
  }
}
