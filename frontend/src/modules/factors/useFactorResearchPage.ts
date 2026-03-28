import { computed, reactive } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import {
  bindPageSnapshot,
  createPageSnapshot,
  isRecord,
  PAGE_SNAPSHOT_KEYS,
  readNumber,
  readString,
  readStringArray,
} from '@/composables/pageSnapshot'
import { useTheme } from '@/composables/useTheme'

import { createFactorExecutionForm, createFactorResearchForm, createFactorResearchState } from './state'
import { useFactorResearchData } from './useFactorResearchData'
import { useFactorResearchFormatting } from './useFactorResearchFormatting'
import { useFactorResearchSelection } from './useFactorResearchSelection'

interface FactorResearchSnapshot {
  form: ReturnType<typeof createFactorResearchForm>
  executionForm: ReturnType<typeof createFactorExecutionForm>
  selectedRunId: number | null
  selectedFactorId: string
}

const normalizeSnapshot = (value: unknown): FactorResearchSnapshot => {
  const defaultForm = createFactorResearchForm()
  const defaultExecutionForm = createFactorExecutionForm()
  if (!isRecord(value)) {
    return {
      form: defaultForm,
      executionForm: defaultExecutionForm,
      selectedRunId: null,
      selectedFactorId: '',
    }
  }

  const form = isRecord(value.form) ? value.form : {}
  const executionForm = isRecord(value.executionForm) ? value.executionForm : {}

  return {
    form: {
      symbol: readString(form.symbol, defaultForm.symbol),
      timeframe: ['1h', '4h', '1d'].includes(readString(form.timeframe, defaultForm.timeframe))
        ? readString(form.timeframe, defaultForm.timeframe) as typeof defaultForm.timeframe
        : defaultForm.timeframe,
      days: readNumber(form.days, defaultForm.days),
      horizon_bars: readNumber(form.horizon_bars, defaultForm.horizon_bars),
      max_lag_bars: readNumber(form.max_lag_bars, defaultForm.max_lag_bars),
      categories: readStringArray(form.categories),
      factor_ids: readStringArray(form.factor_ids),
    },
    executionForm: {
      initial_cash: readNumber(executionForm.initial_cash, defaultExecutionForm.initial_cash),
      fee_rate: readNumber(executionForm.fee_rate, defaultExecutionForm.fee_rate),
      position_size_pct: readNumber(executionForm.position_size_pct, defaultExecutionForm.position_size_pct),
      stake_mode: readString(executionForm.stake_mode, defaultExecutionForm.stake_mode) === 'unlimited' ? 'unlimited' : 'fixed',
      entry_threshold: typeof executionForm.entry_threshold === 'number' ? executionForm.entry_threshold : null,
      exit_threshold: typeof executionForm.exit_threshold === 'number' ? executionForm.exit_threshold : null,
      stoploss_pct: readNumber(executionForm.stoploss_pct, defaultExecutionForm.stoploss_pct),
      takeprofit_pct: readNumber(executionForm.takeprofit_pct, defaultExecutionForm.takeprofit_pct),
      max_hold_bars: readNumber(executionForm.max_hold_bars, defaultExecutionForm.max_hold_bars),
    },
    selectedRunId: typeof value.selectedRunId === 'number' ? value.selectedRunId : null,
    selectedFactorId: readString(value.selectedFactorId, ''),
  }
}


export const useFactorResearchPage = () => {
  const { t } = useI18n()
  const { theme } = useTheme()
  const router = useRouter()
  const pageSnapshot = createPageSnapshot(
    PAGE_SNAPSHOT_KEYS.factorResearch,
    normalizeSnapshot,
    {
      form: createFactorResearchForm(),
      executionForm: createFactorExecutionForm(),
      selectedRunId: null,
      selectedFactorId: '',
    },
  )
  const restoredSnapshot = pageSnapshot.load()

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

  bindPageSnapshot(
    [state.form, state.executionForm, state.selectedRunId, state.selectedFactorId],
    () => ({
      form: {
        symbol: readString(state.form.symbol, 'BTC/USDT'),
        timeframe: state.form.timeframe,
        days: readNumber(state.form.days, 365),
        horizon_bars: readNumber(state.form.horizon_bars, 3),
        max_lag_bars: readNumber(state.form.max_lag_bars, 7),
        categories: [...state.form.categories],
        factor_ids: [...state.form.factor_ids],
      },
      executionForm: {
        initial_cash: readNumber(state.executionForm.initial_cash, 100000),
        fee_rate: readNumber(state.executionForm.fee_rate, 0.1),
        position_size_pct: readNumber(state.executionForm.position_size_pct, 25),
        stake_mode: state.executionForm.stake_mode,
        entry_threshold: state.executionForm.entry_threshold,
        exit_threshold: state.executionForm.exit_threshold,
        stoploss_pct: readNumber(state.executionForm.stoploss_pct, -0.08),
        takeprofit_pct: readNumber(state.executionForm.takeprofit_pct, 0.16),
        max_hold_bars: readNumber(state.executionForm.max_hold_bars, 20),
      },
      selectedRunId: state.selectedRunId.value,
      selectedFactorId: readString(state.selectedFactorId.value, ''),
    }),
    pageSnapshot.save,
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
