import {
  copyPortfolioBalancePortfolio,
  createDefaultPortfolioCollection,
  createPortfolioBalancePortfolio,
} from './snapshot'
import type { PortfolioBalancePortfolio } from './types'

export const buildCopiedPortfolioName = (
  portfolios: PortfolioBalancePortfolio[],
  sourceName: string,
) => {
  const baseName = sourceName.trim() || '组合'
  const copyName = `${baseName} 副本`
  const existingNames = new Set(portfolios.map((portfolio) => portfolio.name))
  if (!existingNames.has(copyName)) return copyName

  let sequence = 2
  while (existingNames.has(`${copyName} ${sequence}`)) {
    sequence += 1
  }
  return `${copyName} ${sequence}`
}

export const createPortfolioInCollection = (
  portfolios: PortfolioBalancePortfolio[],
) => {
  const nextPortfolio = createPortfolioBalancePortfolio({
    name: `组合 ${portfolios.length + 1}`,
  })
  portfolios.unshift(nextPortfolio)
  return nextPortfolio.id
}

export const copyPortfolioInCollection = (
  portfolios: PortfolioBalancePortfolio[],
  portfolioId: string,
) => {
  const index = portfolios.findIndex((portfolio) => portfolio.id === portfolioId)
  if (index < 0) return ''

  const sourcePortfolio = portfolios[index]
  const nextPortfolio = copyPortfolioBalancePortfolio(sourcePortfolio, {
    name: buildCopiedPortfolioName(portfolios, sourcePortfolio.name),
  })
  portfolios.splice(index + 1, 0, nextPortfolio)
  return nextPortfolio.id
}

export const deletePortfolioFromCollection = (
  portfolios: PortfolioBalancePortfolio[],
  portfolioId: string,
  activePortfolioId: string,
) => {
  const index = portfolios.findIndex((portfolio) => portfolio.id === portfolioId)
  if (index < 0) return activePortfolioId

  portfolios.splice(index, 1)
  if (!portfolios.length) {
    const fallback = createDefaultPortfolioCollection()[0]
    portfolios.push(fallback)
    return fallback.id
  }
  if (activePortfolioId === portfolioId) {
    return portfolios[0].id
  }
  return activePortfolioId
}
