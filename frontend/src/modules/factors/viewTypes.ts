import type {
  FactorBlend,
  FactorCatalogItem,
  FactorCatalogResponse,
  FactorDetail,
  FactorExecutionRequest,
  FactorResearchRequest,
  FactorResearchRun,
  FactorResearchSummary,
  FactorScorecard,
} from './contracts'

export interface FactorResearchHeroView {
  catalog: { forward_horizons: number[] }
}

export interface FactorResearchFiltersView {
  form: FactorResearchRequest
  catalog: FactorCatalogResponse
  factorPool: FactorCatalogItem[]
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
  runs: FactorResearchRun[]
  selectedRunId: number | null
  blend: FactorBlend | null
  executionForm: FactorExecutionRequest
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
  ranking: FactorScorecard[]
  loading: boolean
  selectedFactorId: string
  selectedDetail: FactorDetail | null
  blend: FactorBlend | null
  selectFactor: (factorId: string) => void
  scoreClass: (score: number) => string
  correlationClass: (value: number) => string
  formatNumber: (value: number | null | undefined, digits?: number) => string
  formatPct: (value: number | null | undefined, digits?: number) => string
  formatDate: (value: string | null | undefined) => string
}

export interface FactorResearchSummaryView {
  summary: FactorResearchSummary | null
  formatDate: (value: string | null | undefined) => string
}
