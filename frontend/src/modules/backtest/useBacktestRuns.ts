import { computed, ref, type ComputedRef } from 'vue'

import { useBacktestRunChart } from './useBacktestRunChart'
import { useBacktestRunExecution } from './useBacktestRunExecution'
import { useBacktestRunFormatting } from './useBacktestRunFormatting'
import { useBacktestRunHistory } from './useBacktestRunHistory'

export type BacktestRunMode = 'backtest' | 'paper'

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
  const backtestLoading = ref(false)
  const paperLoading = ref(false)
  const isBusy = computed(() => backtestLoading.value || paperLoading.value)
  const history = ref<any[]>([])
  const paperHistory = ref<any[]>([])
  const historyMode = ref<'backtest' | 'paper'>('backtest')
  const selectedRun = ref<any | null>(null)
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
  const execution = useBacktestRunExecution({
    t,
    config,
    backtestLoading,
    paperLoading,
    historyMode,
    symbolsText,
    fetchHistory: historyActions.fetchHistory,
    fetchPaperHistory: historyActions.fetchPaperHistory,
  })

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
