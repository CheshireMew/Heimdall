import { computed, onMounted, reactive, ref, watch, type WatchStopHandle } from 'vue'
import { useI18n } from 'vue-i18n'

import { createPersistentPageSnapshot, PAGE_SNAPSHOT_KEYS } from '@/composables/pageSnapshot'
import { ensureSymbolCatalogLoaded, isIndexSymbol } from '@/modules/market'
import { useTheme } from '@/composables/useTheme'
import { useMoney } from '@/composables/useMoney'
import { useUserPreferences } from '@/composables/useUserPreferences'
import type { DCARequestSchema, DCAResponse } from '../../types/tools'
import { toolsApi } from './api'
import { buildDcaSnapshot, createDefaultDcaConfig, createEmptyDcaConfig, createEmptyDcaSnapshot, normalizeDcaConfig, normalizeDcaSnapshot } from './pageSnapshots'
import { createEmptyMarketData, useDcaMarketContext } from './useDcaMarketContext'
import { useDcaCharts } from './useDcaCharts'

type RequestError = {
  message?: string
  response?: {
    data?: {
      detail?: string
    }
  }
}

export function useDcaPage() {
  const { theme } = useTheme()
  const { t } = useI18n()
  const { timezone, setTimezone } = useUserPreferences()
  const { displayCurrency, fromDisplayAmount, formatDisplayNumber, formatMoney } = useMoney()
  const pageSnapshot = createPersistentPageSnapshot(
    PAGE_SNAPSHOT_KEYS.dca,
    normalizeDcaSnapshot,
    createEmptyDcaSnapshot(),
  )
  const restoredSnapshot = pageSnapshot.initial
  const config = reactive(createEmptyDcaConfig())
  let snapshotStop: WatchStopHandle | null = null
  const strategyKeys = ref<string[]>([])
  const multiplierDefault = ref(0)

  const loading = ref(false)
  const result = ref<DCAResponse | null>(null)
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
      await ensureSymbolCatalogLoaded()
      const payload: DCARequestSchema = {
        ...config,
        strategy: config.strategy || undefined,
      }
      const response = await toolsApi.runSimulation(payload)
      result.value = {
        ...response.data,
        current_price: typeof response.data.current_price !== 'undefined'
          ? response.data.current_price
          : response.data.history?.[response.data.history.length - 1]?.price,
        total_days: response.data.history?.length ?? response.data.total_days,
      }
      await fetchMarketIndicators()
      renderCharts()
    } catch (error: unknown) {
      const requestError = error as RequestError
      console.error('DCA Error:', error)
      alert(`${t('dca.simFailed')}: ${requestError.response?.data?.detail || requestError.message || 'Unknown error'}`)
    } finally {
      loading.value = false
    }
  }

  watch(() => config.strategy, (nextStrategy) => {
    if (nextStrategy === 'ema_deviation') {
      if (!config.strategy_params.multiplier) config.strategy_params.multiplier = multiplierDefault.value
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

  onMounted(async () => {
    const [contractResponse] = await Promise.all([
      toolsApi.getContract(),
      ensureSymbolCatalogLoaded(),
    ])
    strategyKeys.value = [...contractResponse.data.dca_strategies]
    multiplierDefault.value = contractResponse.data.dca_multiplier_default
    const defaultConfig = createDefaultDcaConfig(contractResponse.data)
    const restoredConfig = normalizeDcaSnapshot(
      restoredSnapshot,
      { config: defaultConfig },
      strategyKeys.value,
    ).config
    Object.assign(config, restoredConfig)
    config.timezone = timezone.value
    if (!snapshotStop) {
      snapshotStop = pageSnapshot.bind(
        config,
        () => buildDcaSnapshot(config, defaultConfig, strategyKeys.value),
      )
    }
    await fetchMarketIndicators()
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
