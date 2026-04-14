import { isIndexSymbol, marketApi } from '@/modules/market'
import type { PortfolioBalancePortfolio } from '@/types'

import { buildPortfolioSyntheticHistory } from './backtest'
import { collectPortfolioMarketTargets, normalizePortfolioAssetSymbol, readPortfolioSyntheticPrice } from './model'

type PortfolioHistoryPoint = { date: string; close: number }
type PortfolioHistoryMap = Record<string, PortfolioHistoryPoint[]>

const HISTORY_CACHE_LIMIT = 80
const portfolioHistoryCache = new Map<string, Promise<PortfolioHistoryPoint[]>>()
const portfolioHistoryMapCache = new Map<string, Promise<PortfolioHistoryMap>>()

const cloneHistory = (history: PortfolioHistoryPoint[]) => history.map((point) => ({ ...point }))
const cloneHistoryMap = (historyMap: PortfolioHistoryMap) => Object.fromEntries(
  Object.entries(historyMap).map(([symbol, history]) => [symbol, cloneHistory(history)]),
)

const rememberHistory = (key: string, loader: () => Promise<PortfolioHistoryPoint[]>) => {
  let promise = portfolioHistoryCache.get(key)
  if (!promise) {
    promise = loader()
    portfolioHistoryCache.set(key, promise)
    promise.catch(() => {
      if (portfolioHistoryCache.get(key) === promise) portfolioHistoryCache.delete(key)
    })
    if (portfolioHistoryCache.size > HISTORY_CACHE_LIMIT) {
      const oldestKey = portfolioHistoryCache.keys().next().value
      if (oldestKey) portfolioHistoryCache.delete(oldestKey)
    }
  }
  return promise.then(cloneHistory)
}

const rememberHistoryMap = (key: string, loader: () => Promise<PortfolioHistoryMap>) => {
  let promise = portfolioHistoryMapCache.get(key)
  if (!promise) {
    promise = loader()
    portfolioHistoryMapCache.set(key, promise)
    promise.catch(() => {
      if (portfolioHistoryMapCache.get(key) === promise) portfolioHistoryMapCache.delete(key)
    })
    if (portfolioHistoryMapCache.size > HISTORY_CACHE_LIMIT) {
      const oldestKey = portfolioHistoryMapCache.keys().next().value
      if (oldestKey) portfolioHistoryMapCache.delete(oldestKey)
    }
  }
  return promise.then(cloneHistoryMap)
}

const rowsToHistory = (rows: any[]): PortfolioHistoryPoint[] => rows
  .map((row) => {
    const timestamp = Array.isArray(row) ? Number(row[0]) : 0
    const close = Array.isArray(row) ? Number(row[4]) : 0
    return {
      date: new Date(timestamp).toISOString().slice(0, 10),
      close,
    }
  })
  .filter((point) => point.date && point.close > 0)

const loadCryptoHistoryMap = async (symbols: string[], startText: string) => {
  const cacheKey = `crypto:${symbols.slice().sort().join(',')}:1d:${startText}`
  return rememberHistoryMap(cacheKey, async () => {
    const response = await marketApi.getBatchFullHistory({
      symbols,
      timeframe: '1d',
      start_date: startText,
    })
    return Object.fromEntries(
      symbols.map((symbol) => [symbol, rowsToHistory(response.data?.[symbol] || [])]),
    )
  })
}

const loadIndexHistory = async (symbol: string, startText: string) => {
  const cacheKey = `index-pricing:${symbol}:1d:${startText}`
  return rememberHistory(cacheKey, async () => {
    const response = await marketApi.getIndexPricingHistory({
      symbol,
      timeframe: '1d',
      start_date: startText,
    })
    return rowsToHistory(response.data.data || [])
  })
}

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

  const latestStartDate = new Date(Date.now() - 30 * 86400000).toISOString().slice(0, 10)
  const responses = await Promise.allSettled(
    targets.map((item) => isIndexSymbol(item.marketSymbol)
      ? loadIndexHistory(item.marketSymbol, latestStartDate)
      : marketApi.getRealtime({ symbol: item.marketSymbol, timeframe: '1d', limit: 2 })),
  )

  let successCount = priceBySymbol.size
  const failedSymbols: string[] = []
  responses.forEach((result, index) => {
    if (result.status !== 'fulfilled') {
      failedSymbols.push(targets[index].symbol)
      return
    }
    const payload = isIndexSymbol(targets[index].marketSymbol) ? null : result.value.data
    const indexRows = isIndexSymbol(targets[index].marketSymbol) && Array.isArray(result.value) ? result.value : []
    const currentPrice = Number(
      isIndexSymbol(targets[index].marketSymbol)
        ? indexRows[indexRows.length - 1]?.close || 0
        : payload?.current_price || 0,
    )
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

  const cryptoTargets = targets.filter((item) => !isIndexSymbol(item.marketSymbol))
  const indexTargets = targets.filter((item) => isIndexSymbol(item.marketSymbol))
  const responseMap: PortfolioHistoryMap = {}

  if (cryptoTargets.length) {
    Object.assign(responseMap, await loadCryptoHistoryMap(
      cryptoTargets.map((item) => item.marketSymbol),
      startText,
    ))
  }

  const indexResponses = await Promise.allSettled(
    indexTargets.map((item) => loadIndexHistory(item.marketSymbol, startText)),
  )
  indexResponses.forEach((result, index) => {
    if (result.status === 'fulfilled') {
      responseMap[indexTargets[index].marketSymbol] = result.value
    }
  })

  const failedSymbols = targets
    .filter((item) => !Array.isArray(responseMap[item.marketSymbol]))
    .map((item) => item.symbol)

  if (failedSymbols.length) {
    throw new Error(`以下标的历史数据获取失败: ${failedSymbols.join(', ')}`)
  }

  targets.forEach((item) => {
    historyBySymbol[item.symbol] = cloneHistory(responseMap[item.marketSymbol] || [])
  })

  return historyBySymbol
}
