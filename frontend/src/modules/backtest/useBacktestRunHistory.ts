import type { ComputedRef, Ref } from 'vue'

import { backtestApi } from './api'
import type { BacktestRunMode } from './useBacktestRuns'


interface BacktestRunTarget {
  id: number
  mode: BacktestRunMode
}

interface UseBacktestRunHistoryOptions {
  t: (key: string) => string
  history: Ref<any[]>
  paperHistory: Ref<any[]>
  historyMode: Ref<'backtest' | 'paper'>
  selectedRun: Ref<any | null>
  selectedRunMode: Ref<'backtest' | 'paper' | null>
  compareRunIds: Ref<number[]>
  versionCompareSelections: Ref<number[]>
  versionCompareOptions: ComputedRef<any[]>
  loadChart: (run: any) => Promise<void>
  clearChart: () => void
}

export const useBacktestRunHistory = ({
  t,
  history,
  paperHistory,
  historyMode,
  selectedRun,
  selectedRunMode,
  compareRunIds,
  versionCompareSelections,
  versionCompareOptions,
  loadChart,
  clearChart,
}: UseBacktestRunHistoryOptions) => {
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

  const loadRunTarget = async (target: BacktestRunTarget) => {
    if (target.mode === 'paper') return loadPaperResult(target.id)
    return loadResult(target.id)
  }

  const clearSelectedRun = () => {
    selectedRun.value = null
    selectedRunMode.value = null
    clearChart()
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

  const clearDeletedSelection = (runId: number, mode: BacktestRunMode) => {
    if (mode === 'backtest') {
      compareRunIds.value = compareRunIds.value.filter((item) => item !== runId)
    }
    if (selectedRun.value?.id === runId && selectedRunMode.value === mode) {
      clearSelectedRun()
    }
  }

  const deleteRun = async (runId: number, mode: BacktestRunMode) => {
    const confirmed = window.confirm(
      mode === 'paper'
        ? t('backtest.confirmDeletePaperRun')
        : t('backtest.confirmDeleteRun')
    )
    if (!confirmed) return

    try {
      if (mode === 'paper') {
        await backtestApi.deletePaperRun(runId)
        clearDeletedSelection(runId, 'paper')
        await fetchPaperHistory()
        return
      }

      await backtestApi.deleteRun(runId)
      clearDeletedSelection(runId, 'backtest')
      await fetchHistory()
    } catch (error: any) {
      alert(
        mode === 'paper'
          ? `${t('backtest.deletePaperRunFailed')}: ${error.message}`
          : `${t('backtest.deleteRunFailed')}: ${error.message}`
      )
    }
  }

  const refreshPaperSelection = async () => {
    await fetchPaperHistory()
    if (selectedRunMode.value === 'paper' && selectedRun.value?.id) {
      await loadPaperResult(selectedRun.value.id)
    }
  }

  return {
    fetchHistory,
    fetchPaperHistory,
    loadResult,
    loadPaperResult,
    loadRunTarget,
    clearSelectedRun,
    stopPaperRun,
    deleteRun,
    refreshPaperSelection,
  }
}
