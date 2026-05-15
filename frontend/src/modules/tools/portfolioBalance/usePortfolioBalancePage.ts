import { onBeforeUnmount, watch } from 'vue'

import { toBaseSymbol } from '@/modules/market'

import { createPortfolioBalancePageCommands } from './commands'
import { createPortfolioBalancePageState } from './state'
import { clearPortfolioHoldings } from './holdings'
import { hasActiveAssets, hasMarketGap } from './snapshot'

export function usePortfolioBalancePage() {
  const state = createPortfolioBalancePageState()
  const commands = createPortfolioBalancePageCommands(state)

  state.bindSnapshot()

  watch(state.assets, () => {
    state.updateActivePortfolio((portfolio) => {
      if (!portfolio.lastBacktestResult) return
      portfolio.lastBacktestResult = null
    })
  }, { deep: true })

  watch([state.strategy, state.tracking, state.backtest], () => {
    const portfolio = state.activePortfolio.value
    if (!portfolio || !portfolio.lastBacktestResult) return
    portfolio.lastBacktestResult = null
  }, { deep: true })

  watch(() => state.tracking.value.virtualCapital, () => {
    const portfolio = state.activePortfolio.value
    if (!portfolio || portfolio.holdingsSource === 'paper' || !hasActiveAssets(portfolio)) return

    state.updateActivePortfolio((currentPortfolio) => {
      clearPortfolioHoldings(currentPortfolio, 'virtual')
    })
    commands.scheduleMarketRefresh()
  })

  watch(state.activePortfolioId, async () => {
    commands.clearScheduledMarketRefresh()
    const portfolio = state.activePortfolio.value
    if (!portfolio) return
    if (!portfolio.assets.some((asset) => toBaseSymbol(asset.symbol))) return
    if (!hasMarketGap(portfolio)) return
    await commands.refreshMarketPrices()
  }, { immediate: true })

  onBeforeUnmount(() => {
    commands.clearScheduledMarketRefresh()
  })

  return {
    portfolios: state.portfolios,
    activePortfolioId: state.activePortfolioId,
    activePortfolio: state.activePortfolio,
    assets: state.assets,
    strategy: state.strategy,
    tracking: state.tracking,
    backtest: state.backtest,
    plan: state.plan,
    canRemoveAsset: state.canRemoveAsset,
    importLoading: state.importLoading,
    marketLoading: state.marketLoading,
    backtestLoading: state.backtestLoading,
    sourceMessage: state.sourceMessage,
    sourceError: state.sourceError,
    lastImportedRun: state.lastImportedRun,
    backtestResult: state.backtestResult,
    selectPortfolio: commands.selectPortfolio,
    createPortfolio: commands.createPortfolio,
    copyPortfolio: commands.copyPortfolio,
    deletePortfolio: commands.deletePortfolio,
    addAsset: commands.addAsset,
    removeAsset: commands.removeAsset,
    updateAssetSymbol: commands.updateAssetSymbol,
    updateAssetTargetWeight: commands.updateAssetTargetWeight,
    importLatestPaperHoldings: commands.importLatestPaperHoldings,
    refreshMarketPrices: commands.refreshMarketPrices,
    runBacktest: commands.runBacktest,
  }
}
