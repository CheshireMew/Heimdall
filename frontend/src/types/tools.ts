import type { CandlestickData } from './market'

export interface DCASimulationConfig {
  symbol?: string
  amount?: number
  start_date?: string | null
  investment_time?: string
  timezone?: string
  days?: number | null
  strategy?: string
  strategy_params?: Record<string, unknown>
}

export interface DCAHistoryPoint {
  date: string
  price: number
  invested: number
  value: number
  coins: number
  roi: number
  avg_cost: number
}

export interface DCASimulationResponse {
  symbol: string
  start_date: string
  end_date: string
  target_time: string
  total_days: number
  total_invested: number
  final_value: number
  total_coins: number
  roi: number
  average_cost: number
  profit_loss: number
  current_price: number
  history: DCAHistoryPoint[]
}

export interface PairCompareParams {
  symbol_a: string
  symbol_b: string
  days?: number
  timeframe?: string
}

export interface PairCompareResponse {
  symbol_a: string
  symbol_b: string
  data_a: CandlestickData[]
  data_b: CandlestickData[]
  ratio_ohlc: CandlestickData[]
  ratio_symbol: string
}

export type PortfolioReviewFrequency = 'daily' | 'weekly' | 'monthly' | 'quarterly'
export type PortfolioSuggestedAction = 'wait' | 'cashflow' | 'full'
export type PortfolioSuggestedReason = 'on_track' | 'scheduled_review' | 'band_breach' | 'cashflow_first' | 'full_rebalance' | 'below_threshold'
export type PortfolioHoldingsSource = 'virtual' | 'paper'

export interface PortfolioBalanceAssetInput {
  id: string
  symbol: string
  targetWeight: number
  units: number
  currentPrice: number
  seedValue: number
}

export interface PortfolioBalanceStrategyConfig {
  rebalanceBand: number
  minTradeAmount: number
  reviewFrequency: PortfolioReviewFrequency
}

export interface PortfolioBalanceTrackingConfig {
  virtualCapital: number
  inceptionDate: string
}

export interface PortfolioBalanceBacktestConfig {
  initialCapital: number
  backtestStartDate: string
}

export interface PortfolioBalancePortfolio {
  id: string
  name: string
  assets: PortfolioBalanceAssetInput[]
  strategy: PortfolioBalanceStrategyConfig
  tracking: PortfolioBalanceTrackingConfig
  backtest: PortfolioBalanceBacktestConfig
  lastBacktestResult?: PortfolioBacktestSummary | null
  holdingsInitializedAt?: string | null
  lastPriceUpdatedAt?: string | null
  seedCapital?: number | null
  holdingsSource?: PortfolioHoldingsSource | null
  createdAt: string
  updatedAt: string
}

export interface PortfolioBalanceAssetPlan {
  id: string
  symbol: string
  units: number
  seedValue: number
  currentValue: number
  trackingDiffValue: number
  price: number
  currentWeight: number
  normalizedTargetWeight: number
  targetValue: number
  driftValue: number
  driftWeight: number
  rebalanceAmount: number
  rebalanceUnits: number
  primaryAction: 'buy' | 'sell' | 'hold'
  bandLowerWeight: number
  bandUpperWeight: number
  bandLowerValue: number
  bandUpperValue: number
  isOutOfBand: boolean
  cashflowAmount: number
  projectedValue: number
  projectedWeight: number
  projectedIsOutOfBand: boolean
}

export interface PortfolioBalancePlan {
  totalValue: number
  trackingCapital: number
  targetWeightInputSum: number
  usesEqualWeightFallback: boolean
  totalBuyAmount: number
  totalSellAmount: number
  turnoverAmount: number
  maxDriftWeight: number
  outOfBandCount: number
  projectedOutOfBandCount: number
  reviewDue: boolean
  shouldReviewNow: boolean
  reviewFrequency: PortfolioReviewFrequency
  nextReviewDate: string
  daysUntilReview: number
  suggestedAction: PortfolioSuggestedAction
  suggestedReason: PortfolioSuggestedReason
  assets: PortfolioBalanceAssetPlan[]
}

export interface PortfolioBacktestSummary {
  startDate: string
  endDate: string
  initialValue: number
  finalValue: number
  totalReturnPct: number
  annualizedReturnPct: number | null
  maxDrawdownPct: number
  reviewCount: number
  outOfBandReviewCount: number
  rebalanceCount: number
  equityCurve: PortfolioBacktestEquityPoint[]
}

export interface PortfolioBacktestEquityPoint {
  id: number
  timestamp: string
  equity: number
  pnl_abs: number
  drawdown_pct: number
}
