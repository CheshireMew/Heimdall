export interface BacktestControlPanelView {
  config: any
  today: string
  strategies: any[]
  selectedStrategy: any | null
  selectedStrategyVersions: any[]
  selectedVersion: any | null
  timeframes: string[]
  optimizeMetrics: string[]
  symbolsText: string
  backtestLoading: boolean
  paperLoading: boolean
  isBusy: boolean
  syncStrategyVersion: () => void
  openCopyEditor: () => void
  openBlankEditor: () => void
  startBacktest: () => Promise<void>
  startPaperRun: () => Promise<void>
}

export interface BacktestHistoryPanelView {
  historyMode: 'backtest' | 'paper'
  enableHistoryCompare: boolean
  visibleHistory: any[]
  compareRunIds: number[]
  openRunDetail: (run: any, mode?: 'backtest' | 'paper') => void
  toggleCompareRun: (runId: number) => void
  portfolioLabel: (run: any) => string
  runStatusLabel: (run: any) => string
  profitColorClass: (value: unknown) => string
  stopPaperRun: (runId: number) => Promise<void>
  deleteRun: (runId: number, mode: 'backtest' | 'paper') => Promise<void>
}

export interface BacktestResultPanelView {
  selectedRun: any | null
  isPaperRun: boolean
  isDark: boolean
  chartColors: any
  chartData: { candles: any[]; volume: any[] }
  pairBreakdown: any[]
  optimizationTrials: any[]
  rollingWindows: any[]
  selectedCompareRuns: any[]
  recentRunCompare: any
  versionCompareOptions: any[]
  versionCompareSelections: number[]
  selectedVersionCompareRuns: any[]
  versionRunCompare: any
  profitColorClass: (value: unknown) => string
  runStatusLabel: (run: any) => string
  portfolioLabel: (run: any) => string
  joinSymbols: (symbols: string[] | undefined) => string
  configLabel: (value: Record<string, unknown> | null | undefined) => string
  compareRunLabel: (run: any) => string
  toggleVersionCompare: (version: number) => void
}

export interface BacktestDetailHeroView {
  selectedRun: any | null
  isPaperRun: boolean
  goBackToCenter: () => void
  portfolioLabel: (run: any) => string
  runStatusLabel: (run: any) => string
}
