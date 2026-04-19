import { computed, ref, watch } from 'vue'

import type {
  BinanceWeb3HeatRankItemResponse,
  BinanceWeb3TokenAuditResponse,
  BinanceWeb3TokenDynamicResponse,
  BinanceWeb3TokenKlineItemResponse,
  CandlestickData,
  VolumeData,
} from '@/types'
import { marketApi } from './api'
import type { Web3TokenDialogState } from './binanceMarketShared'

export function useBinanceWeb3Panel(initialChainId: string) {
  const web3ChainId = ref(initialChainId)
  const web3HeatRank = ref<BinanceWeb3HeatRankItemResponse[]>([])
  const web3Loading = ref(false)
  const web3Error = ref('')
  const web3Dialog = ref<Web3TokenDialogState>({ open: false, token: null })
  const web3DetailLoading = ref(false)
  const web3DetailError = ref('')
  const web3Dynamic = ref<BinanceWeb3TokenDynamicResponse | null>(null)
  const web3Audit = ref<BinanceWeb3TokenAuditResponse | null>(null)
  const web3Kline = ref<BinanceWeb3TokenKlineItemResponse[]>([])
  const web3KlineInterval = ref('15min')

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

  const fetchWeb3HeatRank = async () => {
    web3Loading.value = true
    web3Error.value = ''
    try {
      const response = await marketApi.getBinanceWeb3HeatRank({
        chain_id: web3ChainId.value,
        size: 30,
      })
      web3HeatRank.value = response.data?.items || []
    } catch (requestError) {
      web3HeatRank.value = []
      web3Error.value = 'Web3 热度榜加载失败'
      console.error('Failed to load Binance Web3 heat rank', requestError)
    } finally {
      web3Loading.value = false
    }
  }

  const loadWeb3TokenDetail = async () => {
    const token = web3Dialog.value.token
    if (!web3Dialog.value.open || !token?.chain_id || !token?.contract_address || !token?.platform) return
    web3DetailLoading.value = true
    web3DetailError.value = ''
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
      web3DetailError.value = 'Token 详情加载失败'
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
    web3DetailError.value = ''
  }

  watch(web3ChainId, () => {
    void fetchWeb3HeatRank()
  })
  watch(web3KlineInterval, () => {
    void loadWeb3TokenDetail()
  })

  return {
    web3ChainId,
    web3HeatRank,
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
    openWeb3Token,
    closeWeb3Token,
  }
}
