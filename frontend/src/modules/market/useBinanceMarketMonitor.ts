import { computed, ref, watch } from 'vue'

import type {
  BinanceBreakoutMonitorResponse,
  BinanceMarkPriceItemResponse,
  BinanceTickerStatsItemResponse,
} from '../../types/market'
import { marketApi } from './api'
import type { BinanceMarketSnapshot, ContractBoardRow, ContractSortField, ContractSortState, MarketFilter, MonitorMode, SortDirection } from './binanceMarketShared'
import {
  EMPTY_RESPONSE,
  formatLoadFailure,
  mergeDerivatives,
  sortContractRows,
  sortRowsByMetric,
  toItemKey,
} from './binanceMarketShared'

export function useBinanceMarketMonitor(snapshot: BinanceMarketSnapshot) {
  const loading = ref(false)
  const error = ref('')
  const minRisePct = ref(snapshot.minRisePct)
  const mode = ref<MonitorMode>(snapshot.mode)
  const marketFilter = ref<MarketFilter>(snapshot.marketFilter)
  const autoRefresh = ref(snapshot.autoRefresh)
  const spotSortDirection = ref<SortDirection>(snapshot.spotSortDirection)
  const contractSort = ref<ContractSortState>({
    field: snapshot.contractSortField,
    direction: snapshot.contractSortDirection,
  })
  const monitor = ref<BinanceBreakoutMonitorResponse>({ ...EMPTY_RESPONSE })
  const spotTicker = ref<BinanceTickerStatsItemResponse[]>([])
  const usdmTicker = ref<BinanceTickerStatsItemResponse[]>([])
  const usdmMark = ref<BinanceMarkPriceItemResponse[]>([])
  const selectedKey = ref(snapshot.selectedKey)
  let refreshTimer: ReturnType<typeof setInterval> | null = null
  let thresholdTimer: ReturnType<typeof setTimeout> | null = null

  const items = computed(() => monitor.value.items || [])
  const spotRows = computed(() => (
    sortRowsByMetric(
      spotTicker.value.filter((item) => item.symbol?.endsWith('USDT')),
      (row) => row.price_change_pct,
      spotSortDirection.value,
    )
  ))
  const contractSourceItems = computed<ContractBoardRow[]>(() => (
    mergeDerivatives(usdmTicker.value, usdmMark.value).map((item) => ({
      ...item,
      market: 'usdm',
      market_label: '合约',
    }))
  ))
  const contractRows = computed(() => sortContractRows(contractSourceItems.value, contractSort.value))
  const filteredItems = computed(() => items.value.filter((item) => {
    if (marketFilter.value !== 'all' && item.market !== marketFilter.value) return false
    if (mode.value === 'natural' && !item.structure_ok) return false
    if (mode.value === 'momentum' && !item.momentum_ok) return false
    if (mode.value === 'focus' && item.verdict !== '优先关注') return false
    return true
  }))
  const selectedItem = computed(() => (
    filteredItems.value.find((item) => toItemKey(item) === selectedKey.value)
    || filteredItems.value[0]
    || items.value[0]
    || null
  ))
  const summaryCards = computed(() => {
    const summary = monitor.value.summary ?? EMPTY_RESPONSE.summary!
    return [
      { label: '入选标的', value: String(summary.monitored_count || 0), hint: `>${monitor.value.min_rise_pct || minRisePct.value}%` },
      { label: '走势自然', value: String(summary.natural_count || 0), hint: '节奏更顺' },
      { label: '仍有动能', value: String(summary.momentum_count || 0), hint: '还在续推' },
      { label: '优先关注', value: String(summary.focus_count || 0), hint: '结构 + 动能' },
    ]
  })

  const fetchData = async () => {
    loading.value = true
    error.value = ''
    try {
      const response = await marketApi.getBinanceMarketPage({
        min_rise_pct: minRisePct.value,
        limit: 24,
        quote_asset: 'USDT',
      })
      const payload = response.data
      monitor.value = payload?.monitor || { ...EMPTY_RESPONSE }
      spotTicker.value = payload?.spot_ticker?.items || []
      usdmTicker.value = payload?.usdm_ticker?.items || []
      usdmMark.value = payload?.usdm_mark?.items || []
      error.value = formatLoadFailure([...(payload?.load_errors || [])])
    } catch (requestError) {
      monitor.value = { ...EMPTY_RESPONSE }
      spotTicker.value = []
      usdmTicker.value = []
      usdmMark.value = []
      error.value = '异动监控加载失败'
      console.error('Failed to load Binance market page', requestError)
    } finally {
      loading.value = false
    }
  }

  const startAutoRefresh = () => {
    if (refreshTimer) clearInterval(refreshTimer)
    if (!autoRefresh.value) return
    refreshTimer = setInterval(() => {
      void fetchData()
    }, 60000)
  }

  const stopAutoRefresh = () => {
    if (refreshTimer) {
      clearInterval(refreshTimer)
      refreshTimer = null
    }
    if (thresholdTimer) {
      clearTimeout(thresholdTimer)
      thresholdTimer = null
    }
  }

  watch(autoRefresh, startAutoRefresh)
  watch(minRisePct, () => {
    if (thresholdTimer) clearTimeout(thresholdTimer)
    thresholdTimer = setTimeout(() => {
      void fetchData()
    }, 350)
  })

  const toggleContractSort = (field: ContractSortField) => {
    if (contractSort.value.field === field) {
      contractSort.value = {
        ...contractSort.value,
        direction: contractSort.value.direction === 'desc' ? 'asc' : 'desc',
      }
      return
    }
    contractSort.value = { field, direction: 'desc' }
  }

  const toggleSpotSort = () => {
    spotSortDirection.value = spotSortDirection.value === 'desc' ? 'asc' : 'desc'
  }

  return {
    loading,
    error,
    minRisePct,
    mode,
    marketFilter,
    autoRefresh,
    monitor,
    items,
    filteredItems,
    spotRows,
    spotSortDirection,
    contractRows,
    contractSort,
    selectedKey,
    selectedItem,
    summaryCards,
    fetchData,
    startAutoRefresh,
    stopAutoRefresh,
    toggleSpotSort,
    toggleContractSort,
  }
}
