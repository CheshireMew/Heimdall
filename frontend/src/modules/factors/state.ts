import { computed, reactive, ref } from 'vue'
import type { FactorDetail, FactorResearchRun, FactorScorecard } from '@/types'

export const createFactorResearchForm = () => ({
  symbol: 'BTC/USDT',
  timeframe: '1d' as '1h' | '4h' | '1d',
  days: 365,
  horizon_bars: 3,
  max_lag_bars: 7,
  categories: [] as string[],
  factor_ids: [] as string[],
})

export const createFactorExecutionForm = () => ({
  initial_cash: 100000,
  fee_rate: 0.1,
  position_size_pct: 25,
  stake_mode: 'fixed' as 'fixed' | 'unlimited',
  entry_threshold: null as number | null,
  exit_threshold: null as number | null,
  stoploss_pct: -0.08,
  takeprofit_pct: 0.16,
  max_hold_bars: 20,
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
    factors: [] as any[],
    forward_horizons: [] as number[],
    cleaning: {} as Record<string, unknown>,
  })
  const form = reactive(createFactorResearchForm())
  const executionForm = reactive(createFactorExecutionForm())
  const runs = ref<FactorResearchRun[]>([])
  const summary = ref<any | null>(null)
  const ranking = ref<FactorScorecard[]>([])
  const details = ref<FactorDetail[]>([])
  const blend = ref<any | null>(null)
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
