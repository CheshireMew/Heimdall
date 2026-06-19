import type { PortfolioBalancePortfolio, PortfolioHoldingsSource } from './types'

import {
  buildNormalizedPortfolioWeights,
} from './assets'
import {
  round,
  sanitizeNumber,
} from './number'
import { toBaseSymbol } from '@/modules/market'

export const clearPortfolioHoldings = (
  portfolio: PortfolioBalancePortfolio,
  nextSource: PortfolioHoldingsSource | null = null,
) => {
  portfolio.assets.forEach((asset) => {
    if (!toBaseSymbol(asset.symbol)) return
    asset.units = 0
    asset.seedValue = 0
  })
  portfolio.holdingsInitializedAt = null
  portfolio.lastPriceUpdatedAt = null
  portfolio.seedCapital = null
  portfolio.holdingsSource = nextSource
}

export const seedPortfolioHoldingsFromMarket = (
  portfolio: PortfolioBalancePortfolio,
  priceBySymbol: Map<string, number>,
) => {
  const { normalizedWeights } = buildNormalizedPortfolioWeights(portfolio.assets)
  portfolio.assets.forEach((asset, index) => {
    const symbol = toBaseSymbol(asset.symbol)
    const normalizedTargetWeight = normalizedWeights[index] || 0
    const currentPrice = sanitizeNumber(priceBySymbol.get(symbol), asset.currentPrice)
    const seedValue = round(portfolio.tracking.virtualCapital * normalizedTargetWeight, 2)
    asset.currentPrice = currentPrice
    asset.seedValue = seedValue
    asset.units = currentPrice > 0 ? round(seedValue / currentPrice, 8) : 0
  })

  const timestamp = new Date().toISOString()
  portfolio.holdingsInitializedAt = timestamp
  portfolio.lastPriceUpdatedAt = timestamp
  portfolio.seedCapital = portfolio.tracking.virtualCapital
  portfolio.holdingsSource = 'virtual'
}

export const applyLatestMarketPrices = (
  portfolio: PortfolioBalancePortfolio,
  priceBySymbol: Map<string, number>,
) => {
  portfolio.assets.forEach((asset) => {
    const symbol = toBaseSymbol(asset.symbol)
    asset.currentPrice = sanitizeNumber(priceBySymbol.get(symbol), asset.currentPrice)
  })
  portfolio.lastPriceUpdatedAt = new Date().toISOString()
}
