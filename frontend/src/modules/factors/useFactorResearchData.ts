import { onMounted } from 'vue'
import type { Router } from 'vue-router'

import { factorApi } from './api'
import type { FactorResearchState } from './state'
import type { FactorResearchRunDetail } from '@/types'

const responseErrorDetail = (error: unknown): string | null => {
  if (!error || typeof error !== 'object' || !('response' in error)) return null
  const response = (error as { response?: { data?: { detail?: unknown } } }).response
  const detail = response?.data?.detail
  return typeof detail === 'string' ? detail : null
}

export const useFactorResearchData = (
  state: FactorResearchState,
  applyRun: (run: FactorResearchRunDetail) => void,
  t: (key: string) => string,
  router: Router,
) => {
  const fetchCatalog = async () => {
    state.catalogLoading.value = true
    try {
      const response = await factorApi.getCatalog()
      state.catalog.symbols = response.data.symbols || []
      state.catalog.timeframes = response.data.timeframes || []
      state.catalog.categories = response.data.categories || []
      state.catalog.factors = response.data.factors || []
      state.catalog.forward_horizons = response.data.forward_horizons || []
      state.catalog.cleaning = response.data.cleaning || {}
      if (state.catalog.symbols.length && !state.catalog.symbols.includes(state.form.symbol)) state.form.symbol = state.catalog.symbols[0]
      if (state.catalog.timeframes.length && !state.catalog.timeframes.includes(state.form.timeframe)) state.form.timeframe = state.catalog.timeframes[0] as typeof state.form.timeframe
      if (!state.form.categories.length) state.form.categories = [...state.catalog.categories]
    } catch (err) {
      console.error('Failed to load factor catalog', err)
      state.error.value = t('factorResearch.catalogFailed')
    } finally {
      state.catalogLoading.value = false
    }
  }

  const fetchRuns = async () => {
    state.runsLoading.value = true
    try {
      const response = await factorApi.listRuns()
      state.runs.value = response.data || []
      if (!state.selectedRunId.value && state.runs.value.length) {
        const latest = await factorApi.getRun(state.runs.value[0].id)
        applyRun(latest.data)
      }
    } catch (err) {
      console.error('Failed to load factor runs', err)
    } finally {
      state.runsLoading.value = false
    }
  }

  const loadRun = async (runId: number) => {
    const response = await factorApi.getRun(runId)
    const run = response.data
    const existingIndex = state.runs.value.findIndex((item) => item.id === run.id)
    if (existingIndex >= 0) state.runs.value.splice(existingIndex, 1, run)
    else state.runs.value.unshift(run)
    applyRun(run)
  }

  const runAnalysis = async () => {
    state.loading.value = true
    state.error.value = ''
    try {
      const response = await factorApi.analyze({
        symbol: state.form.symbol,
        timeframe: state.form.timeframe,
        days: state.form.days,
        horizon_bars: state.form.horizon_bars,
        max_lag_bars: state.form.max_lag_bars,
        categories: [...state.form.categories],
        factor_ids: [...state.form.factor_ids],
      })
      state.summary.value = response.data.summary
      state.ranking.value = response.data.ranking || []
      state.details.value = response.data.details || []
      state.blend.value = response.data.blend || null
      state.selectedRunId.value = response.data.run_id
      if (!state.selectedDetail.value || !state.details.value.find((item) => item.factor_id === state.selectedFactorId.value)) {
        state.selectedFactorId.value = state.details.value[0]?.factor_id || ''
      }
      state.executionForm.entry_threshold = response.data.blend?.entry_threshold ?? null
      state.executionForm.exit_threshold = response.data.blend?.exit_threshold ?? null
      await fetchRuns()
      if (response.data.run_id) {
        await loadRun(response.data.run_id)
      }
    } catch (err: unknown) {
      console.error('Failed to analyze factors', err)
      state.error.value = responseErrorDetail(err) || t('factorResearch.analysisFailed')
      state.ranking.value = []
      state.details.value = []
      state.summary.value = null
      state.blend.value = null
      state.selectedFactorId.value = ''
    } finally {
      state.loading.value = false
    }
  }

  const startExecution = async (mode: 'backtest' | 'paper') => {
    if (!state.selectedRunId.value) return
    state.executionLoading.value = mode
    state.error.value = ''
    try {
      const body = {
        initial_cash: state.executionForm.initial_cash,
        fee_rate: state.executionForm.fee_rate,
        position_size_pct: state.executionForm.position_size_pct,
        stake_mode: state.executionForm.stake_mode,
        entry_threshold: state.executionForm.entry_threshold,
        exit_threshold: state.executionForm.exit_threshold,
        stoploss_pct: state.executionForm.stoploss_pct,
        takeprofit_pct: state.executionForm.takeprofit_pct,
        max_hold_bars: state.executionForm.max_hold_bars,
      }
      const response = mode === 'backtest'
        ? await factorApi.startBacktest(state.selectedRunId.value, body)
        : await factorApi.startPaper(state.selectedRunId.value, body)
      router.push(mode === 'backtest' ? `/backtest/runs/${response.data.run_id}` : `/backtest/paper/${response.data.run_id}`)
    } catch (err: unknown) {
      console.error('Failed to start factor execution', err)
      state.error.value = responseErrorDetail(err) || t('factorResearch.executionFailed')
    } finally {
      state.executionLoading.value = ''
    }
  }

  onMounted(async () => {
    await Promise.all([fetchCatalog(), fetchRuns()])
    if (state.error.value) return
    if (state.selectedRunId.value) {
      try {
        await loadRun(state.selectedRunId.value)
        return
      } catch (err) {
        console.warn('Failed to restore factor run, falling back to analysis', err)
        state.selectedRunId.value = null
      }
    }
    if (!state.summary.value) await runAnalysis()
  })

  return {
    fetchCatalog,
    fetchRuns,
    loadRun,
    runAnalysis,
    startExecution,
  }
}
