import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import { useTheme } from '@/composables/useTheme'

import { backtestApi } from './api'
import { asNumber } from './format'
import { useBacktestRuns, type BacktestRunMode } from './useBacktestRuns'


export const useBacktestDetailPage = () => {
  const { t } = useI18n()
  const { theme } = useTheme()
  const route = useRoute()
  const router = useRouter()
  let paperRefreshTimer: number | null = null

  const strategies = ref<any[]>([])
  const config = reactive({
    strategy_key: '',
    strategy_version: 1,
  })

  const isDark = computed(() => theme.value === 'dark')
  const chartColors = computed(() => ({
    bg: isDark.value ? '#1f2937' : '#ffffff',
    grid: isDark.value ? '#374151' : '#e5e7eb',
    text: isDark.value ? '#9ca3af' : '#4b5563',
    upColor: '#10b981',
    downColor: '#ef4444',
  }))

  const selectedStrategy = computed(() => strategies.value.find((item) => item.key === config.strategy_key) || null)
  const selectedStrategyVersions = computed(() => {
    const versions = selectedStrategy.value?.versions
    if (!Array.isArray(versions)) return []
    return versions.filter(Boolean)
  })

  const runs = useBacktestRuns({
    t,
    config,
    selectedStrategyVersions,
  })

  const profitColorClass = (value: unknown) => {
    const numeric = asNumber(value)
    if (numeric === null) return 'text-gray-500'
    if (numeric > 0) return 'text-green-600 dark:text-green-400'
    if (numeric < 0) return 'text-red-600 dark:text-red-400'
    return 'text-gray-500'
  }

  const fetchStrategies = async () => {
    try {
      const res = await backtestApi.listStrategies()
      strategies.value = res.data
    } catch (error) {
      console.error(error)
    }
  }

  const syncConfigFromSelectedRun = () => {
    const metadata = runs.selectedRun.value?.metadata || {}
    config.strategy_key = metadata.strategy_key || ''
    config.strategy_version = Number(metadata.strategy_version || 1)
  }

  const currentTarget = computed(() => {
    const mode = route.params.mode === 'paper' ? 'paper' : 'backtest'
    const id = Number(route.params.id)
    if (!Number.isFinite(id) || id <= 0) return null
    return { id, mode: mode as BacktestRunMode }
  })

  const loadCurrentTarget = async () => {
    const target = currentTarget.value
    if (!target) {
      runs.clearSelectedRun()
      return
    }
    const result = await runs.loadRunTarget(target)
    if (!result) return
    syncConfigFromSelectedRun()
  }

  const openRunDetail = (run: any, mode: 'backtest' | 'paper' = runs.historyMode.value) => {
    if (!run?.id) return
    const path = mode === 'paper' ? `/backtest/paper/${run.id}` : `/backtest/runs/${run.id}`
    if (router.currentRoute.value.fullPath === path) {
      loadCurrentTarget().catch((error) => console.error(error))
      return
    }
    router.push(path)
  }

  const goBackToCenter = () => {
    router.push('/backtest')
  }

  onMounted(async () => {
    await Promise.all([fetchStrategies(), runs.fetchHistory(), runs.fetchPaperHistory()])
    await loadCurrentTarget()
    paperRefreshTimer = window.setInterval(() => {
      runs.refreshPaperSelection().catch((error) => console.error(error))
    }, 10000)
  })

  watch(
    () => [route.params.mode, route.params.id],
    () => {
      loadCurrentTarget().catch((error) => console.error(error))
    },
  )

  onBeforeUnmount(() => {
    if (paperRefreshTimer !== null) {
      window.clearInterval(paperRefreshTimer)
      paperRefreshTimer = null
    }
  })

  const page = reactive({
    t,
    theme,
    strategies,
    config,
    isDark,
    chartColors,
    selectedStrategy,
    selectedStrategyVersions,
    enableHistoryCompare: true,
    profitColorClass,
    fetchStrategies,
    ...runs,
    openRunDetail,
    goBackToCenter,
  })

  return page
}


export type BacktestDetailPageState = ReturnType<typeof useBacktestDetailPage>
