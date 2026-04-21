import { computed, onMounted, ref, watch } from 'vue'

import { formatCompactNumber, formatSignedPercent } from '@/modules/format'
import { marketApi } from './api'
import type {
  BinanceWeb3AddressPnlItemResponse,
  BinanceWeb3MemeRankItemResponse,
  BinanceWeb3RankItemResponse,
  BinanceWeb3SmartMoneyInflowItemResponse,
  BinanceWeb3SocialHypeItemResponse,
} from '../../types/market'

const UNIFIED_OPTIONS = [
  { label: 'Trending', value: 10 },
  { label: 'Top Search', value: 11 },
  { label: 'Alpha', value: 20 },
  { label: 'Stock', value: 40 },
]

const CHAIN_OPTIONS = [
  { label: 'BSC', value: '56' },
  { label: 'Base', value: '8453' },
  { label: 'Solana', value: 'CT_501' },
]

const changeClass = (value: number | null | undefined) => {
  if (value === null || value === undefined || Number.isNaN(value)) return 'text-slate-500 dark:text-slate-400'
  return value >= 0 ? 'text-emerald-500' : 'text-rose-500'
}

export function useWeb3MarketRankPage() {
  const loading = ref(false)
  const error = ref('')
  const chainId = ref('56')
  const rankType = ref(10)
  const socialHype = ref<BinanceWeb3SocialHypeItemResponse[]>([])
  const unifiedRank = ref<BinanceWeb3RankItemResponse[]>([])
  const smartMoney = ref<BinanceWeb3SmartMoneyInflowItemResponse[]>([])
  const memeRank = ref<BinanceWeb3MemeRankItemResponse[]>([])
  const addressPnl = ref<BinanceWeb3AddressPnlItemResponse[]>([])

  const summaryCards = computed(() => [
    {
      label: 'Social Hype',
      primary: socialHype.value[0]?.symbol || '--',
      secondary: formatSignedPercent(socialHype.value[0]?.price_change_pct),
      tone: changeClass(socialHype.value[0]?.price_change_pct),
    },
    {
      label: 'Unified Rank',
      primary: unifiedRank.value[0]?.symbol || '--',
      secondary: formatSignedPercent(unifiedRank.value[0]?.percent_change_24h),
      tone: changeClass(unifiedRank.value[0]?.percent_change_24h),
    },
    {
      label: 'Smart Money',
      primary: smartMoney.value[0]?.symbol || '--',
      secondary: formatCompactNumber(smartMoney.value[0]?.inflow),
      tone: 'text-cyan-500',
    },
    {
      label: 'PnL Board',
      primary: addressPnl.value[0]?.address_label || addressPnl.value[0]?.address || '--',
      secondary: formatCompactNumber(addressPnl.value[0]?.realized_pnl),
      tone: changeClass(addressPnl.value[0]?.realized_pnl),
    },
  ])

  const fetchData = async () => {
    loading.value = true
    error.value = ''
    try {
      const pnlChainId = chainId.value === '8453' ? '56' : chainId.value
      const [socialRes, unifiedRes, smartRes, memeRes, pnlRes] = await Promise.all([
        marketApi.getBinanceWeb3SocialHype({ chain_id: chainId.value, target_language: 'zh' }),
        marketApi.getBinanceWeb3UnifiedTokenRank({ chain_id: chainId.value, rank_type: rankType.value, size: 15 }),
        marketApi.getBinanceWeb3SmartMoneyInflow({ chain_id: chainId.value === '8453' ? '56' : chainId.value }),
        marketApi.getBinanceWeb3MemeRank({ chain_id: '56' }),
        marketApi.getBinanceWeb3AddressPnlRank({ chain_id: pnlChainId, page_size: 10 }),
      ])
      socialHype.value = socialRes.data?.items || []
      unifiedRank.value = unifiedRes.data?.items || []
      smartMoney.value = smartRes.data?.items || []
      memeRank.value = memeRes.data?.items || []
      addressPnl.value = pnlRes.data?.items || []
    } catch (err) {
      console.error('Failed to load Binance Web3 rank page', err)
      error.value = 'Failed to load Binance Web3 rankings.'
    } finally {
      loading.value = false
    }
  }

  watch([chainId, rankType], fetchData)
  onMounted(fetchData)

  return {
    loading,
    error,
    chainId,
    rankType,
    chainOptions: CHAIN_OPTIONS,
    unifiedOptions: UNIFIED_OPTIONS,
    socialHype,
    unifiedRank,
    smartMoney,
    memeRank,
    addressPnl,
    summaryCards,
    fetchData,
    formatPercent: formatSignedPercent,
    formatCompact: formatCompactNumber,
    changeClass,
  }
}
