import { onMounted, onUnmounted, watch } from 'vue'

import { bindPageSnapshot, createPageSnapshot, PAGE_SNAPSHOT_KEYS, readBoolean, readNumber, readString } from '@/composables/pageSnapshot'
import { useMoney } from '@/composables/useMoney'
import type { BinanceBreakoutMonitorItemResponse } from '@/types'
import {
  normalizeContractSortField,
  normalizeMarketFilter,
  normalizeMode,
  normalizeSnapshot,
  normalizeSortDirection,
  toItemKey,
  WEB3_CHAIN_OPTIONS,
  WEB3_KLINE_INTERVALS,
  displaySymbol,
  formatScore,
  formatSigned,
  formatTime,
  valueTone,
  verdictTone,
  createDefaultSnapshot,
} from './binanceMarketShared'
import { useBinanceMarketMonitor } from './useBinanceMarketMonitor'
import { useBinanceSymbolChart } from './useBinanceSymbolChart'
import { useBinanceWeb3Panel } from './useBinanceWeb3Panel'

export function useBinanceMarketPage() {
  const { formatMoney, formatCompactMoney } = useMoney()
  const pageSnapshot = createPageSnapshot(PAGE_SNAPSHOT_KEYS.binanceMarket, normalizeSnapshot, createDefaultSnapshot())
  const restoredSnapshot = pageSnapshot.load()
  const market = useBinanceMarketMonitor(restoredSnapshot)
  const web3 = useBinanceWeb3Panel(restoredSnapshot.web3ChainId)
  const chart = useBinanceSymbolChart()

  const handleEscape = (event: KeyboardEvent) => {
    if (event.key === 'Escape' && chart.chartDialog.value.open) {
      chart.closeChart()
    }
    if (event.key === 'Escape' && web3.web3Dialog.value.open) {
      web3.closeWeb3Token()
    }
  }

  const openChart = (
    item: Pick<BinanceBreakoutMonitorItemResponse, 'symbol'> & Partial<Pick<BinanceBreakoutMonitorItemResponse, 'market' | 'market_label'>>,
  ) => {
    if (item.market && item.symbol) {
      market.selectedKey.value = `${item.market}:${item.symbol}`
    }
    chart.openChart(item)
  }

  watch([market.filteredItems, market.items], () => {
    market.selectedKey.value = toItemKey(market.selectedItem.value)
  })

  onMounted(async () => {
    window.addEventListener('keydown', handleEscape)
    await Promise.all([
      market.fetchData(),
      web3.fetchWeb3HeatRank(),
    ])
    market.startAutoRefresh()
  })

  onUnmounted(() => {
    window.removeEventListener('keydown', handleEscape)
    market.stopAutoRefresh()
  })

  bindPageSnapshot(
    [
      market.minRisePct,
      market.mode,
      market.marketFilter,
      market.autoRefresh,
      market.spotSortDirection,
      market.contractSort,
      market.selectedKey,
      web3.web3ChainId,
    ],
    () => ({
      minRisePct: readNumber(market.minRisePct.value, 5),
      mode: normalizeMode(market.mode.value),
      marketFilter: normalizeMarketFilter(market.marketFilter.value),
      autoRefresh: readBoolean(market.autoRefresh.value, true),
      spotSortDirection: normalizeSortDirection(market.spotSortDirection.value),
      contractSortField: normalizeContractSortField(market.contractSort.value.field),
      contractSortDirection: normalizeSortDirection(market.contractSort.value.direction),
      selectedKey: readString(market.selectedKey.value, ''),
      web3ChainId: readString(web3.web3ChainId.value, '56'),
    }),
    pageSnapshot.save,
  )

  const formatPrice = (value: number | null | undefined) => {
    if (value === null || value === undefined || Number.isNaN(value)) return '--'
    return formatMoney(value, 'USDT', { maximumFractionDigits: value >= 100 ? 2 : 6 })
  }

  const formatCompact = (value: number | null | undefined) => formatCompactMoney(value, 'USDT')

  return {
    loading: market.loading,
    error: market.error,
    minRisePct: market.minRisePct,
    mode: market.mode,
    marketFilter: market.marketFilter,
    autoRefresh: market.autoRefresh,
    monitor: market.monitor,
    items: market.items,
    filteredItems: market.filteredItems,
    spotRows: market.spotRows,
    spotSortDirection: market.spotSortDirection,
    contractRows: market.contractRows,
    contractSort: market.contractSort,
    selectedItem: market.selectedItem,
    selectedKey: market.selectedKey,
    summaryCards: market.summaryCards,
    fetchData: market.fetchData,
    toggleSpotSort: market.toggleSpotSort,
    toggleContractSort: market.toggleContractSort,
    web3ChainId: web3.web3ChainId,
    web3ChainOptions: WEB3_CHAIN_OPTIONS,
    web3HeatRank: web3.web3HeatRank,
    web3Loading: web3.web3Loading,
    web3Error: web3.web3Error,
    web3Dialog: web3.web3Dialog,
    web3Dynamic: web3.web3Dynamic,
    web3Audit: web3.web3Audit,
    web3DetailLoading: web3.web3DetailLoading,
    web3DetailError: web3.web3DetailError,
    web3KlineInterval: web3.web3KlineInterval,
    web3KlineIntervals: WEB3_KLINE_INTERVALS,
    web3ChartData: web3.web3ChartData,
    web3VolumeData: web3.web3VolumeData,
    fetchWeb3HeatRank: web3.fetchWeb3HeatRank,
    openWeb3Token: web3.openWeb3Token,
    closeWeb3Token: web3.closeWeb3Token,
    chartDialog: chart.chartDialog,
    chartSymbol: chart.chartSymbol,
    chartTitle: chart.chartTitle,
    chartMarketLabel: chart.chartMarketLabel,
    chartTimeframe: chart.chartTimeframe,
    chartTimeframes: chart.chartTimeframes,
    chartColors: chart.chartColors,
    chartData: chart.chartData,
    volumeData: chart.volumeData,
    chartLoadingMore: chart.chartLoadingMore,
    openChart,
    closeChart: chart.closeChart,
    loadMoreChartHistory: chart.loadMoreChartHistory,
    formatSigned,
    formatScore,
    formatTime,
    formatPrice,
    formatCompact,
    displaySymbol,
    valueTone,
    verdictTone,
    toItemKey,
  }
}
