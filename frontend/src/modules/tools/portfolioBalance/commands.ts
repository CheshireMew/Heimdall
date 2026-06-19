import { toBaseSymbol } from '@/modules/market'

import { buildPortfolioSimulationSummary } from './simulation'
import { fetchPortfolioPriceMap, loadPortfolioSimulationHistory } from './data'
import {
  applyLatestMarketPrices,
  clearPortfolioHoldings,
  seedPortfolioHoldingsFromMarket,
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
        !portfolio.holdingsInitializedAt
        || portfolio.seedCapital !== portfolio.tracking.virtualCapital
        || portfolio.assets.some((asset) => toBaseSymbol(asset.symbol) && asset.units <= 0)
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
    clearPortfolioHoldings(portfolio, 'virtual')
    scheduleMarketRefresh()
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
    clearPortfolioHoldings(portfolio, 'virtual')
    scheduleMarketRefresh()
  })

  const runSimulation = async () => {
    const portfolio = state.activePortfolio.value
    if (!portfolio) return

    state.simulationLoading.value = true
    state.resetFeedback()
    state.updateActivePortfolio((currentPortfolio) => {
      currentPortfolio.lastSimulationResult = null
    })
    try {
      const startText = portfolio.simulation.simulationStartDate
      if (!startText) throw new Error('请先选择模拟开始日期')

      const historyBySymbol = await loadPortfolioSimulationHistory(portfolio, startText)
      const nextResult = buildPortfolioSimulationSummary(
        historyBySymbol,
        portfolio.assets,
        portfolio.strategy,
        portfolio.simulation,
        startText,
      )
      if (!nextResult) throw new Error('历史样本不足，无法生成模拟结果')

      state.updateActivePortfolio((currentPortfolio) => {
        currentPortfolio.lastSimulationResult = nextResult
      })
      state.sourceMessage.value = `已生成 ${nextResult.startDate} 到 ${nextResult.endDate} 的历史模拟结果`
    } catch (error: unknown) {
      state.sourceError.value = toPortfolioUserError(error, '组合历史模拟失败')
    } finally {
      state.simulationLoading.value = false
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
    runSimulation,
  }
}
