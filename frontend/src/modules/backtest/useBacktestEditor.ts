import { computed, reactive, ref, type ComputedRef, type Ref } from 'vue'

import { isRecord, readBoolean, readString } from '@/composables/pageSnapshot'
import type { StrategyEditorContract, StrategyTemplateConfig } from '@/types'

import {
  buildId,
  clone,
  collectRuleTargets,
  createBlankConfig,
  createBlankIndicatorDraft,
  createBlankTemplateDraft,
  createBlankVersionDraft,
  pruneTreeByIndicator,
} from './editorContract'


interface UseBacktestEditorOptions {
  t: (key: string) => string
  editorContract: Ref<StrategyEditorContract | null>
  templates: Ref<any[]>
  indicators: Ref<any[]>
  indicatorEngines: Ref<any[]>
  selectedStrategy: ComputedRef<any | null>
  selectedVersion: ComputedRef<any | null>
}


export const useBacktestEditor = ({
  t,
  editorContract,
  templates,
  indicators,
  indicatorEngines,
  selectedStrategy,
  selectedVersion,
}: UseBacktestEditorOptions) => {
  const normalizedTemplates = computed(() => (Array.isArray(templates.value) ? templates.value.filter((item) => item?.template) : []))
  const normalizedIndicators = computed(() => (Array.isArray(indicators.value) ? indicators.value.filter((item) => item?.key) : []))
  const normalizedIndicatorEngines = computed(() => (Array.isArray(indicatorEngines.value) ? indicatorEngines.value.filter((item) => item?.key) : []))
  const showVersionEditor = ref(false)
  const showIndicatorCreator = ref(false)
  const showTemplateCreator = ref(false)
  const useGlobalIndicatorCatalog = ref(false)
  const newIndicatorType = ref('ema')
  const editorReady = computed(() => Boolean(editorContract.value))

  const versionDraft = reactive({
    key: 'ema_rsi_macd',
    name: 'Variant',
    template: 'ema_rsi_macd',
    category: 'trend',
    description: '',
    notes: '',
    config: null as StrategyTemplateConfig | null,
    parameterSpaceValues: {} as Record<string, string>,
    make_default: true,
  })
  const indicatorDraft = reactive(createBlankIndicatorDraft())
  const templateDraft = reactive(createBlankTemplateDraft())

  const editorTemplate = computed(() => normalizedTemplates.value.find((item) => item.template === versionDraft.template) || null)
  const availableIndicators = computed(() => (
    useGlobalIndicatorCatalog.value
      ? normalizedIndicators.value
      : ((Array.isArray(editorTemplate.value?.indicator_registry) ? editorTemplate.value?.indicator_registry.filter((item: any) => item?.key) : normalizedIndicators.value))
  ).filter((item: any) => item?.key))
  const operatorOptions = computed(() => editorTemplate.value?.operators || editorContract.value?.operators || [])
  const groupLogicOptions = computed(() => editorTemplate.value?.group_logics || editorContract.value?.group_logics || [])
  const indicatorCards = computed(() => Object.entries(versionDraft.config?.indicators || {}).map(([id, indicator]: any) => {
    const spec = availableIndicators.value.find((item: any) => item?.key === indicator.type) || normalizedIndicators.value.find((item: any) => item?.key === indicator.type)
    const timeframeLabel = editorContract.value?.timeframe_options?.find((item: any) => item?.key === (indicator.timeframe || 'base'))?.label || indicator.timeframe || 'base'
    return {
      id,
      label: indicator.label || spec?.name || id,
      typeLabel: spec?.name || indicator.type,
      timeframeLabel,
      params: Array.isArray(spec?.params) ? spec.params.filter((item: any) => item?.key) : [],
    }
  }))

  const sourceOptions = computed(() => {
    const base = [
      { value: 'price:open:0', label: `Price · Open · ${t('backtest.currentBar')}` },
      { value: 'price:high:0', label: `Price · High · ${t('backtest.currentBar')}` },
      { value: 'price:low:0', label: `Price · Low · ${t('backtest.currentBar')}` },
      { value: 'price:close:0', label: `Price · Close · ${t('backtest.currentBar')}` },
      { value: 'price:volume:0', label: `Price · Volume · ${t('backtest.currentBar')}` },
      { value: 'price:open:1', label: `Price · Open · ${t('backtest.previousBar')}` },
      { value: 'price:high:1', label: `Price · High · ${t('backtest.previousBar')}` },
      { value: 'price:low:1', label: `Price · Low · ${t('backtest.previousBar')}` },
      { value: 'price:close:1', label: `Price · Close · ${t('backtest.previousBar')}` },
      { value: 'price:volume:1', label: `Price · Volume · ${t('backtest.previousBar')}` },
    ]
    const extra = []
    for (const [indicatorId, indicator] of Object.entries(versionDraft.config?.indicators || {})) {
      const spec = availableIndicators.value.find((item: any) => item?.key === (indicator as any).type) || normalizedIndicators.value.find((item: any) => item?.key === (indicator as any).type)
      for (const output of spec?.outputs || []) {
        const timeframeLabel = editorContract.value?.timeframe_options?.find((item: any) => item?.key === ((indicator as any).timeframe || 'base'))?.label || ((indicator as any).timeframe || 'base')
        extra.push({
          value: `indicator:${indicatorId}:${output.key}:0`,
          label: `${(indicator as any).label || indicatorId} · ${output.label} · ${timeframeLabel} · ${t('backtest.currentBar')}`,
        })
        extra.push({
          value: `indicator:${indicatorId}:${output.key}:1`,
          label: `${(indicator as any).label || indicatorId} · ${output.label} · ${timeframeLabel} · ${t('backtest.previousBar')}`,
        })
      }
    }
    return [...base, ...extra]
  })
  const indicatorSourceOptions = computed(() => sourceOptions.value.filter((item) => item.value.startsWith('indicator:')))
  const branchKeys = ['trend', 'range'] as const
  const branchSignalKeys = ['long_entry', 'long_exit', 'short_entry', 'short_exit'] as const

  const optimizableTargets = computed(() => {
    const targets: Array<{ path: string; label: string; type: string; fallback: number }> = []
    for (const [indicatorId, indicator] of Object.entries(versionDraft.config?.indicators || {})) {
      const spec = availableIndicators.value.find((item: any) => item?.key === (indicator as any).type) || normalizedIndicators.value.find((item: any) => item?.key === (indicator as any).type)
      for (const param of spec?.params || []) {
        if (param.type === 'bool') continue
        targets.push({ path: `indicators.${indicatorId}.params.${param.key}`, label: `${(indicator as any).label || indicatorId} · ${param.label}`, type: param.type, fallback: param.default })
      }
    }
    for (const branchKey of branchKeys) {
      const branch = (versionDraft.config as any)?.[branchKey]
      if (!branch) continue
      collectRuleTargets(branch.regime, `${branchKey}.regime`, targets, t('backtest.constantValue'), t('backtest.multiplier'))
      for (const signalKey of branchSignalKeys) {
        collectRuleTargets(branch[signalKey], `${branchKey}.${signalKey}`, targets, t('backtest.constantValue'), t('backtest.multiplier'))
      }
    }
    for (const target of versionDraft.config?.risk?.roi_targets || []) {
      targets.push({ path: `risk.roi_targets.${target.id}.profit`, label: `ROI · ${target.minutes}m`, type: 'float', fallback: target.profit || 0 })
    }
    for (const item of versionDraft.config?.risk?.partial_exits || []) {
      targets.push({ path: `risk.partial_exits.${item.id}.profit`, label: `Partial Exit · ${item.id}`, type: 'float', fallback: item.profit || 0 })
    }
    targets.push({ path: 'risk.stoploss', label: t('backtest.stoplossLabel'), type: 'float', fallback: versionDraft.config?.risk?.stoploss || -0.1 })
    targets.push({ path: 'risk.trailing.positive', label: t('backtest.trailingPositive'), type: 'float', fallback: versionDraft.config?.risk?.trailing?.positive || 0.02 })
    targets.push({ path: 'risk.trailing.offset', label: t('backtest.trailingOffset'), type: 'float', fallback: versionDraft.config?.risk?.trailing?.offset || 0.03 })
    return targets
  })

  const resetIndicatorDraft = () => {
    Object.assign(indicatorDraft, createBlankIndicatorDraft(normalizedIndicatorEngines.value))
  }

  const resetTemplateDraft = () => {
    Object.assign(templateDraft, createBlankTemplateDraft())
  }

  const syncIndicatorDraftEngine = () => {
    const engine = normalizedIndicatorEngines.value.find((item) => item.key === indicatorDraft.engine_key)
    indicatorDraft.params = clone(engine?.params || [])
  }

  const applyDraftFromTemplate = (templateKey: string, configValues = {}, parameterSpaceValues = {}, overrides = {}) => {
    const templateSpec = normalizedTemplates.value.find((item) => item.template === templateKey)
    if (!templateSpec) return
    useGlobalIndicatorCatalog.value = false
    versionDraft.template = templateSpec.template
    versionDraft.category = templateSpec.category
    versionDraft.description = (overrides as any).description ?? templateSpec.description ?? ''
    versionDraft.config = clone(Object.keys(configValues).length ? configValues : templateSpec.default_config)

    const nextParameterSpaceValues: Record<string, string> = {}
    const source = Object.keys(parameterSpaceValues).length ? parameterSpaceValues : templateSpec.default_parameter_space
    for (const [key, values] of Object.entries(source || {})) {
      nextParameterSpaceValues[key] = Array.isArray(values) ? values.join(', ') : ''
    }
    versionDraft.parameterSpaceValues = nextParameterSpaceValues
    newIndicatorType.value = templateSpec.indicator_registry?.find((item: any) => item?.key)?.key || normalizedIndicators.value[0]?.key || 'ema'
  }

  const syncVersionDraftTemplate = () => {
    if (!versionDraft.template) return
    applyDraftFromTemplate(versionDraft.template)
  }

  const addIndicator = () => {
    if (!versionDraft.config) return
    const spec = availableIndicators.value.find((item) => item.key === newIndicatorType.value)
    if (!spec) return
    let candidateId = spec.key
    let suffix = 2
    while (versionDraft.config.indicators[candidateId]) {
      candidateId = `${spec.key}_${suffix}`
      suffix += 1
    }
    const params: Record<string, number | boolean> = {}
    for (const param of spec.params || []) params[param.key] = param.default
    versionDraft.config.indicators[candidateId] = { label: spec.name, type: spec.key, timeframe: 'base', params }
  }

  const removeIndicator = (indicatorId: string) => {
    if (!versionDraft.config) return
    delete versionDraft.config.indicators[indicatorId]
    for (const branchKey of branchKeys) {
      const branch = (versionDraft.config as any)?.[branchKey]
      if (!branch) continue
      pruneTreeByIndicator(branch.regime, indicatorId)
      for (const signalKey of branchSignalKeys) {
        pruneTreeByIndicator(branch[signalKey], indicatorId)
      }
    }
    Object.keys(versionDraft.parameterSpaceValues).forEach((key) => {
      if (key.startsWith(`indicators.${indicatorId}.`)) delete versionDraft.parameterSpaceValues[key]
    })
  }

  const syncExecutionConfig = () => {
    if (!versionDraft.config?.execution) return
    if (versionDraft.config.execution.market_type === 'spot') {
      versionDraft.config.execution.direction = 'long_only'
    }
  }

  const addRoiTarget = () => {
    if (!versionDraft.config) return
    versionDraft.config.risk.roi_targets.push({ id: buildId('roi'), minutes: 0, profit: 0.03, enabled: true })
  }

  const removeRoiTarget = (targetId: string) => {
    if (!versionDraft.config) return
    const next = versionDraft.config.risk.roi_targets.filter((item) => item.id !== targetId)
    versionDraft.config.risk.roi_targets.splice(0, versionDraft.config.risk.roi_targets.length, ...next)
  }

  const addPartialExit = () => {
    if (!versionDraft.config) return
    versionDraft.config.risk.partial_exits.push({ id: buildId('partial'), profit: 0.05, size_pct: 25, enabled: true })
  }

  const removePartialExit = (itemId: string) => {
    if (!versionDraft.config) return
    const next = versionDraft.config.risk.partial_exits.filter((item) => item.id !== itemId)
    versionDraft.config.risk.partial_exits.splice(0, versionDraft.config.risk.partial_exits.length, ...next)
  }

  const fillVersionDraft = () => {
    const strategy = selectedStrategy.value
    const version = selectedVersion.value
    if (!strategy || !version) return
    versionDraft.key = strategy.key
    versionDraft.name = `${version.name} Copy`
    versionDraft.notes = version.notes || ''
    versionDraft.make_default = true
    applyDraftFromTemplate(strategy.template, version.config || {}, version.parameter_space || {}, { description: strategy.description || '' })
    showVersionEditor.value = true
  }

  const startBlankBuilder = () => {
    if (!editorContract.value) return
    useGlobalIndicatorCatalog.value = true
    versionDraft.template = ''
    versionDraft.category = 'custom'
    versionDraft.description = ''
    versionDraft.notes = ''
    versionDraft.config = createBlankConfig(editorContract.value)
    versionDraft.parameterSpaceValues = {}
    versionDraft.make_default = true
    newIndicatorType.value = normalizedIndicators.value[0]?.key || 'ema'
    resetTemplateDraft()
    showVersionEditor.value = true
  }

  const toggleTemplateIndicator = (indicatorKey: string) => {
    if (templateDraft.indicator_keys.includes(indicatorKey)) {
      templateDraft.indicator_keys = templateDraft.indicator_keys.filter((item) => item !== indicatorKey)
      return
    }
    templateDraft.indicator_keys = [...templateDraft.indicator_keys, indicatorKey]
  }

  const initializeDraftFromContract = () => {
    if (!versionDraft.config && editorContract.value) {
      Object.assign(versionDraft, createBlankVersionDraft(editorContract.value))
    }
  }

  const buildSnapshot = () => ({
    showVersionEditor: showVersionEditor.value,
    showIndicatorCreator: showIndicatorCreator.value,
    showTemplateCreator: showTemplateCreator.value,
    useGlobalIndicatorCatalog: useGlobalIndicatorCatalog.value,
    newIndicatorType: newIndicatorType.value,
    versionDraft: clone(versionDraft),
    indicatorDraft: clone(indicatorDraft),
    templateDraft: clone(templateDraft),
  })

  const restoreSnapshot = (snapshot: unknown) => {
    if (!isRecord(snapshot)) return

    showVersionEditor.value = readBoolean(snapshot.showVersionEditor, showVersionEditor.value)
    showIndicatorCreator.value = readBoolean(snapshot.showIndicatorCreator, showIndicatorCreator.value)
    showTemplateCreator.value = readBoolean(snapshot.showTemplateCreator, showTemplateCreator.value)
    useGlobalIndicatorCatalog.value = readBoolean(snapshot.useGlobalIndicatorCatalog, useGlobalIndicatorCatalog.value)
    newIndicatorType.value = readString(snapshot.newIndicatorType, newIndicatorType.value)

    if (isRecord(snapshot.versionDraft)) {
      Object.assign(versionDraft, clone(snapshot.versionDraft))
      versionDraft.key = readString(versionDraft.key, 'ema_rsi_macd')
      versionDraft.name = readString(versionDraft.name, 'Variant')
      versionDraft.template = typeof versionDraft.template === 'string' ? versionDraft.template : ''
      versionDraft.category = readString(versionDraft.category, 'custom')
      versionDraft.description = typeof versionDraft.description === 'string' ? versionDraft.description : ''
      versionDraft.notes = typeof versionDraft.notes === 'string' ? versionDraft.notes : ''
      versionDraft.make_default = typeof versionDraft.make_default === 'boolean' ? versionDraft.make_default : true
      versionDraft.parameterSpaceValues = isRecord(versionDraft.parameterSpaceValues)
        ? Object.fromEntries(Object.entries(versionDraft.parameterSpaceValues).filter((entry): entry is [string, string] => typeof entry[0] === 'string' && typeof entry[1] === 'string'))
        : {}
    }

    if (isRecord(snapshot.indicatorDraft)) {
      Object.assign(indicatorDraft, clone(snapshot.indicatorDraft))
      indicatorDraft.key = typeof indicatorDraft.key === 'string' ? indicatorDraft.key : ''
      indicatorDraft.name = typeof indicatorDraft.name === 'string' ? indicatorDraft.name : ''
      indicatorDraft.engine_key = readString(indicatorDraft.engine_key, normalizedIndicatorEngines.value[0]?.key || 'ema')
      indicatorDraft.description = typeof indicatorDraft.description === 'string' ? indicatorDraft.description : ''
      indicatorDraft.params = Array.isArray(indicatorDraft.params) ? clone(indicatorDraft.params) : clone(normalizedIndicatorEngines.value[0]?.params || [])
    }

    if (isRecord(snapshot.templateDraft)) {
      Object.assign(templateDraft, clone(snapshot.templateDraft))
      templateDraft.key = typeof templateDraft.key === 'string' ? templateDraft.key : ''
      templateDraft.name = typeof templateDraft.name === 'string' ? templateDraft.name : ''
      templateDraft.category = readString(templateDraft.category, 'custom')
      templateDraft.description = typeof templateDraft.description === 'string' ? templateDraft.description : ''
      templateDraft.indicator_keys = Array.isArray(templateDraft.indicator_keys)
        ? templateDraft.indicator_keys.filter((item): item is string => typeof item === 'string' && item.length > 0)
        : []
    }
  }

  return {
    showVersionEditor,
    showIndicatorCreator,
    showTemplateCreator,
    useGlobalIndicatorCatalog,
    newIndicatorType,
    editorReady,
    versionDraft,
    indicatorDraft,
    templateDraft,
    editorTemplate,
    availableIndicators,
    operatorOptions,
    groupLogicOptions,
    indicatorCards,
    sourceOptions,
    indicatorSourceOptions,
    optimizableTargets,
    resetIndicatorDraft,
    resetTemplateDraft,
    syncIndicatorDraftEngine,
    applyDraftFromTemplate,
    syncVersionDraftTemplate,
    addIndicator,
    removeIndicator,
    syncExecutionConfig,
    addRoiTarget,
    removeRoiTarget,
    addPartialExit,
    removePartialExit,
    fillVersionDraft,
    startBlankBuilder,
    toggleTemplateIndicator,
    initializeDraftFromContract,
    buildSnapshot,
    restoreSnapshot,
  }
}
