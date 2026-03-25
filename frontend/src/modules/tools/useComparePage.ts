import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'

import { useTheme } from '@/composables/useTheme'
import { toolsApi } from './api'


export function useComparePage() {
  const { theme } = useTheme()

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

  const config = reactive({
    symbolA: 'BTC',
    symbolB: 'ETH',
    days: 30,
    timeframe: '1h',
  })

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

  onMounted(() => {
    fetchComparisonData()
  })

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
  }
}
