import { computed } from 'vue'
import { formatDate, formatSignedPercent } from '@/modules/format'
import { formatIndicatorDisplayValue } from './indicatorDisplay'
import type { MarketIndicatorResponse } from './contracts'
import { useMarketStore } from './store'

export type MarketSignalCategoryId = 'Onchain' | 'Sentiment' | 'Tech'
export type MarketSignalGroupId = 'cycle' | 'stablecoins' | 'mining'

export interface MarketSignalGroupDefinition {
  id: MarketSignalGroupId
  title: string
  eyebrow: string
  description: string
  accent: 'green' | 'amber' | 'blue'
  indicatorIds: string[]
}

export interface MarketSignalIndicatorCard {
  indicator: MarketIndicatorResponse
  valueLabel: string
  changeLabel: string
  changeValue: number | null
  lastUpdatedLabel: string
}

export interface MarketSignalCategoryGroup {
  definition: MarketSignalGroupDefinition
  cards: MarketSignalIndicatorCard[]
  latestUpdatedLabel: string
}

const SOURCE_CATEGORIES: MarketSignalCategoryId[] = ['Onchain', 'Sentiment', 'Tech']

const GROUP_DEFINITIONS: MarketSignalGroupDefinition[] = [
  {
    id: 'cycle',
    eyebrow: 'Cycle & Sentiment',
    title: '周期与情绪',
    description: '先看 BTC 所处周期位置和外部关注度，再判断当下是否处在拥挤或冷却阶段。',
    accent: 'blue',
    indicatorIds: ['BTC_DRAWDOWN', '200WMA', 'GOOGLE_TRENDS_BTC', 'FEAR_GREED'],
  },
  {
    id: 'stablecoins',
    eyebrow: 'Stablecoin Liquidity',
    title: '稳定币流动性',
    description: '稳定币总量和 USDC、USDT 分项放在一起，观察场内美元购买力的变化。',
    accent: 'amber',
    indicatorIds: ['STABLECOIN_CAP', 'USDC_CAP', 'USDT_CAP'],
  },
  {
    id: 'mining',
    eyebrow: 'Mining & Network',
    title: '矿工与网络',
    description: '最后看网络难度、算力和主流矿机关机价，判断生产侧成本和安全预算压力。',
    accent: 'green',
    indicatorIds: ['DIFFICULTY', 'HASHRATE', 'S19_BREAKEVEN', 'S21_BREAKEVEN', 'S23_BREAKEVEN'],
  },
]

const historyValues = (indicator: MarketIndicatorResponse) => (
  indicator.history
    .map((item) => item.value)
    .filter((value): value is number => typeof value === 'number' && Number.isFinite(value))
)

const latestValue = (indicator: MarketIndicatorResponse) => {
  if (typeof indicator.current_value === 'number') return indicator.current_value
  const values = historyValues(indicator)
  const tail = values[values.length - 1]
  return typeof tail === 'number' ? tail : null
}

const changePercent = (indicator: MarketIndicatorResponse, lookback: number) => {
  const values = historyValues(indicator)
  if (values.length < 2) return null
  const current = values[values.length - 1]
  const previous = values[Math.max(0, values.length - lookback - 1)]
  if (typeof current !== 'number' || typeof previous !== 'number' || previous === 0) return null
  return ((current - previous) / Math.abs(previous)) * 100
}

const toTime = (value: string | null | undefined) => {
  if (!value) return null
  const time = new Date(value).getTime()
  return Number.isFinite(time) ? time : null
}

const latestUpdatedLabel = (cards: MarketSignalIndicatorCard[]) => {
  const latest = cards
    .map((card) => toTime(card.indicator.last_updated))
    .filter((time): time is number => typeof time === 'number')
    .sort((left, right) => right - left)[0]
  return latest ? formatDate(new Date(latest), '未更新') : '未更新'
}

const cardFromIndicator = (indicator: MarketIndicatorResponse, changeDays: number): MarketSignalIndicatorCard => ({
  indicator,
  valueLabel: formatIndicatorDisplayValue(indicator, latestValue(indicator)),
  changeLabel: formatSignedPercent(changePercent(indicator, changeDays)),
  changeValue: changePercent(indicator, changeDays),
  lastUpdatedLabel: formatDate(indicator.last_updated, '未更新'),
})

export function useMarketSignalIndicators(days = 365, changeDays = 30) {
  const marketStore = useMarketStore()
  const indicators = computed<Record<MarketSignalCategoryId, MarketIndicatorResponse[]>>(() => ({
    Onchain: marketStore.readMarketIndicators('Onchain', days) || [],
    Sentiment: marketStore.readMarketIndicators('Sentiment', days) || [],
    Tech: marketStore.readMarketIndicators('Tech', days) || [],
  }))
  const error = computed(() => (
    SOURCE_CATEGORIES.map((category) => marketStore.getMarketIndicatorsError(category, days)).find(Boolean) || ''
  ))
  const hasLoadedAllCategories = computed(() => (
    SOURCE_CATEGORIES.every((category) => marketStore.readMarketIndicators(category, days) !== null)
  ))
  const loading = computed(() => (
    SOURCE_CATEGORIES.some((category) => marketStore.isMarketIndicatorsLoading(category, days))
    || (!hasLoadedAllCategories.value && !error.value)
  ))

  const load = async (options: { force?: boolean } = {}) => {
    await Promise.all(
      SOURCE_CATEGORIES.map((category) => marketStore.getMarketIndicators(category, days, options)),
    )
  }

  const refresh = async () => {
    await load({ force: true })
  }

  const groups = computed<MarketSignalCategoryGroup[]>(() => {
    const indicatorMap = new Map(
      SOURCE_CATEGORIES.flatMap((category) => indicators.value[category]).map((indicator) => [indicator.indicator_id, indicator]),
    )
    return GROUP_DEFINITIONS.map((definition) => {
      const cards = definition.indicatorIds
        .map((indicatorId) => indicatorMap.get(indicatorId))
        .filter((indicator): indicator is MarketIndicatorResponse => Boolean(indicator))
        .map((indicator) => cardFromIndicator(indicator, changeDays))

      return {
        definition,
        cards,
        latestUpdatedLabel: latestUpdatedLabel(cards),
      }
    })
  })

  const totalCount = computed(() => groups.value.reduce((count, group) => count + group.cards.length, 0))
  const populatedGroupCount = computed(() => groups.value.filter((group) => group.cards.length > 0).length)

  return {
    loading,
    error,
    groups,
    totalCount,
    populatedGroupCount,
    load,
    refresh,
  }
}
