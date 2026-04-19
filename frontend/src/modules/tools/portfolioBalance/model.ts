import type {
  PortfolioBalanceAssetInput,
  PortfolioBacktestSummary,
  PortfolioBacktestEquityPoint,
  PortfolioBalanceBacktestConfig,
  PortfolioHoldingsSource,
  PortfolioBalancePortfolio,
  PortfolioReviewFrequency,
  PortfolioBalanceStrategyConfig,
  PortfolioBalanceTrackingConfig,
} from './contracts'
import { isRecord, readNumber, readString } from '@/composables/pageSnapshot'
import { isIndexSymbol } from '@/modules/market'

import {
  clamp,
  daysAgoIso,
  DEFAULT_REVIEW_FREQUENCY,
  PORTFOLIO_SYNTHETIC_PRICE_BY_SYMBOL,
  sanitizeNumber,
  todayIso,
} from './shared'

let assetSequence = 0
let portfolioSequence = 0

const createAssetId = () => `portfolio-asset-${Date.now()}-${assetSequence++}`
const createPortfolioId = () => `portfolio-${Date.now()}-${portfolioSequence++}`

export const normalizePortfolioAssetSymbol = (value: string) => {
  const trimmed = String(value || '').trim().toUpperCase()
  if (!trimmed) return ''
  const [base] = trimmed.split('/')
  const [assetCode] = base.split(':')
  return assetCode.trim()
}

export const readPortfolioSyntheticPrice = (value: string) => {
  const symbol = normalizePortfolioAssetSymbol(value)
  return Object.prototype.hasOwnProperty.call(PORTFOLIO_SYNTHETIC_PRICE_BY_SYMBOL, symbol)
    ? PORTFOLIO_SYNTHETIC_PRICE_BY_SYMBOL[symbol]
    : null
}

export const createPortfolioBalanceAsset = (
  overrides: Partial<PortfolioBalanceAssetInput> = {},
): PortfolioBalanceAssetInput => {
  const syntheticPrice = readPortfolioSyntheticPrice(overrides.symbol || '')
  const currentPrice = sanitizeNumber(overrides.currentPrice)
  return {
    id: overrides.id || createAssetId(),
    symbol: normalizePortfolioAssetSymbol(overrides.symbol || ''),
    targetWeight: sanitizeNumber(overrides.targetWeight),
    units: sanitizeNumber(overrides.units),
    currentPrice: syntheticPrice !== null && currentPrice <= 0 ? syntheticPrice : currentPrice,
    seedValue: sanitizeNumber(overrides.seedValue),
  }
}

export const toPortfolioMarketSymbol = (value: string) => {
  const symbol = normalizePortfolioAssetSymbol(value)
  if (!symbol || readPortfolioSyntheticPrice(symbol) !== null) return ''
  if (isIndexSymbol(symbol)) return symbol
  return `${symbol}/USDT`
}

export const collectPortfolioMarketTargets = (rawAssets: PortfolioBalanceAssetInput[]) => {
  const uniqueTargets = new Map<string, { symbol: string; marketSymbol: string }>()
  rawAssets.forEach((asset) => {
    const symbol = normalizePortfolioAssetSymbol(asset.symbol)
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
    symbol: normalizePortfolioAssetSymbol(readString(value.symbol, '')),
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
    virtualCapital: sanitizeNumber(value.virtualCapital ?? value.totalCapital, defaults.virtualCapital),
    inceptionDate: readString(value.inceptionDate ?? value.lastReviewDate, defaults.inceptionDate),
  }
}

export const normalizePortfolioBalanceBacktestConfig = (value: unknown): PortfolioBalanceBacktestConfig => {
  const defaults = createDefaultPortfolioBalanceBacktestConfig()
  if (!isRecord(value)) return defaults

  return {
    initialCapital: sanitizeNumber(value.initialCapital ?? value.totalCapital, defaults.initialCapital),
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
    strategy: normalizePortfolioBalanceStrategyConfig(value.strategy ?? value.config),
    tracking: normalizePortfolioBalanceTrackingConfig(value.tracking ?? value.config),
    backtest: normalizePortfolioBalanceBacktestConfig(value.backtest ?? value.config),
    lastBacktestResult: normalizePortfolioBacktestSummary(value.lastBacktestResult),
    holdingsInitializedAt: typeof value.holdingsInitializedAt === 'string' ? value.holdingsInitializedAt : null,
    lastPriceUpdatedAt: typeof value.lastPriceUpdatedAt === 'string' ? value.lastPriceUpdatedAt : null,
    seedCapital: typeof value.seedCapital === 'number' ? value.seedCapital : null,
    holdingsSource,
    createdAt: readString(value.createdAt, defaults.createdAt),
    updatedAt: readString(value.updatedAt, defaults.updatedAt),
  }
}
