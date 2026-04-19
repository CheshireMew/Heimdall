import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { bindPageSnapshot, createPageSnapshot, isRecord, PAGE_SNAPSHOT_KEYS, readNumber, readString } from '@/composables/pageSnapshot'
import { isIndexSymbol } from '@/modules/market'
import { useTheme } from '@/composables/useTheme'
import { useMoney } from '@/composables/useMoney'
import { useUserPreferences } from '@/composables/useUserPreferences'
import type { DCASimulationConfig, DCASimulationResponse } from '@/types'
import { toolsApi } from './api'
import { createEmptyMarketData, useDcaMarketContext } from './useDcaMarketContext'
import { useDcaCharts } from './useDcaCharts'

interface DcaPageSnapshot {
  config: DCASimulationConfig
}

type DcaPageConfig = Required<Pick<DCASimulationConfig, 'symbol' | 'amount' | 'investment_time' | 'timezone' | 'strategy'>> & {
  start_date: string
  strategy_params: {
    multiplier: number
  }
}

const createDefaultConfig = (): DcaPageConfig => ({
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

const normalizeConfig = (value: unknown): DcaPageConfig => {
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
    }
  }
  return {
    config: normalizeConfig(value.config),
  }
}


export function useDcaPage() {
  const { theme } = useTheme()
  const { t } = useI18n()
  const { timezone, setTimezone } = useUserPreferences()
  const { displayCurrency, fromDisplayAmount, formatDisplayNumber, formatMoney } = useMoney()
  const pageSnapshot = createPageSnapshot(
    PAGE_SNAPSHOT_KEYS.dca,
    normalizeSnapshot,
    {
      config: createDefaultConfig(),
    },
  )
  const restoredSnapshot = pageSnapshot.load()

  const config = reactive(normalizeConfig(restoredSnapshot?.config))
  config.timezone = timezone.value

  const loading = ref(false)
  const result = ref<DCASimulationResponse | null>(null)
  const { marketData, fetchMarketIndicators } = useDcaMarketContext({
    symbol: () => config.symbol,
    t,
    initialValue: createEmptyMarketData(),
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

  watch(timezone, (nextTimezone) => {
    config.timezone = nextTimezone
  })

  watch(() => config.timezone, (nextTimezone) => {
    if (nextTimezone && nextTimezone !== timezone.value) {
      setTimezone(nextTimezone)
    }
  })

  const displayAmount = computed({
    get: () => formatDisplayNumber(config.amount, 'USDT', 2),
    set: (value: number | string) => {
      const converted = fromDisplayAmount(value, 'USDT')
      config.amount = converted ?? config.amount
    },
  })

  watch(() => config.symbol, () => {
    if (isIndexSymbol(config.symbol) && ['ahr999', 'fear_greed'].includes(config.strategy)) {
      config.strategy = 'standard'
    }
  })

  watch(theme, () => {
    if (result.value) {
      renderCharts()
    }
  })

  watch(displayCurrency, () => {
    if (result.value) {
      renderCharts()
    }
  })

  bindPageSnapshot(
    config,
    () => ({
      config: normalizeConfig(config),
    }),
    pageSnapshot.save,
  )

  onMounted(() => {
    fetchMarketIndicators()
    if (result.value) {
      renderCharts()
    }
  })

  const isPositiveRoi = computed(() => (result.value?.roi || 0) >= 0)
  const isIndexSelected = computed(() => isIndexSymbol(config.symbol))
  const sentimentClass = computed(() => ((marketData.sentiment || 0) >= 50
    ? 'text-green-600 dark:text-green-400'
    : 'text-red-500 dark:text-red-400'))

  return {
    config,
    displayAmount,
    loading,
    result,
    marketData,
    roiChartCanvas,
    priceChartCanvas,
    investmentChartCanvas,
    runSimulation,
    isPositiveRoi,
    isIndexSelected,
    sentimentClass,
    displayCurrency,
    formatMoney,
  }
}
