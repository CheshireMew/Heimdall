import { computed, ref, watch, type Ref } from 'vue'
import { useI18n } from 'vue-i18n'

import type {
  BinanceWeb3HeatRankItemResponse,
  BinanceWeb3TokenAuditResponse,
  BinanceWeb3TokenDynamicResponse,
  BinanceWeb3TokenKlineItemResponse,
} from '../../types/market'
import { marketApi } from './api'
import { compareNullableNumber } from './binanceMarketShared'
import type { CandlestickData, VolumeData } from './contracts'
import { restoreWeb3HeatRankWarmSnapshot, saveWeb3HeatRankWarmSnapshot } from './web3MarketWarmSnapshot'
import {
  web3ApiChainId,
  type Web3HeatRankSortField,
  type Web3HeatRankSortState,
  type Web3TokenDialogState,
} from './web3MarketShared'

const WEB3_HEAT_RANK_SIZE = 30

export function useWeb3HeatRankPanel(chainId: Ref<string>) {
  const { t } = useI18n()
  const web3HeatRank = ref<BinanceWeb3HeatRankItemResponse[]>([])
  const web3Sort = ref<Web3HeatRankSortState>({ field: 'heat_score', direction: 'desc' })
  const web3Loading = ref(false)
  const web3ErrorKey = ref('')
  const web3Error = computed(() => (web3ErrorKey.value ? t(web3ErrorKey.value) : ''))
  const web3Dialog = ref<Web3TokenDialogState>({ open: false, token: null })
  const web3DetailLoading = ref(false)
  const web3DetailErrorKey = ref('')
  const web3DetailError = computed(() => (web3DetailErrorKey.value ? t(web3DetailErrorKey.value) : ''))
  const web3Dynamic = ref<BinanceWeb3TokenDynamicResponse | null>(null)
  const web3Audit = ref<BinanceWeb3TokenAuditResponse | null>(null)
  const web3Kline = ref<BinanceWeb3TokenKlineItemResponse[]>([])
  const web3KlineInterval = ref('15min')
  let heatRankFetchPromise: Promise<void> | null = null

  const web3ChartData = computed<CandlestickData[]>(() => (
    web3Kline.value
      .filter((item) => item.open_time && item.open != null && item.high != null && item.low != null && item.close != null)
      .map((item) => ({
        time: Math.floor(Number(item.open_time) / 1000),
        open: Number(item.open),
        high: Number(item.high),
        low: Number(item.low),
        close: Number(item.close),
      }))
  ))

  const web3VolumeData = computed<VolumeData[]>(() => (
    web3Kline.value
      .filter((item) => item.open_time && item.volume != null)
      .map((item) => ({
        time: Math.floor(Number(item.open_time) / 1000),
        value: Number(item.volume),
        color: Number(item.close ?? 0) >= Number(item.open ?? 0) ? '#10b98188' : '#ef444488',
      }))
  ))

  const sortedWeb3HeatRank = computed(() => (
    [...web3HeatRank.value]
      .sort((left, right) => {
        const primary = compareNullableNumber(web3SortValue(left, web3Sort.value.field), web3SortValue(right, web3Sort.value.field), web3Sort.value.direction)
        if (primary !== 0) return primary
        return (left.rank || 0) - (right.rank || 0)
      })
  ))

  const web3SortValue = (item: BinanceWeb3HeatRankItemResponse, field: Web3HeatRankSortField) => {
    if (field === 'heat_score') return item.heat_score
    const value = item.metrics?.[field]
    return typeof value === 'number' ? value : null
  }

  const applyHeatRankPayload = (payload: Awaited<ReturnType<typeof marketApi.getBinanceWeb3HeatRank>>['data']) => {
    web3HeatRank.value = payload.items || []
  }

  const restoreHeatRankWarmSnapshot = () => {
    const payload = restoreWeb3HeatRankWarmSnapshot(chainId.value, WEB3_HEAT_RANK_SIZE)
    if (payload) {
      applyHeatRankPayload(payload)
      web3ErrorKey.value = ''
      return true
    }
    return false
  }

  const fetchWeb3HeatRank = async () => {
    if (heatRankFetchPromise) return heatRankFetchPromise
    const task = (async () => {
      web3Loading.value = true
      web3ErrorKey.value = ''
      try {
        const response = await marketApi.getBinanceWeb3HeatRank({
          chain_id: web3ApiChainId(chainId.value),
          size: WEB3_HEAT_RANK_SIZE,
        })
        applyHeatRankPayload(response.data)
        saveWeb3HeatRankWarmSnapshot(chainId.value, WEB3_HEAT_RANK_SIZE, response.data)
      } catch (requestError) {
        web3ErrorKey.value = web3HeatRank.value.length
          ? 'web3Rank.heatRankRefreshFailedWithCache'
          : 'web3Rank.heatRankLoadFailed'
        console.error('Failed to load Binance Web3 heat rank', requestError)
      } finally {
        web3Loading.value = false
      }
    })()
    heatRankFetchPromise = task
    try {
      await task
    } finally {
      if (heatRankFetchPromise === task) {
        heatRankFetchPromise = null
      }
    }
  }

  const loadWeb3TokenDetail = async () => {
    const token = web3Dialog.value.token
    if (!web3Dialog.value.open || !token?.chain_id || !token?.contract_address || !token?.platform) return
    web3DetailLoading.value = true
    web3DetailErrorKey.value = ''
    try {
      const [dynamicRes, auditRes, klineRes] = await Promise.all([
        marketApi.getBinanceWeb3TokenDynamic({
          chain_id: token.chain_id,
          contract_address: token.contract_address,
        }),
        marketApi.getBinanceWeb3TokenAudit({
          binance_chain_id: token.chain_id,
          contract_address: token.contract_address,
        }),
        marketApi.getBinanceWeb3TokenKline({
          address: token.contract_address,
          platform: token.platform,
          interval: web3KlineInterval.value,
          limit: 240,
        }),
      ])
      web3Dynamic.value = dynamicRes.data
      web3Audit.value = auditRes.data
      web3Kline.value = klineRes.data?.items || []
    } catch (requestError) {
      web3DetailErrorKey.value = 'web3Rank.tokenDetailLoadFailed'
      web3Dynamic.value = null
      web3Audit.value = null
      web3Kline.value = []
      console.error('Failed to load Web3 token detail', requestError)
    } finally {
      web3DetailLoading.value = false
    }
  }

  const openWeb3Token = (token: BinanceWeb3HeatRankItemResponse) => {
    if (!token.chain_id || !token.contract_address) return
    web3Dialog.value = { open: true, token }
    void loadWeb3TokenDetail()
  }

  const closeWeb3Token = () => {
    web3Dialog.value = { open: false, token: null }
    web3Dynamic.value = null
    web3Audit.value = null
    web3Kline.value = []
    web3DetailErrorKey.value = ''
  }

  const toggleWeb3Sort = (field: Web3HeatRankSortField) => {
    if (web3Sort.value.field === field) {
      web3Sort.value = {
        ...web3Sort.value,
        direction: web3Sort.value.direction === 'desc' ? 'asc' : 'desc',
      }
      return
    }
    web3Sort.value = { field, direction: 'desc' }
  }

  watch(chainId, () => {
    if (!restoreHeatRankWarmSnapshot()) web3HeatRank.value = []
    void fetchWeb3HeatRank()
  })

  watch(web3KlineInterval, () => {
    void loadWeb3TokenDetail()
  })

  restoreHeatRankWarmSnapshot()

  return {
    web3HeatRank: sortedWeb3HeatRank,
    web3Sort,
    web3Loading,
    web3Error,
    web3Dialog,
    web3Dynamic,
    web3Audit,
    web3DetailLoading,
    web3DetailError,
    web3KlineInterval,
    web3ChartData,
    web3VolumeData,
    fetchWeb3HeatRank,
    toggleWeb3Sort,
    openWeb3Token,
    closeWeb3Token,
  }
}
