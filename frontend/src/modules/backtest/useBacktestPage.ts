import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import { useTheme } from '@/composables/useTheme'
import { backtestApi } from './api'
import { asNumber } from './format'
import { useBacktestRuns } from './useBacktestRuns'


export const useBacktestPage = () => {
  const { t } = useI18n()
  const { theme } = useTheme()
  const router = useRouter()
  let paperRefreshTimer: number | null = null

  const timeframes = ['1m', '5m', '15m', '1h', '4h', '1d']
  const optimizeMetrics = ['sharpe', 'profit_pct', 'calmar', 'profit_factor']
  const strategies = ref<any[]>([])

  const config = reactive({
    strategy_key: 'ema_rsi_macd',
    strategy_version: 1,
    timeframe: '1h',
    days: 180,
    initial_cash: 100000,
    fee_rate: 0.1,
    portfolio: {
      max_open_trades: 2,
      position_size_pct: 25,
      stake_mode: 'fixed',
    },
    research: {
      slippage_bps: 5,
      funding_rate_daily: 0,
      in_sample_ratio: 70,
      optimize_metric: 'sharpe',
      optimize_trials: 12,
      rolling_windows: 3,
    },
  })

  const isDark = computed(() => theme.value === 'dark')
  const chartColors = computed(() => ({
    bg: isDark.value ? '#1f2937' : '#ffffff',
    grid: isDark.value ? '#374151' : '#e5e7eb',
    text: isDark.value ? '#9ca3af' : '#4b5563',
    upColor: '#10b981',
    downColor: '#ef4444',
  }))

  const selectedStrategy = computed(() => strategies.value.find((item) => item.key === config.strategy_key) || null)
  const selectedStrategyVersions = computed(() => {
    const versions = selectedStrategy.value?.versions
    if (!Array.isArray(versions)) return []
    return versions.filter(Boolean)
  })
  const selectedVersion = computed(() => selectedStrategyVersions.value.find((item: any) => item.version === config.strategy_version) || null)
  const runs = useBacktestRuns({
    t,
    config,
    selectedStrategyVersions,
  })

  const categoryLabel = (value: string) => {
    if (value === 'trend') return t('backtest.categoryTrend')
    if (value === 'mean_reversion') return t('backtest.categoryMeanReversion')
    if (value === 'breakout') return t('backtest.categoryBreakout')
    if (value === 'custom') return t('backtest.categoryCustom')
    return value || '-'
  }

  const profitColorClass = (value: unknown) => {
    const numeric = asNumber(value)
    if (numeric === null) return 'text-gray-500'
    if (numeric > 0) return 'text-green-600 dark:text-green-400'
    if (numeric < 0) return 'text-red-600 dark:text-red-400'
    return 'text-gray-500'
  }

  const syncStrategyVersion = () => {
    const versions = selectedStrategyVersions.value
    if (!versions.length) return
    if (!versions.find((item: any) => item.version === config.strategy_version)) {
      const fallback = versions.find((item: any) => item.is_default) || versions[0]
      config.strategy_version = fallback.version
    }
    const validVersions = new Set(runs.versionCompareOptions.value.map((item) => item.version))
    runs.versionCompareSelections.value = runs.versionCompareSelections.value.filter((item) => validVersions.has(item))
  }

  const fetchStrategies = async () => {
    try {
      const res = await backtestApi.listStrategies()
      strategies.value = res.data
      if (strategies.value.length && !strategies.value.find((item) => item.key === config.strategy_key)) {
        config.strategy_key = strategies.value[0].key
      }
      syncStrategyVersion()
    } catch (error) {
      console.error(error)
    }
  }

  const openCopyEditor = () => {
    if (!selectedStrategy.value || !selectedVersion.value) return
    router.push({
      path: '/backtest/editor',
      query: {
        mode: 'copy',
        strategy: config.strategy_key,
        version: String(config.strategy_version),
      },
    })
  }

  const openBlankEditor = () => {
    router.push({
      path: '/backtest/editor',
      query: {
        mode: 'blank',
        strategy: config.strategy_key,
      },
    })
  }

  const openRunDetail = (run: any, mode: 'backtest' | 'paper' = runs.historyMode.value) => {
    if (!run?.id) return
    const path = mode === 'paper' ? `/backtest/paper/${run.id}` : `/backtest/runs/${run.id}`
    router.push(path)
  }

  const startBacktest = async () => {
    const target = await runs.startBacktest()
    if (!target) return
    router.push(`/backtest/runs/${target.id}`)
  }

  const startPaperRun = async () => {
    const target = await runs.startPaperRun()
    if (!target) return
    router.push(`/backtest/paper/${target.id}`)
  }

  onMounted(async () => {
    await Promise.all([runs.fetchHistory(), runs.fetchPaperHistory(), fetchStrategies()])
    paperRefreshTimer = window.setInterval(() => {
      runs.refreshPaperSelection().catch((error) => console.error(error))
    }, 10000)
  })

  onBeforeUnmount(() => {
    if (paperRefreshTimer !== null) {
      window.clearInterval(paperRefreshTimer)
      paperRefreshTimer = null
    }
  })

  const page = reactive({
    t,
    theme,
    timeframes,
    optimizeMetrics,
    strategies,
    config,
    isDark,
    chartColors,
    selectedStrategy,
    selectedStrategyVersions,
    selectedVersion,
    enableHistoryCompare: false,
    categoryLabel,
    profitColorClass,
    syncStrategyVersion,
    fetchStrategies,
    ...runs,
    openRunDetail,
    openCopyEditor,
    openBlankEditor,
    startBacktest,
    startPaperRun,
  })

  return page
}


export type BacktestPageState = ReturnType<typeof useBacktestPage>
