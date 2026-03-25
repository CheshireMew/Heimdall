import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { useTheme } from '@/composables/useTheme'
import type { StrategyEditorContract } from '@/types'

import { backtestApi } from './api'
import { buildParameterSpaceJson, clone } from './editorContract'
import { asNumber } from './format'
import { useBacktestEditor } from './useBacktestEditor'
import { useBacktestRuns } from './useBacktestRuns'


export const useBacktestPage = () => {
  const { t } = useI18n()
  const { theme } = useTheme()

  const timeframes = ['1m', '5m', '15m', '1h', '4h', '1d']
  const optimizeMetrics = ['sharpe', 'profit_pct', 'calmar', 'profit_factor']
  const editorContract = ref<StrategyEditorContract | null>(null)
  const strategies = ref<any[]>([])
  const templates = ref<any[]>([])
  const indicators = ref<any[]>([])
  const indicatorEngines = ref<any[]>([])

  const config = reactive({
    strategy_key: 'ema_rsi_macd',
    strategy_version: 1,
    timeframe: '1h',
    days: 180,
    initial_cash: 100000,
    fee_rate: 0.1,
    portfolio: {
      max_open_trades: 2,
      position_size_pct: 25,
      stake_mode: 'fixed',
    },
    research: {
      slippage_bps: 5,
      funding_rate_daily: 0,
      in_sample_ratio: 70,
      optimize_metric: 'sharpe',
      optimize_trials: 12,
      rolling_windows: 3,
    },
  })

  const isDark = computed(() => theme.value === 'dark')
  const chartColors = computed(() => ({
    bg: isDark.value ? '#1f2937' : '#ffffff',
    grid: isDark.value ? '#374151' : '#e5e7eb',
    text: isDark.value ? '#9ca3af' : '#4b5563',
    upColor: '#10b981',
    downColor: '#ef4444',
  }))

  const selectedStrategy = computed(() => strategies.value.find((item) => item.key === config.strategy_key) || null)
  const selectedStrategyVersions = computed(() => selectedStrategy.value?.versions || [])
  const selectedVersion = computed(() => selectedStrategyVersions.value.find((item: any) => item.version === config.strategy_version) || null)

  const editor = useBacktestEditor({
    t,
    editorContract,
    templates,
    indicators,
    indicatorEngines,
    selectedStrategy,
    selectedVersion,
  })
  const runs = useBacktestRuns({
    t,
    config,
    selectedStrategyVersions,
  })

  const categoryLabel = (value: string) => {
    if (value === 'trend') return t('backtest.categoryTrend')
    if (value === 'mean_reversion') return t('backtest.categoryMeanReversion')
    if (value === 'breakout') return t('backtest.categoryBreakout')
    if (value === 'custom') return t('backtest.categoryCustom')
    return value || '-'
  }

  const profitColorClass = (value: unknown) => {
    const numeric = asNumber(value)
    if (numeric === null) return 'text-gray-500'
    if (numeric > 0) return 'text-green-600 dark:text-green-400'
    if (numeric < 0) return 'text-red-600 dark:text-red-400'
    return 'text-gray-500'
  }

  const syncStrategyVersion = () => {
    const versions = selectedStrategyVersions.value
    if (!versions.length) return
    if (!versions.find((item: any) => item.version === config.strategy_version)) {
      const fallback = versions.find((item: any) => item.is_default) || versions[0]
      config.strategy_version = fallback.version
    }
    const validVersions = new Set(runs.versionCompareOptions.value.map((item) => item.version))
    runs.versionCompareSelections.value = runs.versionCompareSelections.value.filter((item) => validVersions.has(item))
  }

  const fetchStrategies = async () => {
    try {
      const res = await backtestApi.listStrategies()
      strategies.value = res.data
      if (strategies.value.length && !strategies.value.find((item) => item.key === config.strategy_key)) {
        config.strategy_key = strategies.value[0].key
      }
      syncStrategyVersion()
    } catch (error) {
      console.error(error)
    }
  }

  const fetchTemplates = async () => {
    try {
      const res = await backtestApi.listTemplates()
      templates.value = res.data
      if (!templates.value.length) return
      const matchedTemplate = templates.value.find((item) => item.template === editor.versionDraft.template) || templates.value[0]
      if (!editor.versionDraft.template) return
      if (!Object.keys(editor.versionDraft.config?.indicators || {}).length) {
        editor.applyDraftFromTemplate(matchedTemplate.template)
      } else {
        editor.newIndicatorType.value = matchedTemplate.indicator_registry?.[0]?.key || indicators.value[0]?.key || 'ema'
      }
    } catch (error) {
      console.error(error)
    }
  }

  const fetchIndicators = async () => {
    try {
      const [indicatorRes, engineRes] = await Promise.all([backtestApi.listIndicators(), backtestApi.listIndicatorEngines()])
      indicators.value = indicatorRes.data
      indicatorEngines.value = engineRes.data
      if (!editor.newIndicatorType.value) editor.newIndicatorType.value = indicators.value[0]?.key || 'ema'
      editor.resetIndicatorDraft()
    } catch (error) {
      console.error(error)
    }
  }

  const fetchEditorContract = async () => {
    try {
      const res = await backtestApi.getEditorContract()
      editorContract.value = res.data
      editor.initializeDraftFromContract()
    } catch (error) {
      console.error(error)
    }
  }

  const createIndicator = async () => {
    try {
      await backtestApi.createIndicator({
        key: editor.indicatorDraft.key.trim(),
        name: editor.indicatorDraft.name.trim(),
        engine_key: editor.indicatorDraft.engine_key,
        description: editor.indicatorDraft.description.trim() || null,
        params: clone(editor.indicatorDraft.params),
      })
      await fetchIndicators()
      editor.resetIndicatorDraft()
      alert(t('backtest.indicatorSaved'))
    } catch (error: any) {
      alert(`${t('backtest.versionSaveFailed')}: ${error.message}`)
    }
  }

  const createTemplate = async () => {
    try {
      if (!editor.versionDraft.config) throw new Error(t('backtest.templateMissing'))
      if (!editor.templateDraft.key.trim() || !editor.templateDraft.name.trim()) throw new Error(t('backtest.templateDraftRequired'))
      const indicatorKeys = Array.from(new Set([
        ...editor.templateDraft.indicator_keys,
        ...Object.values(editor.versionDraft.config.indicators).map((item: any) => item.type),
      ]))
      const res = await backtestApi.createTemplate({
        key: editor.templateDraft.key.trim(),
        name: editor.templateDraft.name.trim(),
        category: editor.templateDraft.category.trim() || 'custom',
        description: editor.templateDraft.description.trim() || null,
        indicator_keys: indicatorKeys,
        default_config: clone(editor.versionDraft.config),
        default_parameter_space: buildParameterSpaceJson(editor.optimizableTargets.value, editor.versionDraft.parameterSpaceValues),
      })
      await fetchTemplates()
      editor.applyDraftFromTemplate(res.data.template, res.data.default_config, res.data.default_parameter_space, { description: res.data.description || '' })
      editor.resetTemplateDraft()
      alert(t('backtest.templateSaved'))
    } catch (error: any) {
      alert(`${t('backtest.versionSaveFailed')}: ${error.message}`)
    }
  }

  const createStrategyVersion = async () => {
    try {
      if (!editor.versionDraft.key.trim() || !editor.versionDraft.name.trim()) throw new Error(t('backtest.versionDraftRequired'))
      if (!editor.versionDraft.config) throw new Error(t('backtest.templateMissing'))
      if (!editor.versionDraft.template || !editor.editorTemplate.value) throw new Error(t('backtest.templateMissing'))
      await backtestApi.createStrategyVersion({
        key: editor.versionDraft.key.trim(),
        name: editor.versionDraft.name.trim(),
        template: editor.versionDraft.template,
        category: editor.editorTemplate.value.category || editor.versionDraft.category,
        description: editor.versionDraft.description.trim() || null,
        notes: editor.versionDraft.notes.trim() || null,
        config: clone(editor.versionDraft.config),
        parameter_space: buildParameterSpaceJson(editor.optimizableTargets.value, editor.versionDraft.parameterSpaceValues),
        make_default: editor.versionDraft.make_default,
      })
      await fetchStrategies()
      config.strategy_key = editor.versionDraft.key.trim()
      syncStrategyVersion()
      alert(t('backtest.versionSaved'))
    } catch (error: any) {
      alert(`${t('backtest.versionSaveFailed')}: ${error.message}`)
    }
  }

  onMounted(async () => {
    await fetchEditorContract()
    await Promise.all([runs.fetchHistory(), fetchStrategies(), fetchTemplates(), fetchIndicators()])
  })

  return {
    t,
    theme,
    timeframes,
    optimizeMetrics,
    editorContract,
    strategies,
    templates,
    indicators,
    indicatorEngines,
    config,
    isDark,
    chartColors,
    selectedStrategy,
    selectedStrategyVersions,
    selectedVersion,
    categoryLabel,
    profitColorClass,
    syncStrategyVersion,
    fetchStrategies,
    fetchTemplates,
    fetchIndicators,
    fetchEditorContract,
    createIndicator,
    createTemplate,
    createStrategyVersion,
    ...editor,
    ...runs,
  }
}


export type BacktestPageState = ReturnType<typeof useBacktestPage>
