import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { bindPageSnapshot, createPageSnapshot, isRecord, PAGE_SNAPSHOT_KEYS, readNumber, readString } from '@/composables/pageSnapshot'
import { useTheme } from '@/composables/useTheme'
import type { DCASimulationConfig, DCASimulationResponse } from '@/types'
import { toolsApi } from './api'
import { createEmptyMarketData, normalizeMarketData, useDcaMarketContext, type DcaMarketState } from './useDcaMarketContext'
import { useDcaCharts } from './useDcaCharts'

interface DcaPageSnapshot {
  config: DCASimulationConfig
  result: DCASimulationResponse | null
  marketData: DcaMarketState
}

const createDefaultConfig = (): Required<Pick<DCASimulationConfig, 'symbol' | 'amount' | 'start_date' | 'investment_time' | 'timezone' | 'strategy' | 'strategy_params'>> => ({
  symbol: 'BTC/USDT',
  amount: 100,
  start_date: '2025-04-25',
  investment_time: '23:00',
  timezone: 'Asia/Shanghai',
  strategy: 'standard',
  strategy_params: {
    multiplier: 3,
  },
})

const normalizeConfig = (value: unknown) => {
  const defaults = createDefaultConfig()
  if (!isRecord(value)) return defaults

  const strategyParams = isRecord(value.strategy_params) ? value.strategy_params : {}

  return {
    symbol: readString(value.symbol, defaults.symbol),
    amount: readNumber(value.amount, defaults.amount),
    start_date: readString(value.start_date, defaults.start_date),
    investment_time: readString(value.investment_time, defaults.investment_time),
    timezone: readString(value.timezone, defaults.timezone),
    strategy: readString(value.strategy, defaults.strategy),
    strategy_params: {
      multiplier: readNumber(strategyParams.multiplier, defaults.strategy_params.multiplier),
    },
  }
}

const normalizeSnapshot = (value: unknown): DcaPageSnapshot => {
  if (!isRecord(value)) {
    return {
      config: createDefaultConfig(),
      result: null,
      marketData: createEmptyMarketData(),
    }
  }
  return {
    config: normalizeConfig(value.config),
    result: value.result && isRecord(value.result) ? value.result as DCASimulationResponse : null,
    marketData: normalizeMarketData(value.marketData),
  }
}


export function useDcaPage() {
  const { theme } = useTheme()
  const { t } = useI18n()
  const pageSnapshot = createPageSnapshot(
    PAGE_SNAPSHOT_KEYS.dca,
    normalizeSnapshot,
    {
      config: createDefaultConfig(),
      result: null,
      marketData: createEmptyMarketData(),
    },
  )
  const hasSavedSnapshot = pageSnapshot.exists()
  const restoredSnapshot = pageSnapshot.load()

  const config = reactive(normalizeConfig(restoredSnapshot?.config))

  const loading = ref(false)
  const result = ref<DCASimulationResponse | null>(restoredSnapshot?.result ?? null)
  const { marketData, fetchMarketIndicators } = useDcaMarketContext({
    symbol: () => config.symbol,
    t,
    initialValue: restoredSnapshot?.marketData,
  })
  const {
    roiChartCanvas,
    priceChartCanvas,
    investmentChartCanvas,
    renderCharts,
  } = useDcaCharts({
    theme,
    t,
    result,
  })

  const runSimulation = async () => {
    loading.value = true
    try {
      const response = await toolsApi.runSimulation(config)
      result.value = {
        ...response.data,
        current_price: typeof response.data.current_price !== 'undefined'
          ? response.data.current_price
          : response.data.history?.[response.data.history.length - 1]?.price,
        total_days: response.data.history?.length ?? response.data.total_days,
      }
      await fetchMarketIndicators()
      renderCharts()
    } catch (error: any) {
      console.error('DCA Error:', error)
      alert(`${t('dca.simFailed')}: ${error.response?.data?.detail || error.message}`)
    } finally {
      loading.value = false
    }
  }

  watch(() => config.strategy, (nextStrategy) => {
    if (nextStrategy === 'ema_deviation') {
      config.strategy_params.multiplier = 3
    } else if (['rsi_dynamic', 'fear_greed', 'ahr999'].includes(nextStrategy)) {
      config.strategy_params.multiplier = 1
    }
  })

  watch(theme, () => {
    if (result.value) {
      renderCharts()
    }
  })

  bindPageSnapshot(
    [config, result, marketData],
    () => ({
      config: normalizeConfig(config),
      result: result.value,
      marketData: normalizeMarketData(marketData),
    }),
    pageSnapshot.save,
  )

  onMounted(() => {
    if (!hasSavedSnapshot) {
      try {
        const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone
        if (userTimezone) {
          config.timezone = userTimezone
        }
      } catch (error) {
        console.warn('Timezone detection failed:', error)
      }
    }
    fetchMarketIndicators()
    if (result.value) {
      renderCharts()
    }
  })

  const isPositiveRoi = computed(() => (result.value?.roi || 0) >= 0)
  const sentimentClass = computed(() => ((marketData.sentiment || 0) >= 50
    ? 'text-green-600 dark:text-green-400'
    : 'text-red-500 dark:text-red-400'))

  return {
    config,
    loading,
    result,
    marketData,
    roiChartCanvas,
    priceChartCanvas,
    investmentChartCanvas,
    runSimulation,
    isPositiveRoi,
    sentimentClass,
  }
}
