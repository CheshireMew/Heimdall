import { computed, unref, type Ref } from 'vue'
import { formatCompactNumber, formatSignedPercent } from '@/modules/format'
import type { DliComponentResponse, DliLiquidityResponse, MarketIndicatorResponse } from './contracts'
import { useMacroLiquidityStore } from './macroLiquidityStore'

export type MacroGroupId = 'policy' | 'funding' | 'credit' | 'risk'
export type MacroPolarity = 'higherTightens' | 'lowerTightens'

export interface MacroIndicatorDefinition {
  id: string
  label: string
  shortLabel: string
  group: MacroGroupId
  groupLabel: string
  groupDescription: string
  polarity: MacroPolarity
  description: string
}

export interface MacroMetricCard {
  definition: MacroIndicatorDefinition
  indicator: MarketIndicatorResponse | null
  valueLabel: string
  changeLabel: string
  changeValue: number | null
  tone: 'support' | 'pressure' | 'neutral'
  freshness: string
  dataLagDays: number | null
  dataLagLabel: string
}

export interface MacroDriver extends MacroMetricCard {
  score: number
  pressure: number
  contribution: number | null
  rawWeight: number
  effectiveWeight: number
  zScore: number | null
  percentile: number | null
}

const toDate = (value: string | null | undefined) => {
  if (!value) return null
  const time = new Date(value).getTime()
  return Number.isFinite(time) ? time : null
}

const latestValue = (indicator: MarketIndicatorResponse | null) => {
  if (!indicator) return null
  if (typeof indicator.current_value === 'number') return indicator.current_value
  const tail = indicator.history[indicator.history.length - 1]
  return typeof tail?.value === 'number' ? tail.value : null
}

const historyValues = (indicator: MarketIndicatorResponse | null) => (
  indicator?.history?.map((item) => item.value).filter((value): value is number => typeof value === 'number' && Number.isFinite(value)) || []
)

const changePercent = (indicator: MarketIndicatorResponse | null, lookback = 30) => {
  const values = historyValues(indicator)
  if (values.length < 2) return null
  const current = values[values.length - 1]
  const previous = values[Math.max(0, values.length - lookback - 1)]
  if (typeof current !== 'number' || typeof previous !== 'number' || previous === 0) return null
  return ((current - previous) / Math.abs(previous)) * 100
}

const formatDateLabel = (value: string | null | undefined) => {
  const time = toDate(value)
  if (!time) return '未更新'
  return new Intl.DateTimeFormat('zh-CN', { month: '2-digit', day: '2-digit' }).format(new Date(time))
}

const formatLagLabel = (value: number | null | undefined) => {
  if (typeof value !== 'number') return '滞后 --'
  if (value <= 0) return '今日更新'
  if (value === 1) return '滞后 1 天'
  return `滞后 ${value} 天`
}

export const formatMacroValue = (indicator: MarketIndicatorResponse | null) => {
  const value = latestValue(indicator)
  if (value === null) return '--'
  switch (indicator?.indicator_id) {
    case 'FED_BALANCE':
      return `$${(value / 1_000_000).toFixed(2)}T`
    case 'TGA':
      return `$${(value / 1_000).toFixed(1)}B`
    case 'ONRRP':
    case 'SRF_USAGE':
      return `$${value.toFixed(1)}B`
    case 'SOFR_IORB':
      return `${value.toFixed(1)}bp`
    case 'M2':
      return `$${(value / 1_000).toFixed(2)}T`
    case 'NET_LIQUIDITY':
      return `$${(value / 1_000_000).toFixed(2)}T`
    case 'GOLD':
    case 'WTI':
      return `$${value.toLocaleString('en-US', { maximumFractionDigits: 2 })}`
    case 'NASDAQ':
    case 'DXY':
    case 'VIX':
      return value.toLocaleString('en-US', { maximumFractionDigits: 2 })
    case 'FED_RATE':
    case 'SOFR':
    case 'US10Y_REAL':
    case 'BANK_CASH_BUFFER':
    case 'US02Y':
    case 'HY_SPREAD':
      return `${value.toFixed(2)}%`
    default:
      return indicator?.unit ? `${formatCompactNumber(value)} ${indicator.unit}` : formatCompactNumber(value)
  }
}

const metricTone = (definition: MacroIndicatorDefinition, change: number | null): MacroMetricCard['tone'] => {
  if (change === null || Math.abs(change) < 0.01) return 'neutral'
  const pressure = definition.polarity === 'higherTightens' ? change > 0 : change < 0
  return pressure ? 'pressure' : 'support'
}

const normalizePolarity = (value: string | null | undefined): MacroPolarity => (
  value === 'higher_tightens' || value === 'higherTightens' ? 'higherTightens' : 'lowerTightens'
)

const definitionFromIndicator = (indicator: MarketIndicatorResponse): MacroIndicatorDefinition => ({
  id: indicator.indicator_id,
  label: indicator.name,
  shortLabel: indicator.short_label || indicator.name,
  group: (indicator.group as MacroGroupId) || 'risk',
  groupLabel: indicator.group_label || '风险与价格',
  groupDescription: indicator.group_description || '',
  polarity: normalizePolarity(indicator.polarity),
  description: indicator.description || '',
})

const definitionFromComponent = (component: DliComponentResponse): MacroIndicatorDefinition => {
  return {
    id: component.indicator_id,
    label: component.name,
    shortLabel: component.short_label,
    group: (component.group as MacroGroupId) || 'risk',
    groupLabel: component.group_label,
    groupDescription: component.group_description || '',
    polarity: normalizePolarity(component.polarity),
    description: '',
  }
}

export function useMacroLiquidityPage(days: number | Ref<number> = 365, changeDays: number | Ref<number> = 30) {
  const macroLiquidityStore = useMacroLiquidityStore()
  const currentDays = computed(() => unref(days))
  const currentChangeDays = computed(() => unref(changeDays))
  const dli = computed<DliLiquidityResponse | null>(() => (
    macroLiquidityStore.readDliLiquidity(currentDays.value, currentChangeDays.value)
  ))
  const indicators = computed<MarketIndicatorResponse[]>(() => dli.value?.indicators || [])
  const error = computed(() => macroLiquidityStore.getDliLiquidityError(currentDays.value, currentChangeDays.value))
  const loading = computed(() => (
    macroLiquidityStore.isDliLiquidityLoading(currentDays.value, currentChangeDays.value)
    || (!dli.value && !error.value)
  ))

  const load = async (options: { force?: boolean } = {}) => {
    await macroLiquidityStore.getDliLiquidity(currentDays.value, currentChangeDays.value, options)
  }

  const refresh = async () => {
    await load({ force: true })
  }

  const indicatorMap = computed(() => new Map(indicators.value.map((item) => [item.indicator_id, item])))

  const changeWindowDays = computed(() => unref(changeDays))
  const changeWindowLabel = computed(() => `${changeWindowDays.value} 日`)

  const definitions = computed(() => indicators.value.map(definitionFromIndicator))

  const cards = computed<MacroMetricCard[]>(() => definitions.value.map((definition) => {
    const indicator = indicatorMap.value.get(definition.id) || null
    const change = changePercent(indicator, changeWindowDays.value)
    return {
      definition,
      indicator,
      valueLabel: formatMacroValue(indicator),
      changeLabel: formatSignedPercent(change),
      changeValue: change,
      tone: metricTone(definition, change),
      freshness: formatDateLabel(indicator?.last_updated),
      dataLagDays: indicator?.data_lag_days ?? null,
      dataLagLabel: formatLagLabel(indicator?.data_lag_days),
    }
  }))

  const score = computed(() => dli.value?.score ?? null)
  const rawScore = computed(() => dli.value?.raw_score ?? null)
  const scorePercentile = computed(() => dli.value?.score_percentile ?? null)
  const scoreLabel = computed(() => dli.value?.state || '等待数据')
  const scoreTone = computed(() => dli.value?.tone || 'neutral')
  const thresholds = computed(() => dli.value?.thresholds || null)

  const groups = computed(() => Array.from(new Set(cards.value.map((card) => card.definition.group))).map((group) => {
    const groupCards = cards.value.filter((card) => card.definition.group === group)
    const firstDefinition = groupCards[0]?.definition
    return {
      id: group,
      title: firstDefinition?.groupLabel || group,
      description: firstDefinition?.groupDescription || '',
      cards: groupCards,
    }
  }))

  const drivers = computed<MacroDriver[]>(() => (dli.value?.components || []).map((component) => {
    const definition = definitionFromComponent(component)
    const card = cards.value.find((item) => item.definition.id === component.indicator_id)
    const driverScore = Math.round(component.score ?? 50)
    return {
      definition,
      indicator: card?.indicator || null,
      valueLabel: card?.valueLabel || '--',
      changeLabel: typeof component.change_pct === 'number' ? formatSignedPercent(component.change_pct) : (card?.changeLabel || '--'),
      changeValue: component.change_pct ?? card?.changeValue ?? null,
      tone: driverScore >= 50 ? 'pressure' : 'support',
      freshness: card?.freshness || formatDateLabel(component.last_updated),
      dataLagDays: component.data_lag_days ?? card?.dataLagDays ?? null,
      dataLagLabel: formatLagLabel(component.data_lag_days ?? card?.dataLagDays),
      score: driverScore,
      pressure: Math.round(100 - driverScore),
      contribution: component.contribution,
      rawWeight: component.weight,
      effectiveWeight: component.effective_weight,
      zScore: component.z_score,
      percentile: component.percentile,
    }
  }))

  const alerts = computed(() => dli.value?.alerts?.length ? dli.value.alerts : ['等待后台采集宏观指标后生成评分。'])

  const lastUpdated = computed(() => {
    const time = toDate(dli.value?.updated_at)
    if (!time) return '未更新'
    return new Intl.DateTimeFormat('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    }).format(new Date(time))
  })

  return {
    dli,
    indicators,
    loading,
    error,
    cards,
    score,
    rawScore,
    scorePercentile,
    scoreLabel,
    scoreTone,
    thresholds,
    groups,
    drivers,
    alerts,
    lastUpdated,
    changeWindowDays,
    changeWindowLabel,
    load,
    refresh,
  }
}

