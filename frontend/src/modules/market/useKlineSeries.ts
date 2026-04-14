import { computed, ref, watch, type Ref } from 'vue'
import { marketApi } from './api'
import { useMarketStore } from './store'
import { isIndexSymbol } from './symbolCatalog'
import type { OHLCVRaw } from '@/types'

export function useKlineSeries(symbol: Ref<string>, timeframe: Ref<string>) {
  const marketStore = useMarketStore()
  const klineData = ref<OHLCVRaw[]>([])
  const loadingMore = ref(false)
  const noMoreHistory = ref(false)

  const cacheKey = computed(() => `${symbol.value}:${timeframe.value}`)

  const chartData = computed(() =>
    klineData.value.map(k => ({
      time: k[0] / 1000,
      open: k[1],
      high: k[2],
      low: k[3],
      close: k[4],
    }))
  )

  const volumeData = computed(() =>
    klineData.value.map(k => ({
      time: k[0] / 1000,
      value: k[5],
      color: k[4] >= k[1] ? 'rgba(16, 185, 129, 0.5)' : 'rgba(239, 68, 68, 0.5)',
    }))
  )

  const fetchLatest = async () => {
    noMoreHistory.value = false
    if (isIndexSymbol(symbol.value)) {
      const end = new Date()
      const start = new Date()
      start.setFullYear(end.getFullYear() - 1)
      const res = await marketApi.getIndexHistory({
        symbol: symbol.value,
        timeframe: '1d',
        start_date: start.toISOString().slice(0, 10),
        end_date: end.toISOString().slice(0, 10),
      })
      klineData.value = res.data.data || []
      return
    }
    const data = await marketStore.getKlineData(symbol.value, timeframe.value)
    if (data) {
      klineData.value = data
    }
  }

  const loadMore = async () => {
    if (loadingMore.value || noMoreHistory.value || klineData.value.length === 0) return

    loadingMore.value = true
    try {
      const oldest = klineData.value[0]
      if (isIndexSymbol(symbol.value)) {
        const end = new Date(oldest[0] - 24 * 60 * 60 * 1000)
        const start = new Date(end)
        start.setFullYear(end.getFullYear() - 1)
        const res = await marketApi.getIndexHistory({
          symbol: symbol.value,
          timeframe: '1d',
          start_date: start.toISOString().slice(0, 10),
          end_date: end.toISOString().slice(0, 10),
        })
        const newKlines = res.data.data || []
        if (newKlines.length === 0) {
          noMoreHistory.value = true
          return
        }
        klineData.value = [...newKlines, ...klineData.value]
        return
      }

      const res = await marketApi.getHistory({
        symbol: symbol.value,
        timeframe: timeframe.value,
        end_ts: oldest[0],
        limit: 500,
      })

      const newKlines = res.data || []
      if (newKlines.length === 0) {
        noMoreHistory.value = true
        return
      }

      klineData.value = [...newKlines, ...klineData.value]
    } catch (e) {
      console.error('Load history failed', e)
    } finally {
      loadingMore.value = false
    }
  }

  watch(
    () => marketStore.klineCache[cacheKey.value]?.data,
    newData => {
      if (newData) {
        klineData.value = newData
      }
    }
  )

  watch(timeframe, () => {
    fetchLatest()
  })

  watch(symbol, () => {
    fetchLatest()
  })

  return {
    chartData,
    volumeData,
    loadingMore,
    noMoreHistory,
    fetchLatest,
    loadMore,
  }
}
