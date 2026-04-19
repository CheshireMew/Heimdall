import { computed, ref } from 'vue'

import { useTheme } from '@/composables/useTheme'
import type {
  BinanceBreakoutMonitorItemResponse,
} from '@/types'
import { toSlashMarketSymbol } from './symbolCatalog'
import { displaySymbol, type ChartDialogState } from './binanceMarketShared'
import { useKlineSeries } from './useKlineSeries'

export function useBinanceSymbolChart() {
  const { theme } = useTheme()
  const chartDialog = ref<ChartDialogState>({
    open: false,
    rawSymbol: '',
    marketLabel: '',
  })
  const chartTimeframe = ref('15m')
  const chartTimeframes = ['5m', '15m', '1h', '4h', '1d']

  const chartSymbol = computed(() => (
    toSlashMarketSymbol(chartDialog.value.rawSymbol, 'USDT')
  ))
  const chartTitle = computed(() => displaySymbol(chartDialog.value.rawSymbol))
  const chartMarketLabel = computed(() => chartDialog.value.marketLabel || '市场')
  const chartEnabled = computed(() => chartDialog.value.open && Boolean(chartSymbol.value))
  const chartColors = computed(() => {
    const isDark = theme.value === 'dark'
    return {
      bg: isDark ? '#020617' : '#ffffff',
      grid: isDark ? '#1e293b' : '#e2e8f0',
      text: isDark ? '#94a3b8' : '#475569',
      upColor: '#10b981',
      downColor: '#ef4444',
    }
  })
  const {
    chartData,
    volumeData,
    loadingMore: chartLoadingMore,
    loadMore: loadMoreChartHistory,
  } = useKlineSeries(chartSymbol, chartTimeframe, { enabled: chartEnabled })

  const openChart = (
    item: Pick<BinanceBreakoutMonitorItemResponse, 'symbol'> & Partial<Pick<BinanceBreakoutMonitorItemResponse, 'market' | 'market_label'>>,
  ) => {
    const rawSymbol = String(item.symbol || '').trim().toUpperCase()
    if (!rawSymbol) return
    chartDialog.value = {
      open: true,
      rawSymbol,
      marketLabel: item.market_label || (item.market === 'usdm' ? '合约' : '现货'),
    }
  }

  const closeChart = () => {
    chartDialog.value = {
      ...chartDialog.value,
      open: false,
    }
  }

  return {
    chartDialog,
    chartSymbol,
    chartTitle,
    chartMarketLabel,
    chartTimeframe,
    chartTimeframes,
    chartColors,
    chartData,
    volumeData,
    chartLoadingMore,
    openChart,
    closeChart,
    loadMoreChartHistory,
  }
}
