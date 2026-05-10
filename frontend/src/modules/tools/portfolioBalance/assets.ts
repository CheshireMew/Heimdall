import { isIndexSymbol, readCashSymbolPrices, toBaseSymbol } from '@/modules/market'
import { sanitizeNumber } from './number'
import type { PortfolioBalanceAssetInput } from './types'

let assetSequence = 0

const createAssetId = () => `portfolio-asset-${Date.now()}-${assetSequence++}`

export const readPortfolioSyntheticPriceMap = () => readCashSymbolPrices()

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
