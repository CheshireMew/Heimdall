import { computed, onMounted, ref } from 'vue'

import { createPersistentPageSnapshot, PAGE_SNAPSHOT_KEYS } from '@/composables/pageSnapshot'
import { useTheme } from '@/composables/useTheme'
import {
  formatCompactCurrency,
  formatMoney,
  formatPercent,
  formatSignedPercent,
} from '@/modules/format'
import type { CryptoIndexConstituentResponse, CryptoIndexHistoryPointResponse, CryptoIndexResponse } from './contracts'
import { buildCryptoIndexSnapshot, createDefaultCryptoIndexSnapshot, normalizeCryptoIndexSnapshot } from './pageSnapshots'
import { useCryptoIndexStore } from './cryptoIndexStore'


export function useCryptoIndexPage() {
  const { theme } = useTheme()
  const cryptoIndexStore = useCryptoIndexStore()
  const pageSnapshot = createPersistentPageSnapshot(PAGE_SNAPSHOT_KEYS.cryptoIndex, normalizeCryptoIndexSnapshot, createDefaultCryptoIndexSnapshot())
  const restoredSnapshot = pageSnapshot.initial

  const basketSizes = [10, 20, 50]
  const topN = ref(restoredSnapshot.topN)
  const days = ref(restoredSnapshot.days)
  const data = computed<CryptoIndexResponse | null>(() => cryptoIndexStore.readCryptoIndex(topN.value, days.value))
  const error = computed(() => cryptoIndexStore.getCryptoIndexError(topN.value, days.value))
  const loading = computed(() => (
    cryptoIndexStore.isCryptoIndexLoading(topN.value, days.value)
    || (!data.value && !error.value)
  ))

  const chartColors = computed(() => {
    const isDark = theme.value === 'dark'
    return {
      bg: isDark ? '#0f172a' : '#f8fafc',
      grid: isDark ? '#334155' : '#dbeafe',
      text: isDark ? '#cbd5e1' : '#475569',
      upColor: '#06b6d4',
      downColor: '#0891b2',
    }
  })

  const summary = computed(() => data.value?.summary || null)
  const constituents = computed(() => data.value?.constituents || [])
  const basketMarketCap = computed(() => summary.value?.current_basket_market_cap || 0)
  const chartData = computed(() =>
    (data.value?.history || []).map((point: CryptoIndexHistoryPointResponse) => ({
      time: point.timestamp,
      value: point.index_value,
    })))

  const formatCurrency = (value: number | null | undefined) => (
    formatMoney(value, 'USD', { maximumFractionDigits: Number(value || 0) >= 1000 ? 0 : 2 }, '--')
  )

  const formatIndexCompactCurrency = (value: number | null | undefined) => formatCompactCurrency(value, 'USD')

  const formatIndexPercent = (value: number | null | undefined) => formatPercent(value, 2, { empty: '--' })

  const changeClass = (value: number | null | undefined) => {
    if (value === null || value === undefined) {
      return 'text-slate-500 dark:text-slate-400'
    }
    return value >= 0 ? 'text-emerald-500' : 'text-rose-500'
  }

  const weightOf = (coin: CryptoIndexConstituentResponse) => {
    if (!basketMarketCap.value || !coin.market_cap) {
      return 0
    }
    return (coin.market_cap / basketMarketCap.value) * 100
  }

  const summaryCards = computed(() => [
    {
      label: 'Index',
      value: summary.value ? summary.value.current_index_value.toFixed(2) : '--',
      hint: summary.value ? `${summary.value.common_start_date} -> now` : '',
    },
    {
      label: 'Basket Cap',
      value: formatIndexCompactCurrency(summary.value?.current_basket_market_cap),
      hint: `${topN.value} assets`,
    },
    {
      label: '24H',
      value: formatSignedPercent(summary.value?.basket_change_24h_pct),
      hint: 'weighted by market cap',
    },
    {
      label: 'BTC / ETH',
      value: summary.value
        ? `${formatIndexPercent(summary.value.btc_weight_pct)} / ${formatIndexPercent(summary.value.eth_weight_pct)}`
        : '--',
      hint: 'basket weights',
    },
  ])

  const fetchData = async (options: { force?: boolean } = {}) => {
    await cryptoIndexStore.getCryptoIndex(topN.value, days.value, options)
  }

  const refresh = async () => {
    await fetchData({ force: true })
  }

  const setTopN = (size: number) => {
    topN.value = size
    void fetchData()
  }

  onMounted(() => {
    fetchData()
  })

  pageSnapshot.bind(
    [topN, days],
    () => buildCryptoIndexSnapshot({
      topN: topN.value,
      days: days.value,
    }),
  )

  return {
    basketSizes,
    topN,
    days,
    loading,
    error,
    data,
    chartColors,
    summary,
    constituents,
    chartData,
    summaryCards,
    setTopN,
    fetchData,
    refresh,
    weightOf,
    formatCurrency,
    formatCompactCurrency: formatIndexCompactCurrency,
    formatPercent: formatIndexPercent,
    formatSignedPercent,
    changeClass,
  }
}


