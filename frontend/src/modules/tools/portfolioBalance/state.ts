import { computed, reactive, ref } from 'vue'

import { createPersistentPageSnapshot, PAGE_SNAPSHOT_KEYS } from '@/composables/pageSnapshot'
import type { BacktestRunResponse } from '@/modules/backtest/contracts'
import type { PortfolioBacktestSummary, PortfolioBalancePortfolio } from './types'

import { computePortfolioBalancePlan } from './plan'
import {
  buildPortfolioBalanceSnapshot,
  createDefaultPortfolioBalanceSnapshot,
  createPortfolioBalancePortfolio,
  normalizePortfolioBalancePortfolio,
  normalizePortfolioBalanceSnapshot,
  touchPortfolio,
} from './snapshot'

export const createPortfolioBalancePageState = () => {
  const pageSnapshot = createPersistentPageSnapshot(
    PAGE_SNAPSHOT_KEYS.portfolioBalance,
    normalizePortfolioBalanceSnapshot,
    createDefaultPortfolioBalanceSnapshot(),
  )
  const restoredSnapshot = pageSnapshot.initial
  const fallbackPortfolio = createPortfolioBalancePortfolio()

  const portfolios = reactive(restoredSnapshot.portfolios) as PortfolioBalancePortfolio[]
  const activePortfolioId = ref(restoredSnapshot.activePortfolioId || portfolios[0]?.id || '')
  const importLoading = ref(false)
  const marketLoading = ref(false)
  const backtestLoading = ref(false)
  const sourceMessage = ref('')
  const sourceError = ref('')
  const lastImportedRun = ref<BacktestRunResponse | null>(null)

  const activePortfolio = computed(() => portfolios.find((portfolio) => portfolio.id === activePortfolioId.value) || portfolios[0] || null)
  const assets = computed(() => activePortfolio.value?.assets || [])
  const strategy = computed(() => activePortfolio.value?.strategy || fallbackPortfolio.strategy)
  const tracking = computed(() => activePortfolio.value?.tracking || fallbackPortfolio.tracking)
  const backtest = computed(() => activePortfolio.value?.backtest || fallbackPortfolio.backtest)
  const backtestResult = computed<PortfolioBacktestSummary | null>(() => activePortfolio.value?.lastBacktestResult || null)
  const plan = computed(() => computePortfolioBalancePlan(assets.value, strategy.value, tracking.value))
  const canRemoveAsset = computed(() => assets.value.length > 2)

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

  const bindSnapshot = () => {
    pageSnapshot.bind(
      [portfolios, activePortfolioId],
      () => buildPortfolioBalanceSnapshot({
        activePortfolioId: activePortfolioId.value,
        portfolios: portfolios.map((portfolio) => normalizePortfolioBalancePortfolio(portfolio)),
      }),
    )
  }

  return {
    portfolios,
    activePortfolioId,
    importLoading,
    marketLoading,
    backtestLoading,
    sourceMessage,
    sourceError,
    lastImportedRun,
    activePortfolio,
    assets,
    strategy,
    tracking,
    backtest,
    backtestResult,
    plan,
    canRemoveAsset,
    resetFeedback,
    updateActivePortfolio,
    bindSnapshot,
  }
}

export type PortfolioBalancePageState = ReturnType<typeof createPortfolioBalancePageState>
