import { computed, reactive, ref } from 'vue'
import { API_BODY_DEFAULTS } from '@/api/routes'
import type { FactorBlend, FactorCatalogItem, FactorCatalogResponse, FactorDetail, FactorExecutionRequest, FactorResearchRequest, FactorResearchRun, FactorResearchSummary, FactorScorecard } from './contracts'

export type FactorResearchForm = Required<FactorResearchRequest>
export type FactorExecutionForm = Required<FactorExecutionRequest>

export const createFactorResearchForm = (): FactorResearchForm => ({
  symbol: API_BODY_DEFAULTS.analyze_factors.symbol,
  timeframe: API_BODY_DEFAULTS.analyze_factors.timeframe as '1h' | '4h' | '1d',
  days: API_BODY_DEFAULTS.analyze_factors.days,
  horizon_bars: API_BODY_DEFAULTS.analyze_factors.horizon_bars,
  max_lag_bars: API_BODY_DEFAULTS.analyze_factors.max_lag_bars,
  categories: [...API_BODY_DEFAULTS.analyze_factors.categories] as string[],
  factor_ids: [...API_BODY_DEFAULTS.analyze_factors.factor_ids] as string[],
})

export const createFactorExecutionForm = (): FactorExecutionForm => ({
  initial_cash: API_BODY_DEFAULTS.start_factor_backtest.initial_cash,
  fee_rate: API_BODY_DEFAULTS.start_factor_backtest.fee_rate,
  position_size_pct: API_BODY_DEFAULTS.start_factor_backtest.position_size_pct,
  stake_mode: API_BODY_DEFAULTS.start_factor_backtest.stake_mode as 'fixed' | 'unlimited',
  entry_threshold: API_BODY_DEFAULTS.start_factor_backtest.entry_threshold as number | null,
  exit_threshold: API_BODY_DEFAULTS.start_factor_backtest.exit_threshold as number | null,
  stoploss_pct: API_BODY_DEFAULTS.start_factor_backtest.stoploss_pct,
  takeprofit_pct: API_BODY_DEFAULTS.start_factor_backtest.takeprofit_pct,
  max_hold_bars: API_BODY_DEFAULTS.start_factor_backtest.max_hold_bars,
})

export const createFactorResearchState = () => {
  const loading = ref(false)
  const catalogLoading = ref(false)
  const runsLoading = ref(false)
  const executionLoading = ref<'backtest' | 'paper' | ''>('')
  const error = ref('')
  const catalog = reactive({
    symbols: [] as string[],
    timeframes: [] as string[],
    categories: [] as string[],
    factors: [] as FactorCatalogItem[],
    forward_horizons: [] as number[],
    cleaning: {} as FactorCatalogResponse['cleaning'],
  })
  const form = reactive(createFactorResearchForm())
  const executionForm = reactive(createFactorExecutionForm())
  const runs = ref<FactorResearchRun[]>([])
  const summary = ref<FactorResearchSummary | null>(null)
  const ranking = ref<FactorScorecard[]>([])
  const details = ref<FactorDetail[]>([])
  const blend = ref<FactorBlend | null>(null)
  const selectedFactorId = ref('')
  const selectedRunId = ref<number | null>(null)

  const factorPool = computed(() => {
    if (!form.categories.length) return catalog.factors
    return catalog.factors.filter((item) => form.categories.includes(item.category))
  })
  const selectedDetail = computed(() => details.value.find((item) => item.factor_id === selectedFactorId.value) || details.value[0] || null)
  const selectedRun = computed(() => runs.value.find((item) => item.id === selectedRunId.value) || null)
  const selectedFactorLookup = computed(() => new Set(form.factor_ids))
  const useAllFactors = computed(() => !form.factor_ids.length)

  return {
    loading,
    catalogLoading,
    runsLoading,
    executionLoading,
    error,
    catalog,
    form,
    executionForm,
    runs,
    summary,
    ranking,
    details,
    blend,
    selectedFactorId,
    selectedRunId,
    factorPool,
    selectedDetail,
    selectedRun,
    selectedFactorLookup,
    useAllFactors,
  }
}

export type FactorResearchState = ReturnType<typeof createFactorResearchState>
