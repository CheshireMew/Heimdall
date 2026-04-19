import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'

import { createPersistentPageSnapshot, PAGE_SNAPSHOT_KEYS } from '@/composables/pageSnapshot'
import { isIndexSymbol } from '@/modules/market'
import type { CandlestickData } from '@/modules/market/contracts'
import type { MarketSymbolSearchResponse } from '@/modules/market/contracts'
import { useTheme } from '@/composables/useTheme'
import { toolsApi } from './api'
import { buildCompareSnapshot, createDefaultCompareSnapshot, normalizeCompareSnapshot } from './pageSnapshots'

interface CompareLinePoint {
  time: number
  value: number
}

interface SyncableChart {
  timeScale: () => {
    setVisibleLogicalRange: (range: unknown) => void
    subscribeVisibleLogicalRangeChange: (handler: (range: unknown) => void) => void
    unsubscribeVisibleLogicalRangeChange: (handler: (range: unknown) => void) => void
  }
}

interface ChartComponentRef {
  chart?: SyncableChart | null
}

export function useComparePage() {
  const { theme } = useTheme()
  const pageSnapshot = createPersistentPageSnapshot(PAGE_SNAPSHOT_KEYS.compare, normalizeCompareSnapshot, createDefaultCompareSnapshot())
  const restoredSnapshot = pageSnapshot.initial

  const chartColors = computed(() => {
    const isDark = theme.value === 'dark'
    return {
      bg: isDark ? '#1f2937' : '#ffffff',
      grid: isDark ? '#374151' : '#e5e7eb',
      text: isDark ? '#9ca3af' : '#4b5563',
      upColor: '#3b82f6',
      downColor: '#1d4ed8',
    }
  })

  const config = reactive(restoredSnapshot.config)

  const loading = ref(false)
  const dataA = ref<CandlestickData[]>([])
  const dataB = ref<CandlestickData[]>([])
  const dataRatio = ref<CompareLinePoint[]>([])
  const chartARef = ref<ChartComponentRef | null>(null)
  const chartBRef = ref<ChartComponentRef | null>(null)
  const chartRatioRef = ref<ChartComponentRef | null>(null)
  const syncUnsubscribers = ref<Array<() => void>>([])

  const syncCharts = () => {
    syncUnsubscribers.value.forEach((fn) => fn())
    syncUnsubscribers.value = []

    const chartA = chartARef.value?.chart
    const chartB = chartBRef.value?.chart
    const chartRatio = chartRatioRef.value?.chart
    if (!chartA || !chartB || !chartRatio) {
      return
    }

    const charts = [chartA, chartB, chartRatio]
    charts.forEach((sourceChart) => {
      const handler = (range: unknown) => {
        if (!range) {
          return
        }
        charts.forEach((targetChart) => {
          if (sourceChart !== targetChart) {
            targetChart.timeScale().setVisibleLogicalRange(range)
          }
        })
      }
      sourceChart.timeScale().subscribeVisibleLogicalRangeChange(handler)
      syncUnsubscribers.value.push(() => {
        try {
          sourceChart.timeScale().unsubscribeVisibleLogicalRangeChange(handler)
        } catch {}
      })
    })
  }

  const fetchComparisonData = async () => {
    loading.value = true
    try {
      if (isIndexSymbol(config.symbolA) || isIndexSymbol(config.symbolB)) {
        config.timeframe = '1d'
      }
      const response = await toolsApi.comparePairs({
        symbol_a: config.symbolA,
        symbol_b: config.symbolB,
        days: config.days,
        timeframe: config.timeframe,
      })
      dataA.value = response.data.data_a || []
      dataB.value = response.data.data_b || []
      dataRatio.value = (response.data.ratio_ohlc || []).map((item) => ({
        time: item.time,
        value: item.close,
      }))
      nextTick(() => {
        syncCharts()
      })
    } catch (error) {
      console.error('Comparison fetch failed', error)
    } finally {
      loading.value = false
    }
  }

  const handleSymbolSelect = (item: MarketSymbolSearchResponse) => {
    if (item.asset_class === 'index') config.timeframe = '1d'
  }

  const symbolLabel = (symbol: string) => isIndexSymbol(symbol) ? symbol : `${symbol}/USDT`

  onMounted(() => {
    fetchComparisonData()
  })

  pageSnapshot.bind(
    config,
    () => buildCompareSnapshot(config),
  )

  onBeforeUnmount(() => {
    syncUnsubscribers.value.forEach((fn) => fn())
    syncUnsubscribers.value = []
  })

  return {
    chartColors,
    config,
    loading,
    dataA,
    dataB,
    dataRatio,
    chartARef,
    chartBRef,
    chartRatioRef,
    fetchComparisonData,
    handleSymbolSelect,
    symbolLabel,
  }
}
