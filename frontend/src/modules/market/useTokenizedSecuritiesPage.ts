import { computed, onMounted, ref, watch } from 'vue'

import { useMoney } from '@/composables/useMoney'
import { marketApi } from './api'

const formatPercent = (value: number | string | null | undefined, digits = 2) => {
  if (value === null || value === undefined || value === '' || Number.isNaN(Number(value))) return '--'
  const numeric = Number(value)
  return `${numeric > 0 ? '+' : ''}${numeric.toFixed(digits)}%`
}

export function useTokenizedSecuritiesPage() {
  const { formatMoney, formatCompactMoney } = useMoney()
  const loading = ref(false)
  const detailLoading = ref(false)
  const error = ref('')
  const rows = ref([])
  const selectedKey = ref('')
  const marketStatus = ref(null)
  const meta = ref(null)
  const assetStatus = ref(null)
  const dynamic = ref(null)
  const kline = ref([])

  const selectedItem = computed(() => rows.value.find((item) => `${item.chain_id}:${item.contract_address}` === selectedKey.value) || null)

  const chartData = computed(() =>
    (kline.value || []).map((item) => ({
      time: Math.floor((item.open_time || 0) / 1000),
      open: item.open,
      high: item.high,
      low: item.low,
      close: item.close,
    })))

  const summaryCards = computed(() => [
    {
      label: 'Ticker',
      value: dynamic.value?.ticker || selectedItem.value?.ticker || '--',
      hint: dynamic.value?.symbol || selectedItem.value?.symbol || '',
    },
    {
      label: 'Token Price',
      value: formatPrice(dynamic.value?.token_info?.price),
      hint: formatPercent(dynamic.value?.token_info?.priceChangePct24h),
    },
    {
      label: 'Stock Market Cap',
      value: formatCompact(dynamic.value?.stock_info?.marketCap),
      hint: formatPrice(dynamic.value?.stock_info?.price),
    },
    {
      label: 'Session',
      value: assetStatus.value?.marketStatus || marketStatus.value?.reasonCode || '--',
      hint: assetStatus.value?.reasonMsg || marketStatus.value?.reasonMsg || '',
    },
  ])

  const fetchDetail = async () => {
    if (!selectedItem.value) return
    detailLoading.value = true
    try {
      const params = {
        chain_id: selectedItem.value.chain_id,
        contract_address: selectedItem.value.contract_address,
      }
      const [metaRes, assetStatusRes, dynamicRes, klineRes] = await Promise.all([
        marketApi.getBinanceRwaMeta(params),
        marketApi.getBinanceRwaAssetMarketStatus(params),
        marketApi.getBinanceRwaDynamic(params),
        marketApi.getBinanceRwaKline({ ...params, interval: '1d', limit: 120 }),
      ])
      meta.value = metaRes.data
      assetStatus.value = assetStatusRes.data
      dynamic.value = dynamicRes.data
      kline.value = klineRes.data?.items || []
    } catch (err) {
      console.error('Failed to load tokenized security detail', err)
      error.value = 'Failed to load tokenized security detail.'
    } finally {
      detailLoading.value = false
    }
  }

  const fetchData = async () => {
    loading.value = true
    error.value = ''
    try {
      const [symbolsRes, marketStatusRes] = await Promise.all([
        marketApi.getBinanceRwaSymbols({ platform_type: 1 }),
        marketApi.getBinanceRwaMarketStatus(),
      ])
      rows.value = symbolsRes.data?.items || []
      marketStatus.value = marketStatusRes.data || null
      if (!selectedKey.value && rows.value.length) {
        selectedKey.value = `${rows.value[0].chain_id}:${rows.value[0].contract_address}`
      }
    } catch (err) {
      console.error('Failed to load tokenized securities page', err)
      error.value = 'Failed to load tokenized securities.'
    } finally {
      loading.value = false
    }
  }

  watch(selectedKey, fetchDetail)
  onMounted(fetchData)

  const formatPrice = (value: number | string | null | undefined) => {
    if (value === null || value === undefined || value === '' || Number.isNaN(Number(value))) return '--'
    return formatMoney(Number(value), 'USD', { maximumFractionDigits: 4 })
  }

  const formatCompact = (value: number | string | null | undefined) => {
    if (value === null || value === undefined || value === '' || Number.isNaN(Number(value))) return '--'
    return formatCompactMoney(Number(value), 'USD')
  }

  return {
    loading,
    detailLoading,
    error,
    rows,
    selectedKey,
    selectedItem,
    marketStatus,
    meta,
    assetStatus,
    dynamic,
    chartData,
    summaryCards,
    fetchData,
    formatCompact,
    formatPercent,
    formatPrice,
  }
}
