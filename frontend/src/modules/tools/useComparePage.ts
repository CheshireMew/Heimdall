import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'

import { bindPageSnapshot, createPageSnapshot, isRecord, PAGE_SNAPSHOT_KEYS, readNumber, readString } from '@/composables/pageSnapshot'
import { isIndexSymbol } from '@/modules/market'
import { useTheme } from '@/composables/useTheme'
import { toolsApi } from './api'
import type { MarketSymbolSearchItem } from '@/types'

interface ComparePageSnapshot {
  config: {
    symbolA: string
    symbolB: string
    days: number
    timeframe: string
  }
}

const createDefaultSnapshot = (): ComparePageSnapshot => ({
  config: {
    symbolA: 'BTC',
    symbolB: 'ETH',
    days: 30,
    timeframe: '1h',
  },
})

const normalizeSnapshot = (value: unknown): ComparePageSnapshot => {
  const defaults = createDefaultSnapshot()
  if (!isRecord(value) || !isRecord(value.config)) return defaults
  return {
    config: {
      symbolA: readString(value.config.symbolA, defaults.config.symbolA),
      symbolB: readString(value.config.symbolB, defaults.config.symbolB),
      days: readNumber(value.config.days, defaults.config.days),
      timeframe: readString(value.config.timeframe, defaults.config.timeframe),
    },
  }
}


export function useComparePage() {
  const { theme } = useTheme()
  const pageSnapshot = createPageSnapshot(PAGE_SNAPSHOT_KEYS.compare, normalizeSnapshot, createDefaultSnapshot())
  const restoredSnapshot = pageSnapshot.load()

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
  const dataA = ref([])
  const dataB = ref([])
  const dataRatio = ref([])
  const chartARef = ref(null)
  const chartBRef = ref(null)
  const chartRatioRef = ref(null)
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
      const handler = (range) => {
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

  const handleSymbolSelect = (item: MarketSymbolSearchItem) => {
    if (item.asset_class === 'index') config.timeframe = '1d'
  }

  const symbolLabel = (symbol: string) => isIndexSymbol(symbol) ? symbol : `${symbol}/USDT`

  onMounted(() => {
    fetchComparisonData()
  })

  bindPageSnapshot(
    config,
    () => ({
      config: {
        symbolA: readString(config.symbolA, 'BTC'),
        symbolB: readString(config.symbolB, 'ETH'),
        days: readNumber(config.days, 30),
        timeframe: readString(config.timeframe, '1h'),
      },
    }),
    pageSnapshot.save,
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
