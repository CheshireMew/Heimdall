import { marketApi } from '@/modules/market'
import type { PortfolioBalancePortfolio } from '@/types'

import { buildPortfolioSyntheticHistory } from './backtest'
import { collectPortfolioMarketTargets, normalizePortfolioAssetSymbol, readPortfolioSyntheticPrice } from './model'

export const fetchPortfolioPriceMap = async (portfolio: PortfolioBalancePortfolio) => {
  const priceBySymbol = new Map<string, number>()
  portfolio.assets.forEach((asset) => {
    const symbol = normalizePortfolioAssetSymbol(asset.symbol)
    const syntheticPrice = readPortfolioSyntheticPrice(symbol)
    if (!symbol || syntheticPrice === null || priceBySymbol.has(symbol)) return
    priceBySymbol.set(symbol, syntheticPrice)
  })

  const targets = collectPortfolioMarketTargets(portfolio.assets)
  if (!targets.length && !priceBySymbol.size) throw new Error('请先填写至少一个标的')

  const responses = await Promise.allSettled(
    targets.map((item) => marketApi.getRealtime({ symbol: item.marketSymbol, timeframe: '1d', limit: 2 })),
  )

  let successCount = priceBySymbol.size
  const failedSymbols: string[] = []
  responses.forEach((result, index) => {
    if (result.status !== 'fulfilled') {
      failedSymbols.push(targets[index].symbol)
      return
    }
    const currentPrice = Number(result.value.data?.current_price || 0)
    if (!currentPrice) {
      failedSymbols.push(targets[index].symbol)
      return
    }
    priceBySymbol.set(targets[index].symbol, currentPrice)
    successCount += 1
  })

  if (!successCount) throw new Error('没有任何标的成功获取到实时价格')
  return { priceBySymbol, successCount, failedSymbols }
}

export const loadPortfolioBacktestHistory = async (
  portfolio: PortfolioBalancePortfolio,
  startText: string,
) => {
  const historyBySymbol: Record<string, Array<{ date: string; close: number }>> = {}

  portfolio.assets.forEach((asset) => {
    const symbol = normalizePortfolioAssetSymbol(asset.symbol)
    if (!symbol || historyBySymbol[symbol]) return
    const syntheticHistory = buildPortfolioSyntheticHistory(symbol, startText)
    if (syntheticHistory.length) historyBySymbol[symbol] = syntheticHistory
  })

  const targets = collectPortfolioMarketTargets(portfolio.assets)
  if (!targets.length && !Object.keys(historyBySymbol).length) throw new Error('请先填写至少一个标的')

  if (!targets.length) return historyBySymbol

  const response = await marketApi.getBatchFullHistory({
    symbols: targets.map((item) => item.marketSymbol),
    timeframe: '1d',
    start_date: startText,
  })
  const responseMap = response.data || {}
  const failedSymbols = targets
    .filter((item) => !Array.isArray(responseMap[item.marketSymbol]))
    .map((item) => item.symbol)

  if (failedSymbols.length) {
    throw new Error(`以下标的历史数据获取失败: ${failedSymbols.join(', ')}`)
  }

  targets.forEach((item) => {
    historyBySymbol[item.symbol] = (responseMap[item.marketSymbol] || [])
      .map((row) => {
        const timestamp = Array.isArray(row) ? Number(row[0]) : 0
        const close = Array.isArray(row) ? Number(row[4]) : 0
        return {
          date: new Date(timestamp).toISOString().slice(0, 10),
          close,
        }
      })
      .filter((point) => point.date && point.close > 0)
  })

  return historyBySymbol
}
