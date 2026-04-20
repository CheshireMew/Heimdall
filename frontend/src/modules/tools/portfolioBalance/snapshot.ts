import type { PortfolioBalancePortfolio } from './contracts'
import { isRecord, readString } from '@/composables/pageSnapshot'
import { toBaseSymbol } from '@/modules/market'

import {
  createDefaultPortfolioCollection,
  createPortfolioBalancePortfolio,
  normalizePortfolioBalancePortfolio,
} from './model'

export interface PortfolioBalanceSnapshot {
  activePortfolioId: string
  portfolios: PortfolioBalancePortfolio[]
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
