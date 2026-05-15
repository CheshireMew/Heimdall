import { backtestApi } from '@/modules/backtest'
import { toBaseSymbol } from '@/modules/market'
import { todayLocalIsoDate } from '@/utils/localDate'

import { buildPortfolioBacktestSummary } from './backtest'
import { fetchPortfolioPriceMap, loadPortfolioBacktestHistory } from './data'
import {
  applyLatestMarketPrices,
  buildPortfolioAssetsFromPaperRun,
  clearPortfolioHoldings,
  readPaperRunCashBalance,
  readPaperRunTotalValue,
  seedPortfolioHoldingsFromMarket,
  selectLatestPaperRunForPortfolio,
} from './holdings'
import {
  createPortfolioBalanceAsset,
  readPortfolioSyntheticPrice,
} from './assets'
import { toPortfolioUserError } from './errors'
import { copyPortfolioInCollection, createPortfolioInCollection, deletePortfolioFromCollection } from './portfolioCrud'
import type { PortfolioBalancePageState } from './state'

export const createPortfolioBalancePageCommands = (state: PortfolioBalancePageState) => {
  let marketRefreshTimer: ReturnType<typeof setTimeout> | null = null

  const clearScheduledMarketRefresh = () => {
    if (!marketRefreshTimer) return
    clearTimeout(marketRefreshTimer)
    marketRefreshTimer = null
  }

  const refreshMarketPrices = async () => {
    const portfolio = state.activePortfolio.value
    if (!portfolio) return

    state.marketLoading.value = true
    state.resetFeedback()
    try {
      const { priceBySymbol, successCount, failedSymbols } = await fetchPortfolioPriceMap(portfolio)
      const needsSeed = (
        portfolio.holdingsSource !== 'paper'
        && (
          !portfolio.holdingsInitializedAt
          || portfolio.seedCapital !== portfolio.tracking.virtualCapital
          || portfolio.assets.some((asset) => toBaseSymbol(asset.symbol) && asset.units <= 0)
        )
      )
      if (needsSeed) {
        seedPortfolioHoldingsFromMarket(portfolio, priceBySymbol)
        state.sourceMessage.value = failedSymbols.length
          ? `已初始化 ${successCount} 个，失败: ${failedSymbols.join(', ')}`
          : `已初始化 ${successCount} 个标的`
      } else {
        applyLatestMarketPrices(portfolio, priceBySymbol)
        state.sourceMessage.value = failedSymbols.length
          ? `已刷新 ${successCount} 个，失败: ${failedSymbols.join(', ')}`
          : `已刷新 ${successCount} 个标的`
      }
    } catch (error: unknown) {
      state.sourceError.value = toPortfolioUserError(error, '刷新市场价格失败')
    } finally {
      state.marketLoading.value = false
    }
  }

  const scheduleMarketRefresh = (delay = 600) => {
    clearScheduledMarketRefresh()
    marketRefreshTimer = setTimeout(async () => {
      marketRefreshTimer = null
      const portfolio = state.activePortfolio.value
      if (!portfolio || state.marketLoading.value) return
      if (!portfolio.assets.some((asset) => toBaseSymbol(asset.symbol))) return
      await refreshMarketPrices()
    }, delay)
  }

  const selectPortfolio = (portfolioId: string) => {
    state.activePortfolioId.value = portfolioId
    state.resetFeedback()
  }

  const createPortfolio = () => {
    state.activePortfolioId.value = createPortfolioInCollection(state.portfolios)
    state.sourceMessage.value = '已创建新组合'
    state.sourceError.value = ''
  }

  const copyPortfolio = (portfolioId: string) => {
    const nextPortfolioId = copyPortfolioInCollection(state.portfolios, portfolioId)
    if (!nextPortfolioId) return
    state.activePortfolioId.value = nextPortfolioId
    state.sourceMessage.value = '组合已复制'
    state.sourceError.value = ''
  }

  const deletePortfolio = (portfolioId: string) => {
    state.activePortfolioId.value = deletePortfolioFromCollection(
      state.portfolios,
      portfolioId,
      state.activePortfolioId.value,
    )
    state.sourceMessage.value = '组合已删除'
    state.sourceError.value = ''
  }

  const addAsset = () => state.updateActivePortfolio((portfolio) => {
    portfolio.assets.push(createPortfolioBalanceAsset())
  })

  const removeAsset = (assetId: string) => state.updateActivePortfolio((portfolio) => {
    if (portfolio.assets.length <= 2) return
    const index = portfolio.assets.findIndex((asset) => asset.id === assetId)
    if (index < 0) return

    portfolio.assets.splice(index, 1)
    if (portfolio.holdingsSource !== 'paper') {
      clearPortfolioHoldings(portfolio, 'virtual')
      scheduleMarketRefresh()
    }
  })

  const updateAssetSymbol = (assetId: string, rawValue: string) => {
    let shouldRefresh = false
    state.updateActivePortfolio((portfolio) => {
      const asset = portfolio.assets.find((item) => item.id === assetId)
      if (!asset) return

      const previousSymbol = toBaseSymbol(asset.symbol)
      const nextSymbol = toBaseSymbol(rawValue)
      if (previousSymbol === nextSymbol) return

      asset.symbol = nextSymbol
      asset.currentPrice = readPortfolioSyntheticPrice(nextSymbol) ?? 0
      asset.units = 0
      if (!nextSymbol) {
        asset.targetWeight = 0
      }

      clearPortfolioHoldings(portfolio, 'virtual')
      shouldRefresh = true
    })

    if (!shouldRefresh) return
    state.resetFeedback()
    scheduleMarketRefresh()
  }

  const updateAssetTargetWeight = (assetId: string, rawValue: string | number) => state.updateActivePortfolio((portfolio) => {
    const asset = portfolio.assets.find((item) => item.id === assetId)
    if (!asset) return

    const nextWeight = Number(rawValue)
    asset.targetWeight = Number.isFinite(nextWeight) && nextWeight > 0 ? nextWeight : 0
    if (portfolio.holdingsSource !== 'paper') {
      clearPortfolioHoldings(portfolio, 'virtual')
      scheduleMarketRefresh()
    }
  })

  const importLatestPaperHoldings = async () => {
    state.importLoading.value = true
    state.resetFeedback()
    try {
      const response = await backtestApi.listPaperRuns()
      const targetRun = selectLatestPaperRunForPortfolio(response || [])
      if (!targetRun) throw new Error('没有找到可导入的模拟盘持仓')

      const importedAssets = buildPortfolioAssetsFromPaperRun(targetRun)
      if (!importedAssets.length) throw new Error('最近的模拟盘记录里没有持仓')

      state.updateActivePortfolio((portfolio) => {
        const previousWeightBySymbol = new Map(
          portfolio.assets.map((asset) => [toBaseSymbol(asset.symbol), Number(asset.targetWeight) || 0]),
        )
        const importedTotalValue = readPaperRunTotalValue(targetRun)
        const nextAssets = importedAssets.map((asset) => ({
          ...asset,
          targetWeight: previousWeightBySymbol.get(toBaseSymbol(asset.symbol)) || 0,
          seedValue: importedTotalValue > 0 ? Number((asset.units * asset.currentPrice).toFixed(2)) : 0,
        }))

        portfolio.assets.splice(0, portfolio.assets.length, ...nextAssets)
        portfolio.holdingsInitializedAt = new Date().toISOString()
        portfolio.lastPriceUpdatedAt = new Date().toISOString()
        portfolio.seedCapital = importedTotalValue + readPaperRunCashBalance(targetRun)
        portfolio.holdingsSource = 'paper'
        portfolio.tracking.virtualCapital = portfolio.seedCapital
        portfolio.backtest.initialCapital = portfolio.seedCapital
        portfolio.tracking.inceptionDate = todayLocalIsoDate()
      })

      state.lastImportedRun.value = targetRun
      state.sourceMessage.value = `已导入模拟盘 #${targetRun.id}`
    } catch (error: unknown) {
      state.sourceError.value = toPortfolioUserError(error, '导入模拟盘持仓失败')
    } finally {
      state.importLoading.value = false
    }
  }

  const runBacktest = async () => {
    const portfolio = state.activePortfolio.value
    if (!portfolio) return

    state.backtestLoading.value = true
    state.resetFeedback()
    state.updateActivePortfolio((currentPortfolio) => {
      currentPortfolio.lastBacktestResult = null
    })
    try {
      const startText = portfolio.backtest.backtestStartDate
      if (!startText) throw new Error('请先选择回测开始日期')

      const historyBySymbol = await loadPortfolioBacktestHistory(portfolio, startText)
      const nextResult = buildPortfolioBacktestSummary(
        historyBySymbol,
        portfolio.assets,
        portfolio.strategy,
        portfolio.backtest,
        startText,
      )
      if (!nextResult) throw new Error('回测样本不足，无法生成结果')

      state.updateActivePortfolio((currentPortfolio) => {
        currentPortfolio.lastBacktestResult = nextResult
      })
      state.sourceMessage.value = `已生成 ${nextResult.startDate} 到 ${nextResult.endDate} 的回测结果`
    } catch (error: unknown) {
      state.sourceError.value = toPortfolioUserError(error, '组合回测失败')
    } finally {
      state.backtestLoading.value = false
    }
  }

  return {
    clearScheduledMarketRefresh,
    refreshMarketPrices,
    scheduleMarketRefresh,
    selectPortfolio,
    createPortfolio,
    copyPortfolio,
    deletePortfolio,
    addAsset,
    removeAsset,
    updateAssetSymbol,
    updateAssetTargetWeight,
    importLatestPaperHoldings,
    runBacktest,
  }
}
