import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import { bindPageSnapshot, createPageSnapshot, isRecord, PAGE_SNAPSHOT_KEYS, readNumber, readString } from '@/composables/pageSnapshot'
import { useTheme } from '@/composables/useTheme'
import { backtestApi } from './api'
import { asNumber } from './format'
import { useBacktestRuns } from './useBacktestRuns'

interface BacktestPageSnapshot {
  config: {
    strategy_key: string
    strategy_version: number
    timeframe: string
    days: number
    initial_cash: number
    fee_rate: number
    portfolio: {
      max_open_trades: number
      position_size_pct: number
      stake_mode: string
    }
    research: {
      slippage_bps: number
      funding_rate_daily: number
      in_sample_ratio: number
      optimize_metric: string
      optimize_trials: number
      rolling_windows: number
    }
  }
  symbolsText: string
  historyMode: 'backtest' | 'paper'
}

const createDefaultSnapshot = (): BacktestPageSnapshot => ({
  config: {
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
  },
  symbolsText: 'BTC/USDT, ETH/USDT',
  historyMode: 'backtest',
})

const normalizeSnapshot = (value: unknown): BacktestPageSnapshot => {
  const defaults = createDefaultSnapshot()
  if (!isRecord(value) || !isRecord(value.config)) return defaults
  const config = value.config
  const portfolio = isRecord(config.portfolio) ? config.portfolio : {}
  const research = isRecord(config.research) ? config.research : {}
  const historyMode = readString(value.historyMode, defaults.historyMode)

  return {
    config: {
      strategy_key: readString(config.strategy_key, defaults.config.strategy_key),
      strategy_version: readNumber(config.strategy_version, defaults.config.strategy_version),
      timeframe: readString(config.timeframe, defaults.config.timeframe),
      days: readNumber(config.days, defaults.config.days),
      initial_cash: readNumber(config.initial_cash, defaults.config.initial_cash),
      fee_rate: readNumber(config.fee_rate, defaults.config.fee_rate),
      portfolio: {
        max_open_trades: readNumber(portfolio.max_open_trades, defaults.config.portfolio.max_open_trades),
        position_size_pct: readNumber(portfolio.position_size_pct, defaults.config.portfolio.position_size_pct),
        stake_mode: readString(portfolio.stake_mode, defaults.config.portfolio.stake_mode),
      },
      research: {
        slippage_bps: readNumber(research.slippage_bps, defaults.config.research.slippage_bps),
        funding_rate_daily: readNumber(research.funding_rate_daily, defaults.config.research.funding_rate_daily),
        in_sample_ratio: readNumber(research.in_sample_ratio, defaults.config.research.in_sample_ratio),
        optimize_metric: readString(research.optimize_metric, defaults.config.research.optimize_metric),
        optimize_trials: readNumber(research.optimize_trials, defaults.config.research.optimize_trials),
        rolling_windows: readNumber(research.rolling_windows, defaults.config.research.rolling_windows),
      },
    },
    symbolsText: readString(value.symbolsText, defaults.symbolsText),
    historyMode: historyMode === 'paper' ? 'paper' : 'backtest',
  }
}


export const useBacktestPage = () => {
  const { t } = useI18n()
  const { theme } = useTheme()
  const router = useRouter()
  let paperRefreshTimer: number | null = null
  const pageSnapshot = createPageSnapshot(PAGE_SNAPSHOT_KEYS.backtest, normalizeSnapshot, createDefaultSnapshot())
  const restoredSnapshot = pageSnapshot.load()

  const timeframes = ['1m', '5m', '15m', '1h', '4h', '1d']
  const optimizeMetrics = ['sharpe', 'profit_pct', 'calmar', 'profit_factor']
  const strategies = ref<any[]>([])

  const config = reactive(restoredSnapshot.config)

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
  runs.symbolsText.value = restoredSnapshot.symbolsText
  runs.historyMode.value = restoredSnapshot.historyMode

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

  bindPageSnapshot(
    [config, runs.symbolsText, runs.historyMode],
    () => ({
      config: {
        strategy_key: readString(config.strategy_key, 'ema_rsi_macd'),
        strategy_version: readNumber(config.strategy_version, 1),
        timeframe: readString(config.timeframe, '1h'),
        days: readNumber(config.days, 180),
        initial_cash: readNumber(config.initial_cash, 100000),
        fee_rate: readNumber(config.fee_rate, 0.1),
        portfolio: {
          max_open_trades: readNumber(config.portfolio.max_open_trades, 2),
          position_size_pct: readNumber(config.portfolio.position_size_pct, 25),
          stake_mode: readString(config.portfolio.stake_mode, 'fixed'),
        },
        research: {
          slippage_bps: readNumber(config.research.slippage_bps, 5),
          funding_rate_daily: readNumber(config.research.funding_rate_daily, 0),
          in_sample_ratio: readNumber(config.research.in_sample_ratio, 70),
          optimize_metric: readString(config.research.optimize_metric, 'sharpe'),
          optimize_trials: readNumber(config.research.optimize_trials, 12),
          rolling_windows: readNumber(config.research.rolling_windows, 3),
        },
      },
      symbolsText: readString(runs.symbolsText.value, 'BTC/USDT, ETH/USDT'),
      historyMode: runs.historyMode.value,
    }),
    pageSnapshot.save,
  )

  const controlPanel = reactive({
    config,
    strategies,
    selectedStrategy,
    selectedStrategyVersions,
    selectedVersion,
    timeframes,
    optimizeMetrics,
    symbolsText: runs.symbolsText,
    backtestLoading: runs.backtestLoading,
    paperLoading: runs.paperLoading,
    isBusy: runs.isBusy,
    syncStrategyVersion,
    openCopyEditor,
    openBlankEditor,
    startBacktest,
    startPaperRun,
  })

  const historyPanel = reactive({
    historyMode: runs.historyMode,
    enableHistoryCompare: false,
    visibleHistory: runs.visibleHistory,
    compareRunIds: runs.compareRunIds,
    openRunDetail,
    toggleCompareRun: runs.toggleCompareRun,
    portfolioLabel: runs.portfolioLabel,
    runStatusLabel: runs.runStatusLabel,
    profitColorClass,
    stopPaperRun: runs.stopPaperRun,
    deleteRun: runs.deleteRun,
  })

  return {
    controlPanel,
    historyPanel,
  }
}


export type BacktestPageState = ReturnType<typeof useBacktestPage>
