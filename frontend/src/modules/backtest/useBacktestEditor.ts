import { computed, reactive, ref, type ComputedRef, type Ref } from 'vue'

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

  const editorTemplate = computed(() => templates.value.find((item) => item.template === versionDraft.template) || null)
  const availableIndicators = computed(() => (
    useGlobalIndicatorCatalog.value
      ? indicators.value
      : (editorTemplate.value?.indicator_registry || indicators.value)
  ))
  const operatorOptions = computed(() => editorTemplate.value?.operators || editorContract.value?.operators || [])
  const groupLogicOptions = computed(() => editorTemplate.value?.group_logics || editorContract.value?.group_logics || [])
  const indicatorCards = computed(() => Object.entries(versionDraft.config?.indicators || {}).map(([id, indicator]: any) => {
    const spec = availableIndicators.value.find((item) => item.key === indicator.type) || indicators.value.find((item) => item.key === indicator.type)
    return {
      id,
      label: indicator.label || spec?.name || id,
      typeLabel: spec?.name || indicator.type,
      params: spec?.params || [],
    }
  }))

  const sourceOptions = computed(() => {
    const base = [
      { value: 'price:open', label: 'Price · Open' },
      { value: 'price:high', label: 'Price · High' },
      { value: 'price:low', label: 'Price · Low' },
      { value: 'price:close', label: 'Price · Close' },
      { value: 'price:volume', label: 'Price · Volume' },
    ]
    const extra = []
    for (const [indicatorId, indicator] of Object.entries(versionDraft.config?.indicators || {})) {
      const spec = availableIndicators.value.find((item) => item.key === (indicator as any).type) || indicators.value.find((item) => item.key === (indicator as any).type)
      for (const output of spec?.outputs || []) {
        extra.push({
          value: `indicator:${indicatorId}:${output.key}`,
          label: `${(indicator as any).label || indicatorId} · ${output.label}`,
        })
      }
    }
    return [...base, ...extra]
  })
  const indicatorSourceOptions = computed(() => sourceOptions.value.filter((item) => item.value.startsWith('indicator:')))

  const optimizableTargets = computed(() => {
    const targets: Array<{ path: string; label: string; type: string; fallback: number }> = []
    for (const [indicatorId, indicator] of Object.entries(versionDraft.config?.indicators || {})) {
      const spec = availableIndicators.value.find((item) => item.key === (indicator as any).type) || indicators.value.find((item) => item.key === (indicator as any).type)
      for (const param of spec?.params || []) {
        if (param.type === 'bool') continue
        targets.push({ path: `indicators.${indicatorId}.params.${param.key}`, label: `${(indicator as any).label || indicatorId} · ${param.label}`, type: param.type, fallback: param.default })
      }
    }
    collectRuleTargets(versionDraft.config?.entry, 'entry', targets, t('backtest.constantValue'), t('backtest.multiplier'))
    collectRuleTargets(versionDraft.config?.exit, 'exit', targets, t('backtest.constantValue'), t('backtest.multiplier'))
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
    Object.assign(indicatorDraft, createBlankIndicatorDraft(indicatorEngines.value))
  }

  const resetTemplateDraft = () => {
    Object.assign(templateDraft, createBlankTemplateDraft())
  }

  const syncIndicatorDraftEngine = () => {
    const engine = indicatorEngines.value.find((item) => item.key === indicatorDraft.engine_key)
    indicatorDraft.params = clone(engine?.params || [])
  }

  const applyDraftFromTemplate = (templateKey: string, configValues = {}, parameterSpaceValues = {}, overrides = {}) => {
    const templateSpec = templates.value.find((item) => item.template === templateKey)
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
    newIndicatorType.value = templateSpec.indicator_registry?.[0]?.key || indicators.value[0]?.key || 'ema'
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
    versionDraft.config.indicators[candidateId] = { label: spec.name, type: spec.key, params }
  }

  const removeIndicator = (indicatorId: string) => {
    if (!versionDraft.config) return
    delete versionDraft.config.indicators[indicatorId]
    pruneTreeByIndicator(versionDraft.config.entry, indicatorId)
    pruneTreeByIndicator(versionDraft.config.exit, indicatorId)
    Object.keys(versionDraft.parameterSpaceValues).forEach((key) => {
      if (key.startsWith(`indicators.${indicatorId}.`)) delete versionDraft.parameterSpaceValues[key]
    })
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
    newIndicatorType.value = indicators.value[0]?.key || 'ema'
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
    addRoiTarget,
    removeRoiTarget,
    addPartialExit,
    removePartialExit,
    fillVersionDraft,
    startBlankBuilder,
    toggleTemplateIndicator,
    initializeDraftFromContract,
  }
}
