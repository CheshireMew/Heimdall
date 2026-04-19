import { computed, onUnmounted, ref, watch, type Ref } from 'vue'
import { marketApi } from './api'
import { useMarketStore } from './store'
import { isIndexSymbol } from './symbolCatalog'
import type { OhlcvPointResponse } from '@/types'

const REFRESH_INTERVAL_MS = 5000
const LIVE_TAIL_LIMIT = 16

type UseKlineSeriesOptions = {
  enabled?: Ref<boolean>
}

export function useKlineSeries(symbol: Ref<string>, timeframe: Ref<string>, options: UseKlineSeriesOptions = {}) {
  const marketStore = useMarketStore()
  const indexKlineData = ref<OhlcvPointResponse[]>([])
  const loadingMore = ref(false)
  const noMoreHistory = ref(false)
  const enabled = computed(() => options.enabled?.value ?? true)
  let tailRefreshPending = false
  let refreshTimer: number | null = null

  const cacheKey = computed(() => `${symbol.value}:${timeframe.value}`)
  const klineData = computed(() => (
    isIndexSymbol(symbol.value)
      ? indexKlineData.value
      : marketStore.klineCache[cacheKey.value]?.data || []
  ))

  const chartData = computed(() =>
    klineData.value.map(k => ({
      time: k.timestamp / 1000,
      open: k.open,
      high: k.high,
      low: k.low,
      close: k.close,
    }))
  )

  const volumeData = computed(() =>
    klineData.value.map(k => ({
      time: k.timestamp / 1000,
      value: k.volume,
      color: k.close >= k.open ? 'rgba(16, 185, 129, 0.5)' : 'rgba(239, 68, 68, 0.5)',
    }))
  )

  const fetchLatest = async (options: { force?: boolean } = {}) => {
    const requestSymbol = symbol.value
    const requestTimeframe = timeframe.value
    if (!enabled.value || !requestSymbol || !requestTimeframe) {
      indexKlineData.value = []
      return
    }
    noMoreHistory.value = false
    if (isIndexSymbol(requestSymbol)) {
      const end = new Date()
      const start = new Date()
      start.setFullYear(end.getFullYear() - 1)
      const res = await marketApi.getIndexHistory({
        symbol: requestSymbol,
        timeframe: '1d',
        start_date: start.toISOString().slice(0, 10),
        end_date: end.toISOString().slice(0, 10),
      })
      if (requestSymbol !== symbol.value || requestTimeframe !== timeframe.value) return
      indexKlineData.value = res.data.data || []
      return
    }
    const data = await marketStore.getKlineData(requestSymbol, requestTimeframe, 1000, options)
    if (requestSymbol !== symbol.value || requestTimeframe !== timeframe.value) return
    if (data) {
      marketStore.setKlineHistory(requestSymbol, requestTimeframe, data, 1000)
    }
    if (!isIndexSymbol(requestSymbol)) {
      refreshTail().catch(error => {
        console.error('Initial realtime refresh failed', error)
      })
    }
  }

  const refreshTail = async () => {
    const requestSymbol = symbol.value
    const requestTimeframe = timeframe.value
    const res = await marketApi.getPriceSeriesTail({
      symbol: requestSymbol,
      timeframe: requestTimeframe,
      limit: LIVE_TAIL_LIMIT,
    })
    if (requestSymbol !== symbol.value || requestTimeframe !== timeframe.value) return
    const tail = res.data.kline_data || []
    if (tail.length === 0) return
    marketStore.applyKlineTail(requestSymbol, requestTimeframe, tail, 1000)
  }

  const stopAutoRefresh = () => {
    if (refreshTimer !== null) {
      window.clearInterval(refreshTimer)
      refreshTimer = null
    }
  }

  const startAutoRefresh = () => {
    stopAutoRefresh()
    if (!enabled.value || !symbol.value || !timeframe.value) return
    refreshTimer = window.setInterval(() => {
      if (isIndexSymbol(symbol.value) || tailRefreshPending) return
      tailRefreshPending = true
      refreshTail().catch(error => {
        console.error('Realtime refresh failed', error)
      }).finally(() => {
        tailRefreshPending = false
      })
    }, REFRESH_INTERVAL_MS)
  }

  const loadMore = async () => {
    if (loadingMore.value || noMoreHistory.value || klineData.value.length === 0) return

    loadingMore.value = true
    try {
      const requestSymbol = symbol.value
      const requestTimeframe = timeframe.value
      const oldest = klineData.value[0]
      if (isIndexSymbol(requestSymbol)) {
        const end = new Date(oldest.timestamp - 24 * 60 * 60 * 1000)
        const start = new Date(end)
        start.setFullYear(end.getFullYear() - 1)
        const res = await marketApi.getIndexHistory({
          symbol: requestSymbol,
          timeframe: '1d',
          start_date: start.toISOString().slice(0, 10),
          end_date: end.toISOString().slice(0, 10),
        })
        if (requestSymbol !== symbol.value || requestTimeframe !== timeframe.value) return
        const newKlines = res.data.data || []
        if (newKlines.length === 0) {
          noMoreHistory.value = true
          return
        }
        indexKlineData.value = [...newKlines, ...indexKlineData.value]
        return
      }

      const res = await marketApi.getPriceSeriesWindow({
        symbol: requestSymbol,
        timeframe: requestTimeframe,
        end_ts: oldest.timestamp,
        limit: 500,
      })
      if (requestSymbol !== symbol.value || requestTimeframe !== timeframe.value) return

      const newKlines = res.data.items || []
      if (newKlines.length === 0) {
        noMoreHistory.value = true
        return
      }

      marketStore.prependKlineHistory(requestSymbol, requestTimeframe, newKlines)
    } catch (e) {
      console.error('Load history failed', e)
    } finally {
      loadingMore.value = false
    }
  }

  watch([symbol, timeframe, enabled], () => {
    stopAutoRefresh()
    tailRefreshPending = false
    if (!enabled.value || !symbol.value || !timeframe.value) {
      indexKlineData.value = []
      noMoreHistory.value = false
      return
    }
    if (isIndexSymbol(symbol.value)) {
      indexKlineData.value = []
    }
    void fetchLatest()
    startAutoRefresh()
  }, { immediate: true })

  onUnmounted(() => {
    stopAutoRefresh()
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
