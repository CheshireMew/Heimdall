import { computed, onMounted, ref, watch } from 'vue'

import { useMoney } from '@/composables/useMoney'
import { marketApi } from './api'
import type {
  BinanceRwaDynamicResponse,
  BinanceRwaKlineItemResponse,
  BinanceRwaMarketStatusResponse,
  BinanceRwaMetaResponse,
  BinanceRwaSymbolItemResponse,
} from '@/types'

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
  const rows = ref<BinanceRwaSymbolItemResponse[]>([])
  const selectedKey = ref('')
  const marketStatus = ref<BinanceRwaMarketStatusResponse | null>(null)
  const meta = ref<BinanceRwaMetaResponse | null>(null)
  const assetStatus = ref<BinanceRwaMarketStatusResponse | null>(null)
  const dynamic = ref<BinanceRwaDynamicResponse | null>(null)
  const kline = ref<BinanceRwaKlineItemResponse[]>([])

  const selectedItem = computed(() => rows.value.find((item) => `${item.chain_id}:${item.contract_address}` === selectedKey.value) || null)

  const chartData = computed(() =>
    (kline.value || []).map((item) => ({
      time: Math.floor((item.open_time || 0) / 1000),
      open: Number(item.open || 0),
      high: Number(item.high || 0),
      low: Number(item.low || 0),
      close: Number(item.close || 0),
    })))

  const summaryCards = computed(() => [
    {
      label: 'Ticker',
      value: dynamic.value?.ticker || selectedItem.value?.ticker || '--',
      hint: dynamic.value?.symbol || selectedItem.value?.symbol || '',
    },
    {
      label: 'Token Price',
      value: formatPrice(readDynamicNumber('token_info', 'price')),
      hint: formatPercent(readDynamicNumber('token_info', 'priceChangePct24h')),
    },
    {
      label: 'Stock Market Cap',
      value: formatCompact(readDynamicNumber('stock_info', 'marketCap')),
      hint: formatPrice(readDynamicNumber('stock_info', 'price')),
    },
    {
      label: 'Session',
      value: assetStatus.value?.marketStatus || marketStatus.value?.reasonCode || '--',
      hint: assetStatus.value?.reasonMsg || marketStatus.value?.reasonMsg || '',
    },
  ])

  const fetchDetail = async () => {
    if (!selectedItem.value) return
    const chainId = selectedItem.value.chain_id || ''
    const contractAddress = selectedItem.value.contract_address || ''
    if (!chainId || !contractAddress) return
    detailLoading.value = true
    try {
      const params = {
        chain_id: chainId,
        contract_address: contractAddress,
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

  const readDynamicNumber = (section: 'token_info' | 'stock_info', key: string) => {
    const value = dynamic.value?.[section]?.[key]
    const numeric = Number(value)
    return Number.isFinite(numeric) ? numeric : null
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
