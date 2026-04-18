import { computed, onBeforeUnmount, onMounted, reactive, ref, watch, type WatchStopHandle } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import { bindPageSnapshot, createPageSnapshot, isRecord, PAGE_SNAPSHOT_KEYS, readNumber, readString } from '@/composables/pageSnapshot'
import type { StrategyEditorContract } from '@/types'

import { useBacktestEditor } from './useBacktestEditor'
import { useBacktestEditorActions } from './useBacktestEditorActions'
import { useBacktestEditorCatalog } from './useBacktestEditorCatalog'
import { useBacktestEditorSeeds } from './useBacktestEditorSeeds'
import { supportsPaperTrading, supportsVersionEditing } from './templateRuntime'

interface BacktestEditorPageSnapshot {
  config: {
    strategy_key: string
    strategy_version: number
  }
  editor: unknown
}

const createDefaultSnapshot = (): BacktestEditorPageSnapshot => ({
  config: {
    strategy_key: '',
    strategy_version: 0,
  },
  editor: null,
})

const normalizeSnapshot = (value: unknown): BacktestEditorPageSnapshot => {
  const defaults = createDefaultSnapshot()
  if (!isRecord(value) || !isRecord(value.config)) return defaults
  return {
    config: {
      strategy_key: readString(value.config.strategy_key, defaults.config.strategy_key),
      strategy_version: readNumber(value.config.strategy_version, defaults.config.strategy_version),
    },
    editor: value.editor ?? null,
  }
}


export const useBacktestEditorPage = () => {
  const { t } = useI18n()
  const route = useRoute()
  const router = useRouter()
  const pageSnapshot = createPageSnapshot(PAGE_SNAPSHOT_KEYS.backtestEditor, normalizeSnapshot, createDefaultSnapshot())
  const restoredSnapshot = pageSnapshot.load()

  const editorContract = ref<StrategyEditorContract | null>(null)
  const strategies = ref<any[]>([])
  const templates = ref<any[]>([])
  const indicators = ref<any[]>([])
  const indicatorEngines = ref<any[]>([])
  const config = reactive(restoredSnapshot.config)
  let snapshotStopHandle: WatchStopHandle | null = null

  const selectedStrategy = computed(() => strategies.value.find((item) => item.key === config.strategy_key) || null)
  const selectedStrategyVersions = computed(() => {
    const versions = selectedStrategy.value?.versions
    if (!Array.isArray(versions)) return []
    return versions.filter(Boolean)
  })
  const selectedVersion = computed(() => selectedStrategyVersions.value.find((item: any) => item.version === config.strategy_version) || null)
  const canCopyCurrentStrategy = computed(() => Boolean(selectedVersion.value) && supportsVersionEditing(selectedStrategy.value))
  const strategyCapabilityHint = computed(() => {
    if (!selectedStrategy.value) return ''
    if (!supportsVersionEditing(selectedStrategy.value) && !supportsPaperTrading(selectedStrategy.value)) {
      return t('backtest.scriptedReadonlyHint')
    }
    if (!supportsVersionEditing(selectedStrategy.value)) {
      return t('backtest.readonlyStrategyHint')
    }
    return ''
  })

  const editor = useBacktestEditor({
    t,
    editorContract,
    templates,
    indicators,
    indicatorEngines,
    selectedStrategy,
    selectedVersion,
  })

  const catalog = useBacktestEditorCatalog({
    t,
    config,
    strategies,
    templates,
    indicators,
    indicatorEngines,
    editorContract,
    selectedStrategyVersions,
    editor,
  })

  const actions = useBacktestEditorActions({
    t,
    router,
    config,
    editor,
    fetchStrategies: catalog.fetchStrategies,
    fetchTemplates: catalog.fetchTemplates,
    fetchIndicators: catalog.fetchIndicators,
    syncStrategyVersion: catalog.syncStrategyVersion,
  })

  const seeds = useBacktestEditorSeeds({
    route,
    router,
    config,
    strategies,
    selectedStrategy,
    selectedVersion,
    editor,
    syncStrategyVersion: catalog.syncStrategyVersion,
  })

  const hasExplicitSeed = () => (
    typeof route.query.mode === 'string'
    || typeof route.query.strategy === 'string'
    || typeof route.query.version === 'string'
  )

  const startSnapshotSync = () => {
    snapshotStopHandle?.()
    snapshotStopHandle = bindPageSnapshot(
      [
        config,
        editor.showVersionEditor,
        editor.showIndicatorCreator,
        editor.showTemplateCreator,
        editor.useGlobalIndicatorCatalog,
        editor.newIndicatorType,
        editor.versionDraft,
        editor.indicatorDraft,
        editor.templateDraft,
      ],
      () => ({
        config: {
          strategy_key: readString(config.strategy_key, ''),
          strategy_version: readNumber(config.strategy_version, 0),
        },
        editor: editor.buildSnapshot(),
      }),
      pageSnapshot.save,
    )
  }

  onMounted(async () => {
    await catalog.fetchEditorContract()
    await Promise.all([catalog.fetchStrategies(), catalog.fetchTemplates(), catalog.fetchIndicators()])
    editor.initializeDraftFromContract()

    if (hasExplicitSeed()) {
      seeds.applyRouteSeed()
    } else if (restoredSnapshot.editor) {
      editor.restoreSnapshot(restoredSnapshot.editor)
    } else {
      seeds.applyRouteSeed()
    }

    startSnapshotSync()
  })

  watch(
    () => [route.query.mode, route.query.strategy, route.query.version],
    () => {
      if (!strategies.value.length) return
      seeds.applyRouteSeed()
    },
  )

  onBeforeUnmount(() => {
    snapshotStopHandle?.()
  })

  const toggleIndicatorCreator = () => {
    editor.showIndicatorCreator.value = !editor.showIndicatorCreator.value
  }

  const toggleTemplateCreator = () => {
    editor.showTemplateCreator.value = !editor.showTemplateCreator.value
  }

  const seedPanel = reactive({
    config,
    strategies,
    selectedStrategy,
    selectedStrategyVersions,
    selectedVersion,
    canCopyCurrentStrategy,
    strategyCapabilityHint,
    syncStrategyVersion: catalog.syncStrategyVersion,
    openCopySeed: seeds.openCopySeed,
    openBlankSeed: seeds.openBlankSeed,
    goBackToCenter: seeds.goBackToCenter,
  })

  const editorPanel = reactive({
    showVersionEditor: editor.showVersionEditor,
    versionDraft: editor.versionDraft,
    metaPanel: {
      versionDraft: editor.versionDraft,
      templates: editor.editableTemplates,
      categoryLabel: catalog.categoryLabel,
      syncVersionDraftTemplate: editor.syncVersionDraftTemplate,
      startBlankBuilder: editor.startBlankBuilder,
      showIndicatorCreator: editor.showIndicatorCreator,
      showTemplateCreator: editor.showTemplateCreator,
      toggleIndicatorCreator,
      toggleTemplateCreator,
    },
    indicatorCreatorPanel: {
      show: editor.showIndicatorCreator,
      indicatorDraft: editor.indicatorDraft,
      indicatorEngines,
      createIndicator: actions.createIndicator,
      syncIndicatorDraftEngine: editor.syncIndicatorDraftEngine,
    },
    templateCreatorPanel: {
      show: editor.showTemplateCreator,
      templateDraft: editor.templateDraft,
      indicators,
      toggleTemplateIndicator: editor.toggleTemplateIndicator,
      createTemplate: actions.createTemplate,
    },
    strategyBuilderPanel: {
      editorContract,
      versionDraft: editor.versionDraft,
      editorTemplate: editor.editorTemplate,
      useGlobalIndicatorCatalog: editor.useGlobalIndicatorCatalog,
      availableIndicators: editor.availableIndicators,
      newIndicatorType: editor.newIndicatorType,
      indicatorCards: editor.indicatorCards,
      sourceOptions: editor.sourceOptions,
      indicatorSourceOptions: editor.indicatorSourceOptions,
      operatorOptions: editor.operatorOptions,
      groupLogicOptions: editor.groupLogicOptions,
      optimizableTargets: editor.optimizableTargets,
      syncExecutionConfig: editor.syncExecutionConfig,
      addIndicator: editor.addIndicator,
      removeIndicator: editor.removeIndicator,
      addRoiTarget: editor.addRoiTarget,
      removeRoiTarget: editor.removeRoiTarget,
      addPartialExit: editor.addPartialExit,
      removePartialExit: editor.removePartialExit,
    },
    createStrategyVersion: actions.createStrategyVersion,
  })

  return {
    seedPanel,
    editorPanel,
  }
}
