import { computed, reactive } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import {
  createPersistentPageSnapshot,
  PAGE_SNAPSHOT_KEYS,
} from '@/composables/pageSnapshot'
import { useTheme } from '@/composables/useTheme'

import { buildFactorResearchSnapshot, createDefaultFactorResearchSnapshot, normalizeFactorResearchSnapshot } from './pageSnapshot'
import { createFactorResearchState } from './state'
import { useFactorResearchData } from './useFactorResearchData'
import { useFactorResearchFormatting } from './useFactorResearchFormatting'
import { useFactorResearchSelection } from './useFactorResearchSelection'


export const useFactorResearchPage = () => {
  const { t } = useI18n()
  const { theme } = useTheme()
  const router = useRouter()
  const pageSnapshot = createPersistentPageSnapshot(
    PAGE_SNAPSHOT_KEYS.factorResearch,
    normalizeFactorResearchSnapshot,
    createDefaultFactorResearchSnapshot(),
  )
  const restoredSnapshot = pageSnapshot.initial

  const state = createFactorResearchState()
  Object.assign(state.form, restoredSnapshot.form)
  Object.assign(state.executionForm, restoredSnapshot.executionForm)
  state.selectedRunId.value = restoredSnapshot.selectedRunId
  state.selectedFactorId.value = restoredSnapshot.selectedFactorId
  const isDark = computed(() => theme.value === 'dark')

  const selection = useFactorResearchSelection(state)
  const formatting = useFactorResearchFormatting(state)
  const data = useFactorResearchData(state, selection.applyRun, t, router)

  const heroPanel = reactive({
    catalog: state.catalog,
  })

  const filtersPanel = reactive({
    form: state.form,
    catalog: state.catalog,
    factorPool: state.factorPool,
    loading: state.loading,
    catalogLoading: state.catalogLoading,
    runAnalysis: data.runAnalysis,
    toggleCategory: selection.toggleCategory,
    resetFactorSelection: selection.resetFactorSelection,
    toggleFactor: selection.toggleFactor,
    categoryChipClass: formatting.categoryChipClass,
    factorChipClass: formatting.factorChipClass,
  })

  const summaryPanel = reactive({
    summary: state.summary,
    formatDate: formatting.formatDate,
  })

  const sidebarPanel = reactive({
    runsLoading: state.runsLoading,
    runs: state.runs,
    selectedRunId: state.selectedRunId,
    blend: state.blend,
    executionForm: state.executionForm,
    executionLoading: state.executionLoading,
    loadRun: data.loadRun,
    startExecution: data.startExecution,
    formatDate: formatting.formatDate,
    formatNumber: formatting.formatNumber,
    formatPct: formatting.formatPct,
    scoreClass: formatting.scoreClass,
  })

  const detailPanel = reactive({
    isDark,
    ranking: state.ranking,
    loading: state.loading,
    selectedFactorId: state.selectedFactorId,
    selectedDetail: state.selectedDetail,
    blend: state.blend,
    selectFactor: selection.selectFactor,
    scoreClass: formatting.scoreClass,
    correlationClass: formatting.correlationClass,
    formatNumber: formatting.formatNumber,
    formatPct: formatting.formatPct,
    formatDate: formatting.formatDate,
  })

  pageSnapshot.bind(
    [state.form, state.executionForm, state.selectedRunId, state.selectedFactorId],
    () => buildFactorResearchSnapshot({
      form: {
        symbol: state.form.symbol,
        timeframe: state.form.timeframe,
        days: state.form.days,
        horizon_bars: state.form.horizon_bars,
        max_lag_bars: state.form.max_lag_bars,
        categories: [...state.form.categories],
        factor_ids: [...state.form.factor_ids],
      },
      executionForm: {
        initial_cash: state.executionForm.initial_cash,
        fee_rate: state.executionForm.fee_rate,
        position_size_pct: state.executionForm.position_size_pct,
        stake_mode: state.executionForm.stake_mode,
        entry_threshold: state.executionForm.entry_threshold,
        exit_threshold: state.executionForm.exit_threshold,
        stoploss_pct: state.executionForm.stoploss_pct,
        takeprofit_pct: state.executionForm.takeprofit_pct,
        max_hold_bars: state.executionForm.max_hold_bars,
      },
      selectedRunId: state.selectedRunId.value,
      selectedFactorId: state.selectedFactorId.value,
    }),
  )

  return reactive({
    error: state.error,
    heroPanel,
    filtersPanel,
    summaryPanel,
    sidebarPanel,
    detailPanel,
  })
}
