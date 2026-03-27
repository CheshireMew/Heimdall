import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import { useTheme } from '@/composables/useTheme'
import type { FactorDetail, FactorResearchRun, FactorScorecard } from '@/types'

import { factorApi } from './api'


export const useFactorResearchPage = () => {
  const { t } = useI18n()
  const { theme } = useTheme()
  const router = useRouter()

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
  const form = reactive({
    symbol: 'BTC/USDT',
    timeframe: '1d' as '1h' | '4h' | '1d',
    days: 365,
    horizon_bars: 3,
    max_lag_bars: 7,
    categories: [] as string[],
    factor_ids: [] as string[],
  })
  const executionForm = reactive({
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
  const runs = ref<FactorResearchRun[]>([])
  const summary = ref<any | null>(null)
  const ranking = ref<FactorScorecard[]>([])
  const details = ref<FactorDetail[]>([])
  const blend = ref<any | null>(null)
  const selectedFactorId = ref('')
  const selectedRunId = ref<number | null>(null)

  const isDark = computed(() => theme.value === 'dark')
  const factorPool = computed(() => {
    if (!form.categories.length) return catalog.factors
    return catalog.factors.filter((item) => form.categories.includes(item.category))
  })
  const selectedDetail = computed(() => details.value.find((item) => item.factor_id === selectedFactorId.value) || details.value[0] || null)
  const selectedRun = computed(() => runs.value.find((item) => item.id === selectedRunId.value) || null)
  const selectedFactorLookup = computed(() => new Set(form.factor_ids))
  const useAllFactors = computed(() => !form.factor_ids.length)

  const applyRun = (run: FactorResearchRun) => {
    selectedRunId.value = run.id
    summary.value = run.summary
    ranking.value = run.ranking || []
    details.value = run.details || []
    blend.value = run.blend || null
    selectedFactorId.value = details.value[0]?.factor_id || ''

    const request = run.request || {}
    form.symbol = String(request.symbol || form.symbol)
    form.timeframe = (request.timeframe as typeof form.timeframe) || form.timeframe
    form.days = Number(request.days || form.days)
    form.horizon_bars = Number(request.horizon_bars || form.horizon_bars)
    form.max_lag_bars = Number(request.max_lag_bars || form.max_lag_bars)
    form.categories = Array.isArray(request.categories) ? [...(request.categories as string[])] : []
    form.factor_ids = Array.isArray(request.factor_ids) ? [...(request.factor_ids as string[])] : []

    executionForm.entry_threshold = typeof run.blend?.entry_threshold === 'number' ? run.blend.entry_threshold : null
    executionForm.exit_threshold = typeof run.blend?.exit_threshold === 'number' ? run.blend.exit_threshold : null
  }

  const fetchCatalog = async () => {
    catalogLoading.value = true
    try {
      const response = await factorApi.getCatalog()
      catalog.symbols = response.data.symbols || []
      catalog.timeframes = response.data.timeframes || []
      catalog.categories = response.data.categories || []
      catalog.factors = response.data.factors || []
      catalog.forward_horizons = response.data.forward_horizons || []
      catalog.cleaning = response.data.cleaning || {}
      if (catalog.symbols.length && !catalog.symbols.includes(form.symbol)) form.symbol = catalog.symbols[0]
      if (catalog.timeframes.length && !catalog.timeframes.includes(form.timeframe)) form.timeframe = catalog.timeframes[0] as typeof form.timeframe
      if (!form.categories.length) form.categories = [...catalog.categories]
    } catch (err) {
      console.error('Failed to load factor catalog', err)
      error.value = t('factorResearch.catalogFailed')
    } finally {
      catalogLoading.value = false
    }
  }

  const fetchRuns = async () => {
    runsLoading.value = true
    try {
      const response = await factorApi.listRuns()
      runs.value = response.data || []
      if (!selectedRunId.value && runs.value.length) {
        const latest = await factorApi.getRun(runs.value[0].id)
        applyRun(latest.data)
      }
    } catch (err) {
      console.error('Failed to load factor runs', err)
    } finally {
      runsLoading.value = false
    }
  }

  const loadRun = async (runId: number) => {
    const response = await factorApi.getRun(runId)
    const run = response.data
    const existingIndex = runs.value.findIndex((item) => item.id === run.id)
    if (existingIndex >= 0) runs.value.splice(existingIndex, 1, run)
    else runs.value.unshift(run)
    applyRun(run)
  }

  const runAnalysis = async () => {
    loading.value = true
    error.value = ''
    try {
      const response = await factorApi.analyze({
        symbol: form.symbol,
        timeframe: form.timeframe,
        days: form.days,
        horizon_bars: form.horizon_bars,
        max_lag_bars: form.max_lag_bars,
        categories: [...form.categories],
        factor_ids: [...form.factor_ids],
      })
      summary.value = response.data.summary
      ranking.value = response.data.ranking || []
      details.value = response.data.details || []
      blend.value = response.data.blend || null
      selectedRunId.value = response.data.run_id
      if (!selectedDetail.value || !details.value.find((item) => item.factor_id === selectedFactorId.value)) {
        selectedFactorId.value = details.value[0]?.factor_id || ''
      }
      executionForm.entry_threshold = response.data.blend?.entry_threshold ?? null
      executionForm.exit_threshold = response.data.blend?.exit_threshold ?? null
      await fetchRuns()
      if (response.data.run_id) {
        await loadRun(response.data.run_id)
      }
    } catch (err: any) {
      console.error('Failed to analyze factors', err)
      error.value = err?.response?.data?.detail || t('factorResearch.analysisFailed')
      ranking.value = []
      details.value = []
      summary.value = null
      blend.value = null
      selectedFactorId.value = ''
    } finally {
      loading.value = false
    }
  }

  const startExecution = async (mode: 'backtest' | 'paper') => {
    if (!selectedRunId.value) return
    executionLoading.value = mode
    error.value = ''
    try {
      const body = {
        initial_cash: executionForm.initial_cash,
        fee_rate: executionForm.fee_rate,
        position_size_pct: executionForm.position_size_pct,
        stake_mode: executionForm.stake_mode,
        entry_threshold: executionForm.entry_threshold,
        exit_threshold: executionForm.exit_threshold,
        stoploss_pct: executionForm.stoploss_pct,
        takeprofit_pct: executionForm.takeprofit_pct,
        max_hold_bars: executionForm.max_hold_bars,
      }
      const response = mode === 'backtest'
        ? await factorApi.startBacktest(selectedRunId.value, body)
        : await factorApi.startPaper(selectedRunId.value, body)
      router.push(mode === 'backtest' ? `/backtest/runs/${response.data.run_id}` : `/backtest/paper/${response.data.run_id}`)
    } catch (err: any) {
      console.error('Failed to start factor execution', err)
      error.value = err?.response?.data?.detail || t('factorResearch.executionFailed')
    } finally {
      executionLoading.value = ''
    }
  }

  const toggleCategory = (category: string) => {
    if (form.categories.includes(category)) {
      form.categories = form.categories.filter((item) => item !== category)
      return
    }
    form.categories = [...form.categories, category]
  }

  const resetFactorSelection = () => {
    form.factor_ids = []
  }

  const toggleFactor = (factorId: string) => {
    if (form.factor_ids.includes(factorId)) {
      form.factor_ids = form.factor_ids.filter((item) => item !== factorId)
      return
    }
    form.factor_ids = [...form.factor_ids, factorId]
  }

  const selectFactor = (factorId: string) => {
    selectedFactorId.value = factorId
  }

  const factorChipClass = (factorId: string) => {
    const active = useAllFactors.value || selectedFactorLookup.value.has(factorId)
    return active
      ? 'bg-cyan-600 text-white border-cyan-500'
      : 'bg-slate-100 text-slate-500 border-slate-200 dark:bg-slate-900 dark:text-slate-400 dark:border-slate-700'
  }

  const categoryChipClass = (category: string) => (
    form.categories.includes(category)
      ? 'bg-slate-900 text-white border-slate-700 dark:bg-cyan-600 dark:border-cyan-500'
      : 'bg-slate-100 text-slate-500 border-slate-200 dark:bg-slate-900 dark:text-slate-400 dark:border-slate-700'
  )

  const scoreClass = (score: number) => {
    if (score >= 70) return 'text-emerald-600 dark:text-emerald-400'
    if (score >= 45) return 'text-amber-600 dark:text-amber-300'
    return 'text-slate-500 dark:text-slate-400'
  }

  const correlationClass = (value: number) => {
    if (value > 0) return 'text-emerald-600 dark:text-emerald-400'
    if (value < 0) return 'text-rose-600 dark:text-rose-400'
    return 'text-slate-500 dark:text-slate-400'
  }

  const formatPct = (value: number | null | undefined, digits: number = 2) => {
    if (value === null || value === undefined || Number.isNaN(value)) return '--'
    return `${(value * 100).toFixed(digits)}%`
  }

  const formatNumber = (value: number | null | undefined, digits: number = 3) => {
    if (value === null || value === undefined || Number.isNaN(value)) return '--'
    return value.toLocaleString(undefined, { maximumFractionDigits: digits, minimumFractionDigits: 0 })
  }

  const formatDate = (value: string | null | undefined) => {
    if (!value) return '--'
    return new Date(value).toLocaleDateString()
  }

  watch(
    () => form.categories,
    () => {
      const poolIds = new Set(factorPool.value.map((item) => item.factor_id))
      form.factor_ids = form.factor_ids.filter((item) => poolIds.has(item))
    },
    { deep: true },
  )

  onMounted(async () => {
    await Promise.all([fetchCatalog(), fetchRuns()])
    if (!error.value && !summary.value) await runAnalysis()
  })

  return reactive({
    t,
    theme,
    isDark,
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
    factorPool,
    selectedRunId,
    selectedRun,
    selectedFactorId,
    selectedDetail,
    useAllFactors,
    fetchCatalog,
    fetchRuns,
    loadRun,
    runAnalysis,
    startExecution,
    toggleCategory,
    resetFactorSelection,
    toggleFactor,
    selectFactor,
    factorChipClass,
    categoryChipClass,
    scoreClass,
    correlationClass,
    formatPct,
    formatNumber,
    formatDate,
  })
}
