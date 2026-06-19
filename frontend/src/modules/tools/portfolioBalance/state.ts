import { computed, reactive, ref } from 'vue'

import { createPersistentPageSnapshot, PAGE_SNAPSHOT_KEYS } from '@/composables/pageSnapshot'
import type { PortfolioSimulationSummary, PortfolioBalancePortfolio } from './types'

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
  const marketLoading = ref(false)
  const simulationLoading = ref(false)
  const sourceMessage = ref('')
  const sourceError = ref('')

  const activePortfolio = computed(() => portfolios.find((portfolio) => portfolio.id === activePortfolioId.value) || portfolios[0] || null)
  const assets = computed(() => activePortfolio.value?.assets || [])
  const strategy = computed(() => activePortfolio.value?.strategy || fallbackPortfolio.strategy)
  const tracking = computed(() => activePortfolio.value?.tracking || fallbackPortfolio.tracking)
  const simulation = computed(() => activePortfolio.value?.simulation || fallbackPortfolio.simulation)
  const simulationResult = computed<PortfolioSimulationSummary | null>(() => activePortfolio.value?.lastSimulationResult || null)
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
    marketLoading,
    simulationLoading,
    sourceMessage,
    sourceError,
    activePortfolio,
    assets,
    strategy,
    tracking,
    simulation,
    simulationResult,
    plan,
    canRemoveAsset,
    resetFeedback,
    updateActivePortfolio,
    bindSnapshot,
  }
}

export type PortfolioBalancePageState = ReturnType<typeof createPortfolioBalancePageState>
