export interface BacktestEditorSeedPanel {
  config: any
  strategies: any[]
  selectedStrategy: any | null
  selectedStrategyVersions: any[]
  selectedVersion: any | null
  syncStrategyVersion: () => void
  openCopySeed: () => Promise<void>
  openBlankSeed: () => Promise<void>
  goBackToCenter: () => void
}

export interface BacktestVersionMetaPanel {
  versionDraft: any
  templates: any[]
  categoryLabel: (value: string) => string
  syncVersionDraftTemplate: () => void
  startBlankBuilder: () => void
  showIndicatorCreator: boolean
  showTemplateCreator: boolean
  toggleIndicatorCreator: () => void
  toggleTemplateCreator: () => void
}

export interface BacktestIndicatorCreatorPanel {
  show: boolean
  indicatorDraft: any
  indicatorEngines: any[]
  createIndicator: () => Promise<void>
  syncIndicatorDraftEngine: () => void
}

export interface BacktestTemplateCreatorPanel {
  show: boolean
  templateDraft: any
  indicators: any[]
  toggleTemplateIndicator: (indicatorKey: string) => void
  createTemplate: () => Promise<void>
}

export interface BacktestStrategyBuilderPanel {
  editorContract: any
  versionDraft: any
  editorTemplate: any
  useGlobalIndicatorCatalog: boolean
  availableIndicators: any[]
  newIndicatorType: string
  indicatorCards: any[]
  sourceOptions: any[]
  indicatorSourceOptions: any[]
  operatorOptions: any[]
  groupLogicOptions: any[]
  optimizableTargets: Array<{ path: string; label: string }>
  addIndicator: () => void
  removeIndicator: (indicatorId: string) => void
  addRoiTarget: () => void
  removeRoiTarget: (targetId: string) => void
  addPartialExit: () => void
  removePartialExit: (itemId: string) => void
}

export interface BacktestVersionEditorPanel {
  showVersionEditor: boolean
  versionDraft: any
  metaPanel: BacktestVersionMetaPanel
  indicatorCreatorPanel: BacktestIndicatorCreatorPanel
  templateCreatorPanel: BacktestTemplateCreatorPanel
  strategyBuilderPanel: BacktestStrategyBuilderPanel
  createStrategyVersion: () => Promise<void>
}
