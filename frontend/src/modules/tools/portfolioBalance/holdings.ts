import { isPaperLiveMetadata } from '@/modules/backtest'
import type { BacktestPaperPositionResponse, BacktestRunResponse } from '../../../types/backtest'
import type { PortfolioBalancePortfolio, PortfolioHoldingsSource } from './model'

import {
  buildNormalizedPortfolioWeights,
  createPortfolioBalanceAsset,
  readPortfolioSyntheticPrice,
} from './model'
import {
  round,
  sanitizeNumber,
} from './model'
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

const readPaperPositions = (run: BacktestRunResponse) => {
  const positions = isPaperLiveMetadata(run.metadata) ? run.metadata.paper_live?.positions : null
  return Array.isArray(positions) ? positions : []
}

const toPortfolioAssetFromPaperPosition = (position: BacktestPaperPositionResponse) => createPortfolioBalanceAsset({
  symbol: toBaseSymbol(position.symbol),
  units: sanitizeNumber(position.remaining_amount),
  currentPrice: sanitizeNumber(position.last_price || position.entry_price || readPortfolioSyntheticPrice(position.symbol)),
  targetWeight: 0,
})

export const selectLatestPaperRunForPortfolio = (runs: BacktestRunResponse[]) => {
  const candidates = [...runs]
    .filter((run) => readPaperPositions(run).length > 0)
    .sort((left, right) => new Date(right.created_at || 0).getTime() - new Date(left.created_at || 0).getTime())

  const runningCandidate = candidates.find((run) => String(run.status || '').toLowerCase() === 'running')
  return runningCandidate || candidates[0] || null
}

export const buildPortfolioAssetsFromPaperRun = (run: BacktestRunResponse) => readPaperPositions(run).map(toPortfolioAssetFromPaperPosition)

export const readPaperRunCashBalance = (run: BacktestRunResponse) => (
  sanitizeNumber(isPaperLiveMetadata(run.metadata) ? run.metadata.paper_live?.cash_balance : null)
)

export const readPaperRunTotalValue = (run: BacktestRunResponse) => (
  round(
    buildPortfolioAssetsFromPaperRun(run).reduce((sum, asset) => sum + asset.units * asset.currentPrice, 0),
    2,
  )
)
