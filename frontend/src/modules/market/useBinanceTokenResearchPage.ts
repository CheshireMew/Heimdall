import { computed, onMounted, ref } from 'vue'

import { marketApi } from './api'

const defaultRequests = [
  () => marketApi.getReservedBinanceTokenInfoSearch({ keyword: 'BNB', chainIds: '56,8453,CT_501', orderBy: 'volume24h' }),
  () => marketApi.getReservedBinanceTokenInfoMetadata({ chainId: '56', contractAddress: '0x55d398326f99059ff775485246999027b3197955' }),
  () => marketApi.getReservedBinanceTokenInfoDynamic({ chainId: '56', contractAddress: '0x55d398326f99059ff775485246999027b3197955' }),
  () => marketApi.getReservedBinanceTokenInfoKline({ address: '0x55d398326f99059ff775485246999027b3197955', platform: 'bsc', interval: '1d', limit: 120, pm: 'p' }),
  () => marketApi.getReservedBinanceTokenAudit({ binanceChainId: '56', contractAddress: '0x55d398326f99059ff775485246999027b3197955' }),
]

export function useBinanceTokenResearchPage() {
  const loading = ref(false)
  const error = ref('')
  const features = ref([])

  const tokenInfoFeatures = computed(() => features.value.filter((item) => item.skill_name === 'query-token-info'))
  const auditFeatures = computed(() => features.value.filter((item) => item.skill_name === 'query-token-audit'))

  const fetchData = async () => {
    loading.value = true
    error.value = ''
    try {
      const responses = await Promise.all(defaultRequests.map((request) => request()))
      features.value = responses.map((response) => response.data)
    } catch (err) {
      console.error('Failed to load Binance token research placeholders', err)
      error.value = 'Failed to load Binance token research placeholders.'
    } finally {
      loading.value = false
    }
  }

  onMounted(fetchData)

  return {
    loading,
    error,
    features,
    tokenInfoFeatures,
    auditFeatures,
    fetchData,
  }
}
