import { computed, onBeforeUnmount, reactive, ref, watch } from 'vue'

import { bindPageSnapshot, createPageSnapshot, PAGE_SNAPSHOT_KEYS } from '@/composables/pageSnapshot'
import { backtestApi } from '@/modules/backtest'
import type { BacktestRun, PortfolioBacktestSummary, PortfolioBalancePortfolio } from '@/types'

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
  createDefaultPortfolioCollection,
  createPortfolioBalanceAsset,
  createPortfolioBalancePortfolio,
  normalizePortfolioAssetSymbol,
  normalizePortfolioBalancePortfolio,
  readPortfolioSyntheticPrice,
} from './model'
import { computePortfolioBalancePlan } from './plan'
import {
  createDefaultPortfolioBalanceSnapshot,
  hasActiveAssets,
  hasMarketGap,
  normalizePortfolioBalanceSnapshot,
  touchPortfolio,
} from './snapshot'

export function usePortfolioBalancePage() {
  const pageSnapshot = createPageSnapshot(
    PAGE_SNAPSHOT_KEYS.portfolioBalance,
    normalizePortfolioBalanceSnapshot,
    createDefaultPortfolioBalanceSnapshot(),
  )
  const restoredSnapshot = pageSnapshot.load()
  const fallbackPortfolio = createPortfolioBalancePortfolio()

  const portfolios = reactive(restoredSnapshot.portfolios)
  const activePortfolioId = ref(restoredSnapshot.activePortfolioId || portfolios[0]?.id || '')
  const importLoading = ref(false)
  const marketLoading = ref(false)
  const backtestLoading = ref(false)
  const sourceMessage = ref('')
  const sourceError = ref('')
  const lastImportedRun = ref<BacktestRun | null>(null)

  const activePortfolio = computed(() => portfolios.find((portfolio) => portfolio.id === activePortfolioId.value) || portfolios[0] || null)
  const assets = computed(() => activePortfolio.value?.assets || [])
  const strategy = computed(() => activePortfolio.value?.strategy || fallbackPortfolio.strategy)
  const tracking = computed(() => activePortfolio.value?.tracking || fallbackPortfolio.tracking)
  const backtest = computed(() => activePortfolio.value?.backtest || fallbackPortfolio.backtest)
  const backtestResult = computed<PortfolioBacktestSummary | null>(() => activePortfolio.value?.lastBacktestResult || null)
  const plan = computed(() => computePortfolioBalancePlan(assets.value, strategy.value, tracking.value))
  const canRemoveAsset = computed(() => assets.value.length > 2)

  let marketRefreshTimer: ReturnType<typeof setTimeout> | null = null

  const clearScheduledMarketRefresh = () => {
    if (!marketRefreshTimer) return
    clearTimeout(marketRefreshTimer)
    marketRefreshTimer = null
  }

  const resetFeedback = () => {
    sourceMessage.value = ''
    sourceError.value = ''
  }

  const updateActivePortfolio = (updater: (portfolio: PortfolioBalancePortfolio) => void) => {
    const portfolio = activePortfolio.value
    if (!portfolio) return
    updater(portfolio)
    touchPortfolio(portfolio)
  }

  const refreshMarketPrices = async () => {
    const portfolio = activePortfolio.value
    if (!portfolio) return

    marketLoading.value = true
    resetFeedback()
    try {
      const { priceBySymbol, successCount, failedSymbols } = await fetchPortfolioPriceMap(portfolio)
      const needsSeed = (
        portfolio.holdingsSource !== 'paper'
        && (
          !portfolio.holdingsInitializedAt
          || portfolio.seedCapital !== portfolio.tracking.virtualCapital
          || portfolio.assets.some((asset) => normalizePortfolioAssetSymbol(asset.symbol) && asset.units <= 0)
        )
      )

      if (needsSeed) {
        seedPortfolioHoldingsFromMarket(portfolio, priceBySymbol)
        sourceMessage.value = failedSymbols.length
          ? `已初始化 ${successCount} 个，失败: ${failedSymbols.join(', ')}`
          : `已初始化 ${successCount} 个标的`
      } else {
        applyLatestMarketPrices(portfolio, priceBySymbol)
        sourceMessage.value = failedSymbols.length
          ? `已刷新 ${successCount} 个，失败: ${failedSymbols.join(', ')}`
          : `已刷新 ${successCount} 个标的`
      }
      touchPortfolio(portfolio)
    } catch (error: any) {
      sourceError.value = error?.message || '刷新市场价格失败'
    } finally {
      marketLoading.value = false
    }
  }

  const scheduleMarketRefresh = (delay = 600) => {
    clearScheduledMarketRefresh()
    marketRefreshTimer = setTimeout(async () => {
      marketRefreshTimer = null
      const portfolio = activePortfolio.value
      if (!portfolio || marketLoading.value) return
      if (!portfolio.assets.some((asset) => normalizePortfolioAssetSymbol(asset.symbol))) return
      await refreshMarketPrices()
    }, delay)
  }

  const selectPortfolio = (portfolioId: string) => {
    activePortfolioId.value = portfolioId
    resetFeedback()
  }

  const createPortfolio = () => {
    const nextPortfolio = createPortfolioBalancePortfolio({
      name: `组合 ${portfolios.length + 1}`,
    })
    portfolios.unshift(nextPortfolio)
    activePortfolioId.value = nextPortfolio.id
    sourceMessage.value = '已创建新组合'
    sourceError.value = ''
  }

  const deletePortfolio = (portfolioId: string) => {
    const index = portfolios.findIndex((portfolio) => portfolio.id === portfolioId)
    if (index < 0) return

    portfolios.splice(index, 1)
    if (!portfolios.length) {
      const fallback = createDefaultPortfolioCollection()[0]
      portfolios.push(fallback)
      activePortfolioId.value = fallback.id
    } else if (activePortfolioId.value === portfolioId) {
      activePortfolioId.value = portfolios[0].id
    }

    sourceMessage.value = '组合已删除'
    sourceError.value = ''
  }

  const addAsset = () => updateActivePortfolio((portfolio) => {
    portfolio.assets.push(createPortfolioBalanceAsset())
  })

  const removeAsset = (assetId: string) => updateActivePortfolio((portfolio) => {
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
    updateActivePortfolio((portfolio) => {
      const asset = portfolio.assets.find((item) => item.id === assetId)
      if (!asset) return

      const previousSymbol = normalizePortfolioAssetSymbol(asset.symbol)
      const nextSymbol = normalizePortfolioAssetSymbol(rawValue)
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
    resetFeedback()
    scheduleMarketRefresh()
  }

  const updateAssetTargetWeight = (assetId: string, rawValue: string | number) => updateActivePortfolio((portfolio) => {
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
    importLoading.value = true
    resetFeedback()
    try {
      const response = await backtestApi.listPaperRuns()
      const targetRun = selectLatestPaperRunForPortfolio(response.data || [])
      if (!targetRun) throw new Error('没有找到可导入的模拟盘持仓')

      const importedAssets = buildPortfolioAssetsFromPaperRun(targetRun)
      if (!importedAssets.length) throw new Error('最近的模拟盘记录里没有持仓')

      updateActivePortfolio((portfolio) => {
        const previousWeightBySymbol = new Map(
          portfolio.assets.map((asset) => [normalizePortfolioAssetSymbol(asset.symbol), Number(asset.targetWeight) || 0]),
        )
        const importedTotalValue = readPaperRunTotalValue(targetRun)
        const nextAssets = importedAssets.map((asset) => ({
          ...asset,
          targetWeight: previousWeightBySymbol.get(normalizePortfolioAssetSymbol(asset.symbol)) || 0,
          seedValue: importedTotalValue > 0 ? Number((asset.units * asset.currentPrice).toFixed(2)) : 0,
        }))

        portfolio.assets.splice(0, portfolio.assets.length, ...nextAssets)
        portfolio.holdingsInitializedAt = new Date().toISOString()
        portfolio.lastPriceUpdatedAt = new Date().toISOString()
        portfolio.seedCapital = importedTotalValue + readPaperRunCashBalance(targetRun)
        portfolio.holdingsSource = 'paper'
        portfolio.tracking.virtualCapital = portfolio.seedCapital
        portfolio.backtest.initialCapital = portfolio.seedCapital
        portfolio.tracking.inceptionDate = new Date().toISOString().slice(0, 10)
      })

      lastImportedRun.value = targetRun
      sourceMessage.value = `已导入模拟盘 #${targetRun.id}`
    } catch (error: any) {
      sourceError.value = error?.message || '导入模拟盘持仓失败'
    } finally {
      importLoading.value = false
    }
  }

  const runBacktest = async () => {
    const portfolio = activePortfolio.value
    if (!portfolio) return

    backtestLoading.value = true
    resetFeedback()
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

      updateActivePortfolio((currentPortfolio) => {
        currentPortfolio.lastBacktestResult = nextResult
      })
      sourceMessage.value = `已生成 ${nextResult.startDate} 到 ${nextResult.endDate} 的回测结果`
    } catch (error: any) {
      sourceError.value = error?.message || '组合回测失败'
    } finally {
      backtestLoading.value = false
    }
  }

  bindPageSnapshot(
    [portfolios, activePortfolioId],
    () => ({
      activePortfolioId: activePortfolioId.value,
      portfolios: portfolios.map((portfolio) => normalizePortfolioBalancePortfolio(portfolio)),
    }),
    pageSnapshot.save,
  )

  watch(assets, () => {
    updateActivePortfolio((portfolio) => {
      if (!portfolio.lastBacktestResult) return
      portfolio.lastBacktestResult = null
    })
  }, { deep: true })

  watch([strategy, tracking, backtest], () => {
    const portfolio = activePortfolio.value
    if (!portfolio || !portfolio.lastBacktestResult) return
    portfolio.lastBacktestResult = null
    touchPortfolio(portfolio)
  }, { deep: true })

  watch(() => tracking.value.virtualCapital, () => {
    const portfolio = activePortfolio.value
    if (!portfolio || portfolio.holdingsSource === 'paper' || !hasActiveAssets(portfolio)) return

    updateActivePortfolio((currentPortfolio) => {
      clearPortfolioHoldings(currentPortfolio, 'virtual')
    })
    scheduleMarketRefresh()
  })

  watch(activePortfolioId, async () => {
    clearScheduledMarketRefresh()
    const portfolio = activePortfolio.value
    if (!portfolio) return
    if (!portfolio.assets.some((asset) => normalizePortfolioAssetSymbol(asset.symbol))) return
    if (!hasMarketGap(portfolio)) return
    await refreshMarketPrices()
  }, { immediate: true })

  onBeforeUnmount(() => {
    clearScheduledMarketRefresh()
  })

  return {
    portfolios,
    activePortfolioId,
    activePortfolio,
    assets,
    strategy,
    tracking,
    backtest,
    plan,
    canRemoveAsset,
    importLoading,
    marketLoading,
    backtestLoading,
    sourceMessage,
    sourceError,
    lastImportedRun,
    backtestResult,
    selectPortfolio,
    createPortfolio,
    deletePortfolio,
    addAsset,
    removeAsset,
    updateAssetSymbol,
    updateAssetTargetWeight,
    importLatestPaperHoldings,
    refreshMarketPrices,
    runBacktest,
  }
}
