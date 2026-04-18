import { computed, onBeforeUnmount, onMounted, reactive, ref, watch, type WatchStopHandle } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import type { BacktestRunDefaults, StrategyEditorContract } from '@/types'
import { bindPageSnapshot, createPageSnapshot, isRecord, PAGE_SNAPSHOT_KEYS, readNumber, readString } from '@/composables/pageSnapshot'
import { backtestApi } from './api'
import { asNumber } from './format'
import { supportsPaperTrading, supportsVersionEditing } from './templateRuntime'
import { useBacktestRuns } from './useBacktestRuns'

interface BacktestPageSnapshot {
  config: {
    strategy_key: string
    strategy_version: number
    timeframe: string
    start_date: string
    end_date: string
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

const todayIso = () => new Date().toISOString().slice(0, 10)

const createEmptySnapshot = (): BacktestPageSnapshot => ({
  config: {
    strategy_key: '',
    strategy_version: 1,
    timeframe: '',
    start_date: '',
    end_date: '',
    initial_cash: 0,
    fee_rate: 0,
    portfolio: {
      max_open_trades: 1,
      position_size_pct: 0,
      stake_mode: 'fixed',
    },
    research: {
      slippage_bps: 0,
      funding_rate_daily: 0,
      in_sample_ratio: 100,
      optimize_metric: 'sharpe',
      optimize_trials: 0,
      rolling_windows: 0,
    },
  },
  symbolsText: '',
  historyMode: 'backtest',
})

const createSnapshotDefaults = (runDefaults: BacktestRunDefaults): BacktestPageSnapshot => ({
  config: {
    strategy_key: runDefaults.strategy_key,
    strategy_version: 1,
    timeframe: runDefaults.timeframe,
    start_date: runDefaults.start_date,
    end_date: runDefaults.end_date,
    initial_cash: runDefaults.initial_cash,
    fee_rate: runDefaults.fee_rate,
    portfolio: {
      max_open_trades: runDefaults.portfolio?.max_open_trades ?? 1,
      position_size_pct: runDefaults.portfolio?.position_size_pct ?? 0,
      stake_mode: runDefaults.portfolio?.stake_mode ?? 'fixed',
    },
    research: {
      slippage_bps: runDefaults.research?.slippage_bps ?? 0,
      funding_rate_daily: runDefaults.research?.funding_rate_daily ?? 0,
      in_sample_ratio: runDefaults.research?.in_sample_ratio ?? 100,
      optimize_metric: runDefaults.research?.optimize_metric ?? 'sharpe',
      optimize_trials: runDefaults.research?.optimize_trials ?? 0,
      rolling_windows: runDefaults.research?.rolling_windows ?? 0,
    },
  },
  symbolsText: (runDefaults.portfolio?.symbols || []).join(', '),
  historyMode: runDefaults.history_mode === 'paper' ? 'paper' : 'backtest',
})

const normalizeSnapshot = (value: unknown, defaults: BacktestPageSnapshot): BacktestPageSnapshot => {
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
      start_date: readString(config.start_date, defaults.config.start_date),
      end_date: readString(config.end_date, defaults.config.end_date),
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

const applySnapshot = (
  config: BacktestPageSnapshot['config'],
  snapshot: BacktestPageSnapshot,
  symbolsText: { value: string },
  historyMode: { value: 'backtest' | 'paper' },
) => {
  config.strategy_key = snapshot.config.strategy_key
  config.strategy_version = snapshot.config.strategy_version
  config.timeframe = snapshot.config.timeframe
  config.start_date = snapshot.config.start_date
  config.end_date = snapshot.config.end_date
  config.initial_cash = snapshot.config.initial_cash
  config.fee_rate = snapshot.config.fee_rate
  config.portfolio = { ...snapshot.config.portfolio }
  config.research = { ...snapshot.config.research }
  symbolsText.value = snapshot.symbolsText
  historyMode.value = snapshot.historyMode
}

export const useBacktestPage = () => {
  const { t } = useI18n()
  const router = useRouter()
  let paperRefreshTimer: number | null = null
  let snapshotStopHandle: WatchStopHandle | null = null

  const ready = ref(false)
  const editorContract = ref<StrategyEditorContract | null>(null)
  const strategies = ref<any[]>([])
  const config = reactive(createEmptySnapshot().config)

  const selectedStrategy = computed(() => strategies.value.find((item) => item.key === config.strategy_key) || null)
  const selectedStrategyVersions = computed(() => {
    const versions = selectedStrategy.value?.versions
    return Array.isArray(versions) ? versions.filter(Boolean) : []
  })
  const selectedVersion = computed(() => selectedStrategyVersions.value.find((item: any) => item.version === config.strategy_version) || null)
  const canCopyCurrentStrategy = computed(() => Boolean(selectedVersion.value) && supportsVersionEditing(selectedStrategy.value))
  const canStartPaperRun = computed(() => supportsPaperTrading(selectedStrategy.value))
  const strategyCapabilityHint = computed(() => {
    if (!selectedStrategy.value) return ''
    if (!supportsVersionEditing(selectedStrategy.value) && !supportsPaperTrading(selectedStrategy.value)) {
      return t('backtest.scriptedReadonlyHint')
    }
    if (!supportsPaperTrading(selectedStrategy.value)) {
      return t('backtest.paperUnsupportedHint')
    }
    return ''
  })

  const runs = useBacktestRuns({
    t,
    config,
    selectedStrategyVersions,
  })

  const timeframes = computed(() => (
    editorContract.value?.timeframe_options
      ?.filter((item) => item?.key && item.key !== 'base')
      .map((item) => item.key) || []
  ))
  const optimizeMetrics = computed(() => (
    editorContract.value?.run_defaults?.optimize_metric_options?.map((item) => item.key) || []
  ))

  const profitColorClass = (value: unknown) => {
    const numeric = asNumber(value)
    if (numeric === null) return 'text-gray-500'
    if (numeric > 0) return 'text-green-600 dark:text-green-400'
    if (numeric < 0) return 'text-red-600 dark:text-red-400'
    return 'text-gray-500'
  }

  const syncRunTimeframe = () => {
    const runtime = selectedVersion.value?.runtime
    const preferred = runtime?.preferred_run_timeframe
    if (!preferred) return
    const allowed = new Set(runtime.allowed_run_timeframes || [])
    if (!allowed.size || !allowed.has(config.timeframe)) {
      config.timeframe = preferred
    }
  }

  const syncStrategyVersion = () => {
    const versions = selectedStrategyVersions.value
    if (!versions.length) return
    if (!versions.find((item: any) => item.version === config.strategy_version)) {
      const fallback = versions.find((item: any) => item.is_default) || versions[0]
      config.strategy_version = fallback.version
    }
    syncRunTimeframe()
    const validVersions = new Set(runs.versionCompareOptions.value.map((item) => item.version))
    runs.versionCompareSelections.value = runs.versionCompareSelections.value.filter((item) => validVersions.has(item))
  }

  const bindSnapshot = (contract: StrategyEditorContract) => {
    const defaults = createSnapshotDefaults(contract.run_defaults)
    const pageSnapshot = createPageSnapshot(
      PAGE_SNAPSHOT_KEYS.backtest,
      (value) => normalizeSnapshot(value, defaults),
      defaults,
    )
    applySnapshot(config, pageSnapshot.load(), runs.symbolsText, runs.historyMode)
    snapshotStopHandle?.()
    snapshotStopHandle = bindPageSnapshot(
      [config, runs.symbolsText, runs.historyMode],
      () => ({
        config: {
          strategy_key: readString(config.strategy_key, defaults.config.strategy_key),
          strategy_version: readNumber(config.strategy_version, defaults.config.strategy_version),
          timeframe: readString(config.timeframe, defaults.config.timeframe),
          start_date: readString(config.start_date, defaults.config.start_date),
          end_date: readString(config.end_date, defaults.config.end_date),
          initial_cash: readNumber(config.initial_cash, defaults.config.initial_cash),
          fee_rate: readNumber(config.fee_rate, defaults.config.fee_rate),
          portfolio: {
            max_open_trades: readNumber(config.portfolio.max_open_trades, defaults.config.portfolio.max_open_trades),
            position_size_pct: readNumber(config.portfolio.position_size_pct, defaults.config.portfolio.position_size_pct),
            stake_mode: readString(config.portfolio.stake_mode, defaults.config.portfolio.stake_mode),
          },
          research: {
            slippage_bps: readNumber(config.research.slippage_bps, defaults.config.research.slippage_bps),
            funding_rate_daily: readNumber(config.research.funding_rate_daily, defaults.config.research.funding_rate_daily),
            in_sample_ratio: readNumber(config.research.in_sample_ratio, defaults.config.research.in_sample_ratio),
            optimize_metric: readString(config.research.optimize_metric, defaults.config.research.optimize_metric),
            optimize_trials: readNumber(config.research.optimize_trials, defaults.config.research.optimize_trials),
            rolling_windows: readNumber(config.research.rolling_windows, defaults.config.research.rolling_windows),
          },
        },
        symbolsText: readString(runs.symbolsText.value, defaults.symbolsText),
        historyMode: runs.historyMode.value,
      }),
      pageSnapshot.save,
    )
  }

  const hydratePage = async () => {
    const [contractResponse, strategiesResponse] = await Promise.all([
      backtestApi.getEditorContract(),
      backtestApi.listStrategies(),
    ])

    editorContract.value = contractResponse.data
    bindSnapshot(contractResponse.data)

    strategies.value = strategiesResponse.data
    if (strategies.value.length && !strategies.value.find((item) => item.key === config.strategy_key)) {
      config.strategy_key = strategies.value[0].key
    }
    syncStrategyVersion()
    ready.value = true
    await Promise.all([runs.fetchHistory(), runs.fetchPaperHistory()])
  }

  const openCopyEditor = () => {
    if (!selectedStrategy.value || !selectedVersion.value || !canCopyCurrentStrategy.value) return
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
    router.push(mode === 'paper' ? `/backtest/paper/${run.id}` : `/backtest/runs/${run.id}`)
  }

  const startBacktest = async () => {
    const target = await runs.startBacktest()
    if (!target) return
    router.push(`/backtest/runs/${target.id}`)
  }

  const startPaperRun = async () => {
    if (!canStartPaperRun.value) return
    const target = await runs.startPaperRun()
    if (!target) return
    router.push(`/backtest/paper/${target.id}`)
  }

  onMounted(async () => {
    try {
      await hydratePage()
      paperRefreshTimer = window.setInterval(() => {
        runs.refreshPaperSelection().catch((error) => console.error(error))
      }, 10000)
    } catch (error) {
      console.error(error)
    }
  })

  watch(() => config.strategy_key, () => {
    syncStrategyVersion()
  })

  watch(() => config.strategy_version, () => {
    syncRunTimeframe()
  })

  watch(() => config.start_date, (value) => {
    if (!value) return
    if (!config.end_date || config.end_date <= value) {
      const nextDay = new Date(`${value}T00:00:00`)
      nextDay.setDate(nextDay.getDate() + 1)
      config.end_date = nextDay.toISOString().slice(0, 10)
    }
  })

  watch(() => config.end_date, (value) => {
    if (!value || !config.start_date) return
    if (value <= config.start_date) {
      const previousDay = new Date(`${value}T00:00:00`)
      previousDay.setDate(previousDay.getDate() - 1)
      config.start_date = previousDay.toISOString().slice(0, 10)
    }
  })

  onBeforeUnmount(() => {
    snapshotStopHandle?.()
    if (paperRefreshTimer !== null) {
      window.clearInterval(paperRefreshTimer)
      paperRefreshTimer = null
    }
  })

  const controlPanel = reactive({
    config,
    today: todayIso(),
    ready,
    strategies,
    selectedStrategy,
    selectedStrategyVersions,
    selectedVersion,
    canCopyCurrentStrategy,
    canStartPaperRun,
    strategyCapabilityHint,
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
    ready,
    controlPanel,
    historyPanel,
  }
}

export type BacktestPageState = ReturnType<typeof useBacktestPage>
