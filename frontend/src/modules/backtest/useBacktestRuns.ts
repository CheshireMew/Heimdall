import { computed, ref, type ComputedRef } from 'vue'

import type { BacktestDetailResponse, BacktestRun, StrategyVersion } from './contracts'

import { useBacktestRunChart } from './useBacktestRunChart'
import { useBacktestRunExecution } from './useBacktestRunExecution'
import { useBacktestRunFormatting } from './useBacktestRunFormatting'
import { useBacktestRunHistory } from './useBacktestRunHistory'
import type { BacktestPageConfig, BacktestRunSelectionConfig } from './viewTypes'

export type BacktestRunMode = 'backtest' | 'paper'

interface UseBacktestRunsOptions {
  t: (key: string) => string
  config: BacktestRunSelectionConfig
  executionConfig?: BacktestPageConfig
  selectedStrategyVersions: ComputedRef<StrategyVersion[]>
}

export const useBacktestRuns = ({
  t,
  config,
  executionConfig,
  selectedStrategyVersions,
}: UseBacktestRunsOptions) => {
  const backtestLoading = ref(false)
  const paperLoading = ref(false)
  const isBusy = computed(() => backtestLoading.value || paperLoading.value)
  const history = ref<BacktestRun[]>([])
  const paperHistory = ref<BacktestRun[]>([])
  const historyMode = ref<'backtest' | 'paper'>('backtest')
  const selectedRun = ref<BacktestDetailResponse | null>(null)
  const selectedRunMode = ref<'backtest' | 'paper' | null>(null)
  const symbolsText = ref('BTC/USDT, ETH/USDT')
  const compareRunIds = ref<number[]>([])
  const versionCompareSelections = ref<number[]>([])

  const chart = useBacktestRunChart()
  const formatting = useBacktestRunFormatting({
    t,
    config,
    selectedStrategyVersions,
    history,
    paperHistory,
    historyMode,
    selectedRun,
    selectedRunMode,
    compareRunIds,
    versionCompareSelections,
  })
  const historyActions = useBacktestRunHistory({
    t,
    history,
    paperHistory,
    historyMode,
    selectedRun,
    selectedRunMode,
    compareRunIds,
    versionCompareSelections,
    versionCompareOptions: formatting.versionCompareOptions,
    loadChart: chart.loadChart,
    clearChart: chart.clearChart,
  })
  const execution = executionConfig
    ? useBacktestRunExecution({
        t,
        config: executionConfig,
        backtestLoading,
        paperLoading,
        historyMode,
        symbolsText,
        fetchHistory: historyActions.fetchHistory,
        fetchPaperHistory: historyActions.fetchPaperHistory,
      })
    : {
        buildPayload: () => null,
        buildPaperPayload: () => null,
        startBacktest: async () => null,
        startPaperRun: async () => null,
      }

  return {
    backtestLoading,
    paperLoading,
    isBusy,
    history,
    paperHistory,
    historyMode,
    selectedRun,
    selectedRunMode,
    chartData: chart.chartData,
    symbolsText,
    compareRunIds,
    versionCompareSelections,
    ...formatting,
    ...historyActions,
    ...execution,
  }
}
