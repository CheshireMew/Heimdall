import { computed, onMounted, ref } from 'vue'

import { useMoney } from '@/composables/useMoney'
import { marketApi } from './api'

const formatNumber = (value: number | null | undefined, digits = 2) => {
  if (value === null || value === undefined || Number.isNaN(value)) return '--'
  return Number(value).toFixed(digits)
}

const formatSignedPercent = (value: number | null | undefined, digits = 2) => {
  if (value === null || value === undefined || Number.isNaN(value)) return '--'
  const numeric = Number(value)
  return `${numeric > 0 ? '+' : ''}${numeric.toFixed(digits)}%`
}

const changeClass = (value: number | null | undefined) => {
  if (value === null || value === undefined || Number.isNaN(value)) return 'text-slate-500 dark:text-slate-400'
  return value >= 0 ? 'text-emerald-500' : 'text-rose-500'
}

const mergeDerivatives = (tickerRows = [], markRows = []) => {
  const markMap = new Map(markRows.map((item) => [item.symbol, item]))
  return tickerRows
    .map((item) => {
      const mark = markMap.get(item.symbol)
      return {
        ...item,
        mark_price: mark?.mark_price ?? null,
        index_price: mark?.index_price ?? null,
        funding_rate_pct: mark?.last_funding_rate != null ? mark.last_funding_rate * 100 : null,
      }
    })
    .sort((left, right) => (right.quote_volume || 0) - (left.quote_volume || 0))
}

export function useBinanceMarketPage() {
  const { formatMoney, formatCompactMoney } = useMoney()
  const loading = ref(false)
  const error = ref('')
  const spotTicker = ref([])
  const usdmTicker = ref([])
  const usdmMark = ref([])
  const coinmTicker = ref([])
  const coinmMark = ref([])

  const gainers = computed(() =>
    [...spotTicker.value]
      .filter((item) => item.symbol?.endsWith('USDT'))
      .sort((left, right) => (right.price_change_pct || -999) - (left.price_change_pct || -999))
      .slice(0, 15))

  const losers = computed(() =>
    [...spotTicker.value]
      .filter((item) => item.symbol?.endsWith('USDT'))
      .sort((left, right) => (left.price_change_pct || 999) - (right.price_change_pct || 999))
      .slice(0, 15))

  const usdmRows = computed(() => mergeDerivatives(usdmTicker.value, usdmMark.value).slice(0, 15))
  const coinmRows = computed(() => mergeDerivatives(coinmTicker.value, coinmMark.value).slice(0, 15))

  const summaryCards = computed(() => {
    const bestGainer = gainers.value[0]
    const worstLoser = losers.value[0]
    const usdmFunding = [...usdmRows.value].sort((left, right) => Math.abs(right.funding_rate_pct || 0) - Math.abs(left.funding_rate_pct || 0))[0]
    const coinmFunding = [...coinmRows.value].sort((left, right) => Math.abs(right.funding_rate_pct || 0) - Math.abs(left.funding_rate_pct || 0))[0]

    return [
      {
        label: 'Spot Gainer',
        primary: bestGainer?.symbol || '--',
        secondary: formatSignedPercent(bestGainer?.price_change_pct),
        tone: changeClass(bestGainer?.price_change_pct),
      },
      {
        label: 'Spot Loser',
        primary: worstLoser?.symbol || '--',
        secondary: formatSignedPercent(worstLoser?.price_change_pct),
        tone: changeClass(worstLoser?.price_change_pct),
      },
      {
        label: 'USDM Funding',
        primary: usdmFunding?.symbol || '--',
        secondary: formatSignedPercent(usdmFunding?.funding_rate_pct, 4),
        tone: changeClass(usdmFunding?.funding_rate_pct),
      },
      {
        label: 'COINM Funding',
        primary: coinmFunding?.symbol || '--',
        secondary: formatSignedPercent(coinmFunding?.funding_rate_pct, 4),
        tone: changeClass(coinmFunding?.funding_rate_pct),
      },
    ]
  })

  const fetchData = async () => {
    loading.value = true
    error.value = ''
    try {
      const [spotRes, usdmTickerRes, usdmMarkRes, coinmTickerRes, coinmMarkRes] = await Promise.all([
        marketApi.getBinanceSpotTicker24h(),
        marketApi.getBinanceUsdmTicker24h(),
        marketApi.getBinanceUsdmMarkPrice(),
        marketApi.getBinanceCoinmTicker24h(),
        marketApi.getBinanceCoinmMarkPrice(),
      ])
      spotTicker.value = spotRes.data?.items || []
      usdmTicker.value = usdmTickerRes.data?.items || []
      usdmMark.value = usdmMarkRes.data?.items || []
      coinmTicker.value = coinmTickerRes.data?.items || []
      coinmMark.value = coinmMarkRes.data?.items || []
    } catch (err) {
      console.error('Failed to load Binance market page', err)
      error.value = 'Failed to load Binance market data.'
    } finally {
      loading.value = false
    }
  }

  onMounted(fetchData)

  const formatCompact = (value: number | null | undefined) => formatCompactMoney(value, 'USDT')
  const formatPrice = (value: number | null | undefined) => {
    if (value === null || value === undefined || Number.isNaN(value)) return '--'
    return formatMoney(value, 'USDT', { maximumFractionDigits: value >= 100 ? 2 : 6 })
  }

  return {
    loading,
    error,
    gainers,
    losers,
    usdmRows,
    coinmRows,
    summaryCards,
    fetchData,
    formatNumber,
    formatSignedPercent,
    formatCompact,
    formatPrice,
    changeClass,
  }
}
