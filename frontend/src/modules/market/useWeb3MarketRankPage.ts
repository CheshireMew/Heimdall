import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { useTheme } from '@/composables/useTheme'
import { formatAdaptivePrice, formatCompactNumber, formatSignedPercent } from '@/modules/format'
import { marketApi } from './api'
import type {
  BinanceWeb3AddressPnlItemResponse,
} from '../../types/market'
import { formatScore, sortDirectionIcon } from './binanceMarketShared'
import { useWeb3HeatRankPanel } from './useWeb3HeatRankPanel'
import {
  WEB3_ALL_CHAIN_ID,
  WEB3_SUPPORTED_CHAIN_OPTIONS,
  web3ApiChainId,
  WEB3_KLINE_INTERVALS,
} from './web3MarketShared'

const changeClass = (value: number | null | undefined) => {
  if (value === null || value === undefined || Number.isNaN(value)) return 'text-slate-500 dark:text-slate-400'
  return value >= 0 ? 'text-emerald-500' : 'text-rose-500'
}

export function useWeb3MarketRankPage() {
  const { t } = useI18n()
  const { theme } = useTheme()
  const loading = ref(false)
  const errorKey = ref('')
  const error = computed(() => (errorKey.value ? t(errorKey.value) : ''))
  const chainId = ref(WEB3_ALL_CHAIN_ID)
  const heatRank = useWeb3HeatRankPanel(chainId)
  const addressPnl = ref<BinanceWeb3AddressPnlItemResponse[]>([])

  const chainOptions = computed(() => (
    [
      { label: t('web3Rank.allChains'), value: WEB3_ALL_CHAIN_ID },
      ...WEB3_SUPPORTED_CHAIN_OPTIONS,
    ]
  ))

  const summaryCards = computed(() => [
    {
      label: t('web3Rank.summary.heatLeader'),
      primary: heatRank.web3HeatRank.value[0]?.symbol || '--',
      secondary: formatScore(heatRank.web3HeatRank.value[0]?.heat_score),
      tone: 'text-cyan-500',
    },
    {
      label: t('web3Rank.summary.socialSignal'),
      primary: heatRank.web3HeatRank.value[0]?.sentiment || '--',
      secondary: formatCompactNumber(heatRank.web3HeatRank.value[0]?.metrics?.social_hype),
      tone: 'text-violet-500',
    },
    {
      label: t('web3Rank.summary.smartMoney'),
      primary: heatRank.web3HeatRank.value[0]?.symbol || '--',
      secondary: formatCompactNumber(heatRank.web3HeatRank.value[0]?.metrics?.smart_money_inflow),
      tone: 'text-cyan-500',
    },
    {
      label: t('web3Rank.summary.pnlBoard'),
      primary: addressPnl.value[0]?.address_label || addressPnl.value[0]?.address || '--',
      secondary: formatCompactNumber(addressPnl.value[0]?.realized_pnl),
      tone: changeClass(addressPnl.value[0]?.realized_pnl),
    },
  ])

  const web3ChartColors = computed(() => {
    const isDark = theme.value === 'dark'
    return {
      bg: isDark ? '#020617' : '#ffffff',
      grid: isDark ? '#1e293b' : '#e2e8f0',
      text: isDark ? '#94a3b8' : '#475569',
      upColor: '#10b981',
      downColor: '#ef4444',
    }
  })

  const fetchData = async () => {
    loading.value = true
    errorKey.value = ''
    try {
      const selectedChainId = web3ApiChainId(chainId.value)
      const pnlRes = await marketApi.getBinanceWeb3AddressPnlRank({ chain_id: selectedChainId || '56', page_size: 10 })
      addressPnl.value = pnlRes.data?.items || []
    } catch (err) {
      console.error('Failed to load Binance Web3 rank page', err)
      errorKey.value = 'web3Rank.loadFailed'
    } finally {
      loading.value = false
    }
  }

  const handleEscape = (event: KeyboardEvent) => {
    if (event.key === 'Escape' && heatRank.web3Dialog.value.open) {
      heatRank.closeWeb3Token()
    }
  }

  watch(chainId, fetchData)

  onMounted(() => {
    window.addEventListener('keydown', handleEscape)
    void fetchData()
    void heatRank.fetchWeb3HeatRank()
  })

  onUnmounted(() => {
    window.removeEventListener('keydown', handleEscape)
  })

  return {
    loading,
    error,
    chainId,
    chainOptions,
    addressPnl,
    web3HeatRank: heatRank.web3HeatRank,
    web3Loading: heatRank.web3Loading,
    web3Error: heatRank.web3Error,
    web3Dialog: heatRank.web3Dialog,
    web3Dynamic: heatRank.web3Dynamic,
    web3Audit: heatRank.web3Audit,
    web3DetailLoading: heatRank.web3DetailLoading,
    web3DetailError: heatRank.web3DetailError,
    web3KlineInterval: heatRank.web3KlineInterval,
    web3KlineIntervals: WEB3_KLINE_INTERVALS,
    web3ChartData: heatRank.web3ChartData,
    web3VolumeData: heatRank.web3VolumeData,
    web3ChartColors,
    web3Sort: heatRank.web3Sort,
    fetchWeb3HeatRank: heatRank.fetchWeb3HeatRank,
    toggleWeb3Sort: heatRank.toggleWeb3Sort,
    openWeb3Token: heatRank.openWeb3Token,
    closeWeb3Token: heatRank.closeWeb3Token,
    summaryCards,
    fetchData,
    formatScore,
    formatPercent: formatSignedPercent,
    formatPrice: (value: number | null | undefined) => formatAdaptivePrice(value, 'USDT', '--'),
    formatCompact: formatCompactNumber,
    sortDirectionIcon,
    changeClass,
  }
}
