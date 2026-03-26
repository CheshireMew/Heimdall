import { computed, reactive, ref, type ComputedRef } from 'vue'

import { marketApi } from '@/modules/market'

import { backtestApi } from './api'
import { asNumber } from './format'

export type BacktestRunMode = 'backtest' | 'paper'

interface BacktestRunTarget {
  id: number
  mode: BacktestRunMode
}

interface UseBacktestRunsOptions {
  t: (key: string) => string
  config: any
  selectedStrategyVersions: ComputedRef<any[]>
}


export const useBacktestRuns = ({
  t,
  config,
  selectedStrategyVersions,
}: UseBacktestRunsOptions) => {
  const loading = ref(false)
  const history = ref<any[]>([])
  const paperHistory = ref<any[]>([])
  const historyMode = ref<'backtest' | 'paper'>('backtest')
  const selectedRun = ref<any | null>(null)
  const selectedRunMode = ref<'backtest' | 'paper' | null>(null)
  const chartData = reactive({ candles: [] as any[], volume: [] as any[] })
  const symbolsText = ref('BTC/USDT, ETH/USDT')
  const compareRunIds = ref<number[]>([])
  const versionCompareSelections = ref<number[]>([])

  const visibleHistory = computed(() => (historyMode.value === 'paper' ? paperHistory.value : history.value))
  const isPaperRun = computed(() => selectedRunMode.value === 'paper' || selectedRun.value?.metadata?.execution_mode === 'paper_live')
  const pairBreakdown = computed(() => selectedRun.value?.report?.pair_breakdown || [])
  const optimizationTrials = computed(() => (isPaperRun.value ? [] : (selectedRun.value?.report?.research?.optimization?.trials || [])))
  const rollingWindows = computed(() => (isPaperRun.value ? [] : (selectedRun.value?.report?.research?.rolling_windows || [])))
  const selectedCompareRuns = computed(() => compareRunIds.value.map((id) => history.value.find((run) => run.id === id)).filter(Boolean))
  const latestRunsByVersion = computed(() => {
    const runs = [...history.value]
      .filter((run) => run.metadata?.strategy_key === config.strategy_key && run.metadata?.strategy_version)
      .sort((left, right) => {
        const leftTime = new Date(left.created_at || 0).getTime()
        const rightTime = new Date(right.created_at || 0).getTime()
        if (leftTime !== rightTime) return rightTime - leftTime
        return right.id - left.id
      })
    const map = new Map()
    for (const run of runs) {
      const version = Number(run.metadata?.strategy_version)
      if (!map.has(version)) map.set(version, run)
    }
    return map
  })
  const versionCompareOptions = computed(() => selectedStrategyVersions.value
    .map((version: any) => ({ version: version.version, name: version.name, run: latestRunsByVersion.value.get(version.version) }))
    .filter((item) => item.run))
  const selectedVersionCompareRuns = computed(() => versionCompareSelections.value
    .map((version) => versionCompareOptions.value.find((item) => item.version === version)?.run)
    .filter(Boolean))

  const buildComparisonChart = (runs: any[], labeler: (run: any) => string) => ({
    performance: {
      categories: runs.map(labeler),
      series: [
        { name: t('backtest.totalReturn'), color: '#2563eb', data: runs.map((run) => asNumber(run.report?.profit_pct) ?? 0) },
        { name: t('backtest.maxDrawdown'), color: '#ef4444', data: runs.map((run) => asNumber(run.report?.max_drawdown_pct) ?? 0) },
      ],
    },
    quality: {
      categories: runs.map(labeler),
      series: [
        { name: t('backtest.sharpe'), color: '#14b8a6', data: runs.map((run) => asNumber(run.report?.sharpe) ?? 0) },
        { name: t('backtest.winRate'), color: '#8b5cf6', data: runs.map((run) => asNumber(run.report?.win_rate) ?? 0) },
      ],
    },
  })

  const recentRunCompare = computed(() => buildComparisonChart(selectedCompareRuns.value, compareRunLabel))
  const versionRunCompare = computed(() => buildComparisonChart(selectedVersionCompareRuns.value, (run) => `v${run.metadata?.strategy_version || '-'}`))

  const toggleCompareRun = (runId: number) => {
    if (compareRunIds.value.includes(runId)) {
      compareRunIds.value = compareRunIds.value.filter((item) => item !== runId)
      return
    }
    compareRunIds.value = [...compareRunIds.value, runId]
  }

  const toggleVersionCompare = (version: number) => {
    if (versionCompareSelections.value.includes(version)) {
      versionCompareSelections.value = versionCompareSelections.value.filter((item) => item !== version)
      return
    }
    versionCompareSelections.value = [...versionCompareSelections.value, version]
  }

  const joinSymbols = (symbols: string[] | undefined) => (Array.isArray(symbols) && symbols.length ? symbols.join(', ') : '-')
  const portfolioLabel = (run: any) => run?.metadata?.portfolio_label || joinSymbols(run?.metadata?.symbols) || run?.symbol || '-'
  const previewValue = (value: unknown) => {
    if (Array.isArray(value)) return `${value.length}项`
    if (value && typeof value === 'object') return `${Object.keys(value as Record<string, unknown>).length}项`
    return value ?? '-'
  }
  const configLabel = (value: Record<string, unknown> | null | undefined) => (
    value
      ? Object.entries(value).slice(0, 3).map(([key, item]) => `${key}:${previewValue(item)}`).join(' · ')
      : '-'
  )
  const compareRunLabel = (run: any) => `#${run.id} · v${run.metadata?.strategy_version || '-'}`
  const runStatusLabel = (run: any) => (run?.status || '-').toUpperCase()

  const fetchHistory = async () => {
    try {
      const res = await backtestApi.listRuns()
      history.value = res.data
      const validRunIds = new Set(history.value.map((run) => run.id))
      compareRunIds.value = compareRunIds.value.filter((item) => validRunIds.has(item))
      const validVersions = new Set(versionCompareOptions.value.map((item) => item.version))
      versionCompareSelections.value = versionCompareSelections.value.filter((item) => validVersions.has(item))
    } catch (error) {
      console.error(error)
    }
  }

  const fetchPaperHistory = async () => {
    try {
      const res = await backtestApi.listPaperRuns()
      paperHistory.value = res.data
    } catch (error) {
      console.error(error)
    }
  }

  const buildPayload = () => ({
    strategy_key: config.strategy_key,
    strategy_version: config.strategy_version,
    timeframe: config.timeframe,
    days: config.days,
    initial_cash: config.initial_cash,
    fee_rate: config.fee_rate,
    portfolio: {
      symbols: symbolsText.value.split(',').map((item) => item.trim()).filter(Boolean),
      max_open_trades: config.portfolio.max_open_trades,
      position_size_pct: config.portfolio.position_size_pct,
      stake_mode: config.portfolio.stake_mode,
    },
    research: {
      slippage_bps: config.research.slippage_bps,
      funding_rate_daily: config.research.funding_rate_daily,
      in_sample_ratio: config.research.in_sample_ratio,
      optimize_metric: config.research.optimize_metric,
      optimize_trials: config.research.optimize_trials,
      rolling_windows: config.research.rolling_windows,
    },
  })

  const buildPaperPayload = () => ({
    strategy_key: config.strategy_key,
    strategy_version: config.strategy_version,
    timeframe: config.timeframe,
    initial_cash: config.initial_cash,
    fee_rate: config.fee_rate,
    portfolio: {
      symbols: symbolsText.value.split(',').map((item) => item.trim()).filter(Boolean),
      max_open_trades: config.portfolio.max_open_trades,
      position_size_pct: config.portfolio.position_size_pct,
      stake_mode: config.portfolio.stake_mode,
    },
  })

  const loadChart = async (run: any) => {
    const targetSymbol = Array.isArray(run?.metadata?.symbols) && run.metadata.symbols.length ? run.metadata.symbols[0] : run?.symbol
    if (!targetSymbol || targetSymbol === 'PORTFOLIO' || !run?.start_date) {
      chartData.candles = []
      chartData.volume = []
      return
    }
    const startDate = run.start_date.slice(0, 10)
    const endTs = run.end_date ? new Date(run.end_date).getTime() : Date.now()
    const res = await marketApi.getFullHistory({ symbol: targetSymbol, timeframe: run.timeframe, start_date: startDate })
    const candles = (res.data || []).filter((item: any[]) => item[0] <= endTs)
    chartData.candles = candles.map((item: any[]) => ({ time: item[0] / 1000, open: item[1], high: item[2], low: item[3], close: item[4] }))
    chartData.volume = candles.map((item: any[]) => ({
      time: item[0] / 1000,
      value: item[5],
      color: item[4] >= item[1] ? 'rgba(16, 185, 129, 0.5)' : 'rgba(239, 68, 68, 0.5)',
    }))
  }

  const loadResult = async (id: number) => {
    try {
      const res = await backtestApi.getRun(id)
      selectedRun.value = res.data
      selectedRunMode.value = 'backtest'
      historyMode.value = 'backtest'
      if (!compareRunIds.value.includes(id)) compareRunIds.value = [...compareRunIds.value, id]
      await loadChart(res.data)
      return res.data
    } catch (error) {
      console.error(error)
      return null
    }
  }

  const loadPaperResult = async (id: number) => {
    try {
      const res = await backtestApi.getPaperRun(id)
      selectedRun.value = res.data
      selectedRunMode.value = 'paper'
      historyMode.value = 'paper'
      await loadChart(res.data)
      return res.data
    } catch (error) {
      console.error(error)
      return null
    }
  }

  const startBacktest = async () => {
    loading.value = true
    try {
      const res = await backtestApi.startRun(buildPayload())
      if (res.data.success) {
        historyMode.value = 'backtest'
        await fetchHistory()
        return { id: res.data.backtest_id, mode: 'backtest' as const }
      }
    } catch (error: any) {
      alert(`${t('backtest.failed')}: ${error.message}`)
    } finally {
      loading.value = false
    }
    return null
  }

  const startPaperRun = async () => {
    loading.value = true
    try {
      const res = await backtestApi.startPaperRun(buildPaperPayload())
      if (res.data.success) {
        historyMode.value = 'paper'
        await fetchPaperHistory()
        return { id: res.data.run_id, mode: 'paper' as const }
      }
    } catch (error: any) {
      alert(`${t('backtest.paperFailed')}: ${error.message}`)
    } finally {
      loading.value = false
    }
    return null
  }

  const loadRunTarget = async (target: BacktestRunTarget) => {
    if (target.mode === 'paper') return loadPaperResult(target.id)
    return loadResult(target.id)
  }

  const clearSelectedRun = () => {
    selectedRun.value = null
    selectedRunMode.value = null
    chartData.candles = []
    chartData.volume = []
  }

  const stopPaperRun = async (runId: number) => {
    try {
      await backtestApi.stopPaperRun(runId)
      await fetchPaperHistory()
      if (selectedRunMode.value === 'paper' && selectedRun.value?.id === runId) {
        await loadPaperResult(runId)
      }
    } catch (error: any) {
      alert(`${t('backtest.paperStopFailed')}: ${error.message}`)
    }
  }

  const refreshPaperSelection = async () => {
    await fetchPaperHistory()
    if (selectedRunMode.value === 'paper' && selectedRun.value?.id) {
      await loadPaperResult(selectedRun.value.id)
    }
  }

  return {
    loading,
    history,
    paperHistory,
    historyMode,
    visibleHistory,
    selectedRun,
    selectedRunMode,
    isPaperRun,
    chartData,
    symbolsText,
    compareRunIds,
    versionCompareSelections,
    pairBreakdown,
    optimizationTrials,
    rollingWindows,
    selectedCompareRuns,
    latestRunsByVersion,
    versionCompareOptions,
    selectedVersionCompareRuns,
    recentRunCompare,
    versionRunCompare,
    toggleCompareRun,
    toggleVersionCompare,
    joinSymbols,
    portfolioLabel,
    configLabel,
    compareRunLabel,
    runStatusLabel,
    fetchHistory,
    fetchPaperHistory,
    buildPayload,
    buildPaperPayload,
    loadChart,
    loadResult,
    loadPaperResult,
    loadRunTarget,
    clearSelectedRun,
    startBacktest,
    startPaperRun,
    stopPaperRun,
    refreshPaperSelection,
  }
}
