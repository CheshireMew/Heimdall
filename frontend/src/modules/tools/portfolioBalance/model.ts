import { isRecord, readNumber, readString } from '@/composables/pageSnapshot'
import { isIndexSymbol, toBaseSymbol } from '@/modules/market'
import { readCashSymbolPrices } from '@/modules/market'
import { addDaysToLocalIsoDate, localIsoDateDaysAgo, parseLocalIsoDate, todayLocalIsoDate, toLocalIsoDate } from '@/utils/localDate'

export type PortfolioReviewFrequency = 'daily' | 'weekly' | 'monthly' | 'quarterly'
export type PortfolioSuggestedAction = 'wait' | 'cashflow' | 'full'
export type PortfolioSuggestedReason = 'on_track' | 'scheduled_review' | 'band_breach' | 'cashflow_first' | 'full_rebalance' | 'below_threshold'
export type PortfolioHoldingsSource = 'virtual' | 'paper'

export const PERCENT_BASE = 100
export const DEFAULT_REVIEW_FREQUENCY: PortfolioReviewFrequency = 'weekly'
export const readPortfolioSyntheticPriceMap = () => readCashSymbolPrices()

export const round = (value: number, digits = 2) => {
  const base = 10 ** digits
  return Math.round((value + Number.EPSILON) * base) / base
}

export const clamp = (value: number, min: number, max: number) => Math.min(max, Math.max(min, value))

export const sanitizeNumber = (value: unknown, fallback = 0) => {
  const candidate = typeof value === 'number' && Number.isFinite(value) ? value : fallback
  return candidate >= 0 ? candidate : fallback
}

export const daysAgoIso = localIsoDateDaysAgo
export const todayIso = todayLocalIsoDate
export const parseIsoDate = (value: string) => parseLocalIsoDate(value)

export const shiftReviewDate = (dateText: string, frequency: PortfolioReviewFrequency) => {
  const source = parseIsoDate(dateText)
  if (!source) return todayIso()

  if (frequency === 'daily') return addDaysToLocalIsoDate(dateText, 1)
  if (frequency === 'weekly') return addDaysToLocalIsoDate(dateText, 7)
  const next = new Date(source)
  next.setMonth(next.getMonth() + (frequency === 'monthly' ? 1 : 3))
  return toLocalIsoDate(next)
}

export const diffDaysFromToday = (dateText: string) => {
  const target = parseIsoDate(dateText)
  if (!target) return 0
  const today = new Date()
  const current = new Date(today.getFullYear(), today.getMonth(), today.getDate())
  return Math.ceil((target.getTime() - current.getTime()) / 86400000)
}

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

export interface PortfolioBalanceSnapshot {
  activePortfolioId: string
  portfolios: PortfolioBalancePortfolio[]
}

let assetSequence = 0
let portfolioSequence = 0

const createAssetId = () => `portfolio-asset-${Date.now()}-${assetSequence++}`
const createPortfolioId = () => `portfolio-${Date.now()}-${portfolioSequence++}`

export const readPortfolioSyntheticPrice = (value: string) => {
  const symbol = toBaseSymbol(value)
  const syntheticPrices = readPortfolioSyntheticPriceMap()
  return Object.prototype.hasOwnProperty.call(syntheticPrices, symbol)
    ? syntheticPrices[symbol]
    : null
}

export const createPortfolioBalanceAsset = (
  overrides: Partial<PortfolioBalanceAssetInput> = {},
): PortfolioBalanceAssetInput => {
  const syntheticPrice = readPortfolioSyntheticPrice(overrides.symbol || '')
  const currentPrice = sanitizeNumber(overrides.currentPrice)
  return {
    id: overrides.id || createAssetId(),
    symbol: toBaseSymbol(overrides.symbol || ''),
    targetWeight: sanitizeNumber(overrides.targetWeight),
    units: sanitizeNumber(overrides.units),
    currentPrice: syntheticPrice !== null && currentPrice <= 0 ? syntheticPrice : currentPrice,
    seedValue: sanitizeNumber(overrides.seedValue),
  }
}

export const toPortfolioMarketSymbol = (value: string) => {
  const symbol = toBaseSymbol(value)
  if (!symbol || readPortfolioSyntheticPrice(symbol) !== null) return ''
  if (isIndexSymbol(symbol)) return symbol
  return `${symbol}/USDT`
}

export const collectPortfolioMarketTargets = (rawAssets: PortfolioBalanceAssetInput[]) => {
  const uniqueTargets = new Map<string, { symbol: string; marketSymbol: string }>()
  rawAssets.forEach((asset) => {
    const symbol = toBaseSymbol(asset.symbol)
    const marketSymbol = toPortfolioMarketSymbol(asset.symbol)
    if (!symbol || !marketSymbol || uniqueTargets.has(symbol)) return
    uniqueTargets.set(symbol, { symbol, marketSymbol })
  })
  return [...uniqueTargets.values()]
}

export const computePortfolioAssetHoldingValue = (asset: Pick<PortfolioBalanceAssetInput, 'units' | 'currentPrice'>) => (
  sanitizeNumber(asset.units) * sanitizeNumber(asset.currentPrice)
)

export const buildNormalizedPortfolioWeights = (assets: PortfolioBalanceAssetInput[]) => {
  const targetWeightInputSum = assets.reduce((sum, asset) => sum + sanitizeNumber(asset.targetWeight), 0)
  if (assets.length === 0) {
    return { targetWeightInputSum: 0, usesEqualWeightFallback: false, normalizedWeights: [] as number[] }
  }
  if (targetWeightInputSum <= 0) {
    const equalWeight = 1 / assets.length
    return { targetWeightInputSum, usesEqualWeightFallback: true, normalizedWeights: assets.map(() => equalWeight) }
  }
  return {
    targetWeightInputSum,
    usesEqualWeightFallback: false,
    normalizedWeights: assets.map((asset) => sanitizeNumber(asset.targetWeight) / targetWeightInputSum),
  }
}

export const createDefaultPortfolioBalanceAssets = (): PortfolioBalanceAssetInput[] => ([
  createPortfolioBalanceAsset({ symbol: 'BTC', targetWeight: 30 }),
  createPortfolioBalanceAsset({ symbol: 'USDT', targetWeight: 40 }),
  createPortfolioBalanceAsset({ symbol: 'ETH', targetWeight: 10 }),
  createPortfolioBalanceAsset({ symbol: 'BNB', targetWeight: 10 }),
  createPortfolioBalanceAsset({ symbol: 'SOL', targetWeight: 5 }),
  createPortfolioBalanceAsset({ symbol: 'OKB', targetWeight: 5 }),
])

export const createDefaultPortfolioBalanceStrategyConfig = (): PortfolioBalanceStrategyConfig => ({
  rebalanceBand: 5,
  minTradeAmount: 10,
  reviewFrequency: DEFAULT_REVIEW_FREQUENCY,
})

export const createDefaultPortfolioBalanceTrackingConfig = (): PortfolioBalanceTrackingConfig => ({
  virtualCapital: 100000,
  inceptionDate: todayIso(),
})

export const createDefaultPortfolioBalanceBacktestConfig = (): PortfolioBalanceBacktestConfig => ({
  initialCapital: 100000,
  backtestStartDate: daysAgoIso(365),
})

export const normalizePortfolioBalanceAsset = (value: unknown): PortfolioBalanceAssetInput => {
  if (!isRecord(value)) return createPortfolioBalanceAsset()
  return createPortfolioBalanceAsset({
    id: readString(value.id, createAssetId()),
    symbol: toBaseSymbol(readString(value.symbol, '')),
    targetWeight: sanitizeNumber(value.targetWeight),
    units: sanitizeNumber(value.units),
    currentPrice: sanitizeNumber(value.currentPrice),
    seedValue: sanitizeNumber(value.seedValue),
  })
}

export const normalizePortfolioBalanceStrategyConfig = (value: unknown): PortfolioBalanceStrategyConfig => {
  const defaults = createDefaultPortfolioBalanceStrategyConfig()
  if (!isRecord(value)) return defaults

  const rawFrequency = readString(value.reviewFrequency, defaults.reviewFrequency)
  const reviewFrequency: PortfolioReviewFrequency =
    rawFrequency === 'daily' || rawFrequency === 'weekly' || rawFrequency === 'monthly' || rawFrequency === 'quarterly'
      ? rawFrequency
      : DEFAULT_REVIEW_FREQUENCY

  return {
    rebalanceBand: clamp(readNumber(value.rebalanceBand, defaults.rebalanceBand), 0, 100),
    minTradeAmount: sanitizeNumber(value.minTradeAmount, defaults.minTradeAmount),
    reviewFrequency,
  }
}

export const normalizePortfolioBalanceTrackingConfig = (value: unknown): PortfolioBalanceTrackingConfig => {
  const defaults = createDefaultPortfolioBalanceTrackingConfig()
  if (!isRecord(value)) return defaults

  return {
    virtualCapital: sanitizeNumber(value.virtualCapital, defaults.virtualCapital),
    inceptionDate: readString(value.inceptionDate, defaults.inceptionDate),
  }
}

export const normalizePortfolioBalanceBacktestConfig = (value: unknown): PortfolioBalanceBacktestConfig => {
  const defaults = createDefaultPortfolioBalanceBacktestConfig()
  if (!isRecord(value)) return defaults

  return {
    initialCapital: sanitizeNumber(value.initialCapital, defaults.initialCapital),
    backtestStartDate: readString(value.backtestStartDate, defaults.backtestStartDate),
  }
}

export const normalizePortfolioBacktestEquityPoint = (value: unknown): PortfolioBacktestEquityPoint => {
  if (!isRecord(value)) {
    return {
      id: 0,
      timestamp: '',
      equity: 0,
      pnl_abs: 0,
      drawdown_pct: 0,
    }
  }

  return {
    id: Math.max(readNumber(value.id, 0), 0),
    timestamp: readString(value.timestamp, ''),
    equity: sanitizeNumber(value.equity),
    pnl_abs: readNumber(value.pnl_abs, 0),
    drawdown_pct: sanitizeNumber(value.drawdown_pct),
  }
}

export const normalizePortfolioBacktestSummary = (value: unknown): PortfolioBacktestSummary | null => {
  if (!isRecord(value)) return null

  return {
    startDate: readString(value.startDate, ''),
    endDate: readString(value.endDate, ''),
    initialValue: sanitizeNumber(value.initialValue),
    finalValue: sanitizeNumber(value.finalValue),
    totalReturnPct: readNumber(value.totalReturnPct, 0),
    annualizedReturnPct: value.annualizedReturnPct === null ? null : readNumber(value.annualizedReturnPct, 0),
    maxDrawdownPct: sanitizeNumber(value.maxDrawdownPct),
    reviewCount: Math.max(readNumber(value.reviewCount, 0), 0),
    outOfBandReviewCount: Math.max(readNumber(value.outOfBandReviewCount, 0), 0),
    rebalanceCount: Math.max(readNumber(value.rebalanceCount, 0), 0),
    equityCurve: Array.isArray(value.equityCurve)
      ? value.equityCurve.map((item) => normalizePortfolioBacktestEquityPoint(item))
      : [],
  }
}

type PortfolioBalancePortfolioOverrides = Omit<Partial<PortfolioBalancePortfolio>, 'assets'> & {
  assets?: Partial<PortfolioBalanceAssetInput>[]
}

export const createPortfolioBalancePortfolio = (
  overrides: PortfolioBalancePortfolioOverrides = {},
): PortfolioBalancePortfolio => {
  const timestamp = todayIso()
  const holdingsSource: PortfolioHoldingsSource | null =
    overrides.holdingsSource === 'virtual' || overrides.holdingsSource === 'paper'
      ? overrides.holdingsSource
      : null

  return {
    id: overrides.id || createPortfolioId(),
    name: readString(overrides.name, '新组合'),
    assets: Array.isArray(overrides.assets) && overrides.assets.length
      ? overrides.assets.map((asset) => normalizePortfolioBalanceAsset(asset))
      : createDefaultPortfolioBalanceAssets(),
    strategy: normalizePortfolioBalanceStrategyConfig(overrides.strategy),
    tracking: normalizePortfolioBalanceTrackingConfig(overrides.tracking),
    backtest: normalizePortfolioBalanceBacktestConfig(overrides.backtest),
    lastBacktestResult: normalizePortfolioBacktestSummary(overrides.lastBacktestResult),
    holdingsInitializedAt: typeof overrides.holdingsInitializedAt === 'string' ? overrides.holdingsInitializedAt : null,
    lastPriceUpdatedAt: typeof overrides.lastPriceUpdatedAt === 'string' ? overrides.lastPriceUpdatedAt : null,
    seedCapital: typeof overrides.seedCapital === 'number' ? overrides.seedCapital : null,
    holdingsSource,
    createdAt: readString(overrides.createdAt, timestamp),
    updatedAt: readString(overrides.updatedAt, timestamp),
  }
}

export const copyPortfolioBalancePortfolio = (
  source: PortfolioBalancePortfolio,
  overrides: Pick<Partial<PortfolioBalancePortfolio>, 'name'> = {},
): PortfolioBalancePortfolio => createPortfolioBalancePortfolio({
  name: readString(overrides.name, source.name),
  assets: source.assets.map((asset) => ({
    symbol: asset.symbol,
    targetWeight: asset.targetWeight,
    units: asset.units,
    currentPrice: asset.currentPrice,
    seedValue: asset.seedValue,
  })),
  strategy: { ...source.strategy },
  tracking: { ...source.tracking },
  backtest: { ...source.backtest },
  lastBacktestResult: source.lastBacktestResult
    ? {
        ...source.lastBacktestResult,
        equityCurve: source.lastBacktestResult.equityCurve.map((point) => ({ ...point })),
      }
    : null,
  holdingsInitializedAt: source.holdingsInitializedAt,
  lastPriceUpdatedAt: source.lastPriceUpdatedAt,
  seedCapital: source.seedCapital,
  holdingsSource: source.holdingsSource,
})

export const createDefaultPortfolioCollection = (): PortfolioBalancePortfolio[] => ([
  createPortfolioBalancePortfolio({
    name: '长期核心组合',
  }),
])

export const normalizePortfolioBalancePortfolio = (value: unknown): PortfolioBalancePortfolio => {
  const defaults = createPortfolioBalancePortfolio()
  if (!isRecord(value)) return defaults

  const rawHoldingsSource = readString(value.holdingsSource, '')
  const holdingsSource: PortfolioHoldingsSource | null =
    rawHoldingsSource === 'virtual' || rawHoldingsSource === 'paper'
      ? rawHoldingsSource
      : null

  return {
    id: readString(value.id, defaults.id),
    name: readString(value.name, defaults.name),
    assets: Array.isArray(value.assets) && value.assets.length
      ? value.assets.map((asset) => normalizePortfolioBalanceAsset(asset))
      : defaults.assets,
    strategy: normalizePortfolioBalanceStrategyConfig(value.strategy),
    tracking: normalizePortfolioBalanceTrackingConfig(value.tracking),
    backtest: normalizePortfolioBalanceBacktestConfig(value.backtest),
    lastBacktestResult: normalizePortfolioBacktestSummary(value.lastBacktestResult),
    holdingsInitializedAt: typeof value.holdingsInitializedAt === 'string' ? value.holdingsInitializedAt : null,
    lastPriceUpdatedAt: typeof value.lastPriceUpdatedAt === 'string' ? value.lastPriceUpdatedAt : null,
    seedCapital: typeof value.seedCapital === 'number' ? value.seedCapital : null,
    holdingsSource,
    createdAt: readString(value.createdAt, defaults.createdAt),
    updatedAt: readString(value.updatedAt, defaults.updatedAt),
  }
}

export const createDefaultPortfolioBalanceSnapshot = (): PortfolioBalanceSnapshot => {
  const portfolios = createDefaultPortfolioCollection()
  return {
    activePortfolioId: portfolios[0].id,
    portfolios,
  }
}

export const normalizePortfolioBalanceSnapshot = (
  value: unknown,
  fallback = createDefaultPortfolioBalanceSnapshot(),
): PortfolioBalanceSnapshot => {
  const defaults = fallback
  if (!isRecord(value)) return defaults

  const portfolios = Array.isArray(value.portfolios) && value.portfolios.length
    ? value.portfolios.map((item) => normalizePortfolioBalancePortfolio(item))
    : defaults.portfolios
  const nextActivePortfolioId = readString(value.activePortfolioId, portfolios[0]?.id || defaults.activePortfolioId)

  return {
    activePortfolioId: nextActivePortfolioId,
    portfolios: portfolios.length ? portfolios : [createPortfolioBalancePortfolio()],
  }
}

export const buildPortfolioBalanceSnapshot = (snapshot: PortfolioBalanceSnapshot): PortfolioBalanceSnapshot => (
  normalizePortfolioBalanceSnapshot(snapshot)
)

export const touchPortfolio = (portfolio: PortfolioBalancePortfolio) => {
  portfolio.updatedAt = new Date().toISOString()
}

export const hasMarketGap = (portfolio: PortfolioBalancePortfolio) => (
  portfolio.assets.some((asset) => toBaseSymbol(asset.symbol) && (!asset.currentPrice || asset.currentPrice <= 0))
)

export const hasActiveAssets = (portfolio: PortfolioBalancePortfolio) => (
  portfolio.assets.some((asset) => Boolean(toBaseSymbol(asset.symbol)))
)
