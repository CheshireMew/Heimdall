export interface FactorResearchHeroView {
  catalog: { forward_horizons: number[] }
}

export interface FactorResearchFiltersView {
  form: any
  catalog: any
  factorPool: any[]
  loading: boolean
  catalogLoading: boolean
  runAnalysis: () => Promise<void>
  toggleCategory: (category: string) => void
  resetFactorSelection: () => void
  toggleFactor: (factorId: string) => void
  categoryChipClass: (category: string) => string
  factorChipClass: (factorId: string) => string
}

export interface FactorResearchSidebarView {
  runsLoading: boolean
  runs: any[]
  selectedRunId: number | null
  blend: any | null
  executionForm: any
  executionLoading: '' | 'backtest' | 'paper'
  loadRun: (runId: number) => Promise<void>
  startExecution: (mode: 'backtest' | 'paper') => Promise<void>
  formatDate: (value: string | null | undefined) => string
  formatNumber: (value: number | null | undefined, digits?: number) => string
  formatPct: (value: number | null | undefined, digits?: number) => string
  scoreClass: (score: number) => string
}

export interface FactorResearchDetailView {
  isDark: boolean
  ranking: any[]
  loading: boolean
  selectedFactorId: string
  selectedDetail: any | null
  blend: any | null
  selectFactor: (factorId: string) => void
  scoreClass: (score: number) => string
  correlationClass: (value: number) => string
  formatNumber: (value: number | null | undefined, digits?: number) => string
  formatPct: (value: number | null | undefined, digits?: number) => string
  formatDate: (value: string | null | undefined) => string
}

export interface FactorResearchSummaryView {
  summary: any | null
  formatDate: (value: string | null | undefined) => string
}
