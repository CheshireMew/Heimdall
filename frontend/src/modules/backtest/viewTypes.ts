import { reactive } from 'vue'
import type {
  BacktestDetailResponse,
  BacktestOptimizationTrial,
  BacktestPairBreakdown,
  BacktestRollingWindow,
  BacktestRun,
  CandlestickData,
  StrategyDefinition,
  StrategyVersion,
  VolumeData,
} from '@/types'

export const defineReactiveView = <T extends object>(value: object): T => {
  // Vue templates receive unwrapped refs, while TypeScript checks this boundary
  // before Vue unwraps it. Keep that mismatch handled in one place.
  return reactive(value) as T
}

export interface BacktestRunSelectionConfig {
  strategy_key: string
  strategy_version: number
}

export interface BacktestPageConfig extends BacktestRunSelectionConfig {
  strategy_key: string
  strategy_version: number
  timeframe: string
  start_date: string
  end_date: string
  initial_cash: number
  fee_rate: number
  portfolio: {
    max_open_trades: number
    position_size_pct: number
    stake_mode: 'fixed' | 'unlimited'
  }
  research: {
    slippage_bps: number
    funding_rate_daily: number
    in_sample_ratio: number
    optimize_metric: 'sharpe' | 'profit_pct' | 'calmar' | 'profit_factor'
    optimize_trials: number
    rolling_windows: number
  }
}

export type BacktestDisplayRun = BacktestRun | BacktestDetailResponse

export interface BacktestChartData {
  candles: CandlestickData[]
  volume: VolumeData[]
}

export interface BacktestComparisonSeries {
  name: string
  color: string
  data: number[]
}

export interface BacktestComparisonChart {
  performance: {
    categories: string[]
    series: BacktestComparisonSeries[]
  }
  quality: {
    categories: string[]
    series: BacktestComparisonSeries[]
  }
}

export interface BacktestVersionCompareOption {
  version: number
  name: string
  run: BacktestRun
}

export interface BacktestControlPanelView {
  config: BacktestPageConfig
  today: string
  ready: boolean
  strategies: StrategyDefinition[]
  selectedStrategy: StrategyDefinition | null
  selectedStrategyVersions: StrategyVersion[]
  selectedVersion: StrategyVersion | null
  canCopyCurrentStrategy: boolean
  canStartPaperRun: boolean
  strategyCapabilityHint: string
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
  visibleHistory: BacktestRun[]
  compareRunIds: number[]
  openRunDetail: (run: BacktestRun, mode?: 'backtest' | 'paper') => void
  toggleCompareRun: (runId: number) => void
  portfolioLabel: (run: BacktestDisplayRun) => string
  runStatusLabel: (run: BacktestDisplayRun) => string
  profitColorClass: (value: unknown) => string
  stopPaperRun: (runId: number) => Promise<void>
  deleteRun: (runId: number, mode: 'backtest' | 'paper') => Promise<void>
}

export interface BacktestResultPanelView {
  selectedRun: BacktestDetailResponse | null
  isPaperRun: boolean
  isDark: boolean
  chartColors: {
    bg: string
    grid: string
    text: string
    upColor: string
    downColor: string
  }
  chartData: BacktestChartData
  pairBreakdown: BacktestPairBreakdown[]
  optimizationTrials: BacktestOptimizationTrial[]
  rollingWindows: BacktestRollingWindow[]
  selectedCompareRuns: BacktestRun[]
  recentRunCompare: BacktestComparisonChart
  versionCompareOptions: BacktestVersionCompareOption[]
  versionCompareSelections: number[]
  selectedVersionCompareRuns: BacktestRun[]
  versionRunCompare: BacktestComparisonChart
  profitColorClass: (value: unknown) => string
  runStatusLabel: (run: BacktestDisplayRun) => string
  portfolioLabel: (run: BacktestDisplayRun) => string
  joinSymbols: (symbols: string[] | undefined) => string
  configLabel: (value: Record<string, unknown> | null | undefined) => string
  compareRunLabel: (run: BacktestDisplayRun) => string
  toggleVersionCompare: (version: number) => void
}

export interface BacktestDetailHeroView {
  selectedRun: BacktestDetailResponse | null
  isPaperRun: boolean
  goBackToCenter: () => void
  portfolioLabel: (run: BacktestDisplayRun) => string
  runStatusLabel: (run: BacktestDisplayRun) => string
}
