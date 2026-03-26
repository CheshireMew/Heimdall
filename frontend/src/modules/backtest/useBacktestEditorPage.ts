import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import type { StrategyEditorContract } from '@/types'

import { backtestApi } from './api'
import { buildParameterSpaceJson, clone } from './editorContract'
import { useBacktestEditor } from './useBacktestEditor'


export const useBacktestEditorPage = () => {
  const { t } = useI18n()
  const route = useRoute()
  const router = useRouter()

  const editorContract = ref<StrategyEditorContract | null>(null)
  const strategies = ref<any[]>([])
  const templates = ref<any[]>([])
  const indicators = ref<any[]>([])
  const indicatorEngines = ref<any[]>([])
  const config = reactive({
    strategy_key: 'ema_rsi_macd',
    strategy_version: 1,
  })

  const selectedStrategy = computed(() => strategies.value.find((item) => item.key === config.strategy_key) || null)
  const selectedStrategyVersions = computed(() => {
    const versions = selectedStrategy.value?.versions
    if (!Array.isArray(versions)) return []
    return versions.filter(Boolean)
  })
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

  const categoryLabel = (value: string) => {
    if (value === 'trend') return t('backtest.categoryTrend')
    if (value === 'mean_reversion') return t('backtest.categoryMeanReversion')
    if (value === 'breakout') return t('backtest.categoryBreakout')
    if (value === 'custom') return t('backtest.categoryCustom')
    return value || '-'
  }

  const syncStrategyVersion = () => {
    const versions = selectedStrategyVersions.value
    if (!versions.length) return
    if (!versions.find((item: any) => item.version === config.strategy_version)) {
      const fallback = versions.find((item: any) => item.is_default) || versions[0]
      config.strategy_version = fallback.version
    }
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
      const res = await backtestApi.createStrategyVersion({
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
      config.strategy_version = res.data.version
      syncStrategyVersion()
      await router.replace({
        path: '/backtest/editor',
        query: {
          mode: 'copy',
          strategy: config.strategy_key,
          version: String(config.strategy_version),
        },
      })
      alert(t('backtest.versionSaved'))
    } catch (error: any) {
      alert(`${t('backtest.versionSaveFailed')}: ${error.message}`)
    }
  }

  const prepareCopyDraft = () => {
    if (!selectedStrategy.value || !selectedVersion.value) return
    editor.fillVersionDraft()
    editor.showVersionEditor.value = true
  }

  const prepareBlankDraft = () => {
    editor.startBlankBuilder()
    editor.showVersionEditor.value = true
    editor.versionDraft.key = config.strategy_key || editor.versionDraft.key
  }

  const syncRouteFromSelection = async (mode: 'copy' | 'blank') => {
    await router.replace({
      path: '/backtest/editor',
      query: {
        mode,
        strategy: config.strategy_key,
        ...(mode === 'copy' ? { version: String(config.strategy_version) } : {}),
      },
    })
  }

  const applyRouteSeed = () => {
    const strategyKey = typeof route.query.strategy === 'string' ? route.query.strategy : ''
    const version = Number(route.query.version)
    const mode = route.query.mode === 'blank' ? 'blank' : 'copy'

    if (strategyKey && strategies.value.find((item) => item.key === strategyKey)) {
      config.strategy_key = strategyKey
    }
    syncStrategyVersion()

    if (Number.isFinite(version) && version > 0) {
      config.strategy_version = version
      syncStrategyVersion()
    }

    if (mode === 'blank') {
      prepareBlankDraft()
      return
    }

    prepareCopyDraft()
  }

  const openCopySeed = async () => {
    await syncRouteFromSelection('copy')
    prepareCopyDraft()
  }

  const openBlankSeed = async () => {
    await syncRouteFromSelection('blank')
    prepareBlankDraft()
  }

  const goBackToCenter = () => {
    router.push('/backtest')
  }

  onMounted(async () => {
    await fetchEditorContract()
    await Promise.all([fetchStrategies(), fetchTemplates(), fetchIndicators()])
    applyRouteSeed()
  })

  watch(
    () => [route.query.mode, route.query.strategy, route.query.version],
    () => {
      if (!strategies.value.length) return
      applyRouteSeed()
    },
  )

  const page = reactive({
    t,
    strategies,
    templates,
    indicators,
    indicatorEngines,
    editorContract,
    config,
    selectedStrategy,
    selectedStrategyVersions,
    selectedVersion,
    categoryLabel,
    syncStrategyVersion,
    fetchStrategies,
    fetchTemplates,
    fetchIndicators,
    fetchEditorContract,
    createIndicator,
    createTemplate,
    createStrategyVersion,
    openCopySeed,
    openBlankSeed,
    goBackToCenter,
    ...editor,
  })

  return page
}


export type BacktestEditorPageState = ReturnType<typeof useBacktestEditorPage>
