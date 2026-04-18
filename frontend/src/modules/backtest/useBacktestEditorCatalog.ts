import type { ComputedRef, Ref } from 'vue'

import type { StrategyEditorContract } from '@/types'

import { backtestApi } from './api'


interface UseBacktestEditorCatalogOptions {
  t: (key: string) => string
  config: any
  strategies: Ref<any[]>
  templates: Ref<any[]>
  indicators: Ref<any[]>
  indicatorEngines: Ref<any[]>
  editorContract: Ref<StrategyEditorContract | null>
  selectedStrategyVersions: ComputedRef<any[]>
  editor: any
}

export const useBacktestEditorCatalog = ({
  t,
  config,
  strategies,
  templates,
  indicators,
  indicatorEngines,
  editorContract,
  selectedStrategyVersions,
  editor,
}: UseBacktestEditorCatalogOptions) => {
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
      const editableTemplates = Array.isArray(editor.editableTemplates?.value) ? editor.editableTemplates.value : templates.value
      const matchedTemplate = editableTemplates.find((item: any) => item.template === editor.versionDraft.template) || editableTemplates[0]
      if (!matchedTemplate) return
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
    } catch (error) {
      console.error(error)
    }
  }

  return {
    categoryLabel,
    syncStrategyVersion,
    fetchStrategies,
    fetchTemplates,
    fetchIndicators,
    fetchEditorContract,
  }
}
