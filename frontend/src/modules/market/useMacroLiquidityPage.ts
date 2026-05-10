import { computed, ref } from 'vue'
import { marketApi } from './api'
import type { MarketIndicatorResponse } from './contracts'

export type MacroGroupId = 'policy' | 'rates' | 'risk' | 'money'
export type MacroPolarity = 'higherSupports' | 'lowerSupports'

export interface MacroIndicatorDefinition {
  id: string
  label: string
  shortLabel: string
  group: MacroGroupId
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
}

const MACRO_INDICATORS: MacroIndicatorDefinition[] = [
  { id: 'FED_BALANCE', label: '美联储资产负债表', shortLabel: 'Fed Balance', group: 'policy', polarity: 'higherSupports', description: '联储资产端扩张通常代表基础流动性改善。' },
  { id: 'TGA', label: '美国财政部现金账户', shortLabel: 'TGA', group: 'policy', polarity: 'lowerSupports', description: 'TGA 上升会从银行体系抽走准备金，下降则释放流动性。' },
  { id: 'ONRRP', label: '隔夜逆回购', shortLabel: 'ON RRP', group: 'policy', polarity: 'lowerSupports', description: 'ON RRP 余额下降代表闲置现金回流市场体系。' },
  { id: 'FED_RATE', label: '联邦基金利率', shortLabel: 'Fed Funds', group: 'rates', polarity: 'lowerSupports', description: '政策利率越高，风险资产折现和融资压力越强。' },
  { id: 'SOFR', label: 'SOFR 隔夜融资利率', shortLabel: 'SOFR', group: 'rates', polarity: 'lowerSupports', description: '美元短端融资成本，快速上行通常压制风险偏好。' },
  { id: 'US10Y', label: '美国 10 年期国债收益率', shortLabel: '10Y Yield', group: 'rates', polarity: 'lowerSupports', description: '长端无风险收益率，影响估值锚和美元资产吸引力。' },
  { id: 'US02Y', label: '美国 2 年期国债收益率', shortLabel: '2Y Yield', group: 'rates', polarity: 'lowerSupports', description: '更贴近政策路径预期的短中端收益率。' },
  { id: 'HY_SPREAD', label: '高收益债利差', shortLabel: 'HY Spread', group: 'rates', polarity: 'lowerSupports', description: '信用风险溢价，扩张时代表风险融资环境转差。' },
  { id: 'NASDAQ', label: '纳斯达克综合指数', shortLabel: 'NASDAQ', group: 'risk', polarity: 'higherSupports', description: '高久期成长资产的风险偏好代理。' },
  { id: 'VIX', label: 'VIX 波动率指数', shortLabel: 'VIX', group: 'risk', polarity: 'lowerSupports', description: '美股隐含波动率，越高代表避险需求越强。' },
  { id: 'DXY', label: '贸易加权美元指数', shortLabel: 'Dollar', group: 'risk', polarity: 'lowerSupports', description: '美元强势通常压制全球美元流动性和风险资产。' },
  { id: 'WTI', label: 'WTI 原油价格', shortLabel: 'WTI Oil', group: 'risk', polarity: 'lowerSupports', description: '能源价格上行会推升通胀约束和政策压力。' },
  { id: 'GOLD', label: '黄金现货价格', shortLabel: 'Gold', group: 'risk', polarity: 'higherSupports', description: '真实利率和避险需求的综合映射。' },
  { id: 'M2', label: '美国 M2 货币供应', shortLabel: 'M2', group: 'money', polarity: 'higherSupports', description: '广义货币环境，扩张时更利于风险资产估值。' },
]

const GROUP_TITLES: Record<MacroGroupId, string> = {
  policy: '政策与流动性池',
  rates: '融资压力',
  risk: '市场定价',
  money: '货币供给',
}

const GROUP_DESCRIPTIONS: Record<MacroGroupId, string> = {
  policy: 'Fed 资产负债表、TGA 和 ON RRP 是美元流动性的核心水位。',
  rates: '政策利率、收益率和信用利差决定融资成本和风险补偿。',
  risk: '股指、波动率、美元和商品价格反映市场正在如何定价宏观环境。',
  money: 'M2 用来观察更慢变量的货币周期背景。',
}

const MACRO_SCORE_IDS = ['FED_BALANCE', 'TGA', 'ONRRP', 'FED_RATE', 'SOFR', 'US10Y', 'HY_SPREAD', 'NASDAQ', 'VIX', 'DXY', 'M2']
const HERO_IDS = ['FED_BALANCE', 'TGA', 'ONRRP', 'FED_RATE', 'US10Y', 'DXY', 'VIX', 'M2']

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

const rangeScore = (indicator: MarketIndicatorResponse | null, polarity: MacroPolarity) => {
  const values = historyValues(indicator)
  const current = latestValue(indicator)
  if (values.length < 3 || current === null) return null
  const min = Math.min(...values)
  const max = Math.max(...values)
  if (max === min) return 50
  const percentile = ((current - min) / (max - min)) * 100
  return polarity === 'higherSupports' ? percentile : 100 - percentile
}

const formatDateLabel = (value: string | null | undefined) => {
  const time = toDate(value)
  if (!time) return '未更新'
  return new Intl.DateTimeFormat('zh-CN', { month: '2-digit', day: '2-digit' }).format(new Date(time))
}

const formatSigned = (value: number | null, digits = 2) => {
  if (value === null) return '--'
  const sign = value > 0 ? '+' : ''
  return `${sign}${value.toFixed(digits)}%`
}

const formatCompact = (value: number) => (
  new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 2 }).format(value)
)

export const formatMacroValue = (indicator: MarketIndicatorResponse | null) => {
  const value = latestValue(indicator)
  if (value === null) return '--'
  switch (indicator?.indicator_id) {
    case 'FED_BALANCE':
      return `$${(value / 1_000_000).toFixed(2)}T`
    case 'TGA':
      return `$${(value / 1_000).toFixed(1)}B`
    case 'ONRRP':
      return `$${value.toFixed(1)}B`
    case 'M2':
      return `$${(value / 1_000).toFixed(2)}T`
    case 'GOLD':
    case 'WTI':
      return `$${value.toLocaleString('en-US', { maximumFractionDigits: 2 })}`
    case 'NASDAQ':
    case 'DXY':
    case 'VIX':
      return value.toLocaleString('en-US', { maximumFractionDigits: 2 })
    case 'FED_RATE':
    case 'SOFR':
    case 'US10Y':
    case 'US02Y':
    case 'HY_SPREAD':
      return `${value.toFixed(2)}%`
    default:
      return indicator?.unit ? `${formatCompact(value)} ${indicator.unit}` : formatCompact(value)
  }
}

const metricTone = (definition: MacroIndicatorDefinition, change: number | null): MacroMetricCard['tone'] => {
  if (change === null || Math.abs(change) < 0.01) return 'neutral'
  const supportive = definition.polarity === 'higherSupports' ? change > 0 : change < 0
  return supportive ? 'support' : 'pressure'
}

export function useMacroLiquidityPage(days = 365) {
  const indicators = ref<MarketIndicatorResponse[]>([])
  const loading = ref(true)
  const error = ref('')

  const load = async () => {
    loading.value = true
    error.value = ''
    try {
      const res = await marketApi.getIndicators({ category: 'Macro', days })
      indicators.value = res?.data || []
    } catch (e) {
      console.error('Failed to fetch macro indicators:', e)
      error.value = '宏观数据加载失败'
      indicators.value = []
    } finally {
      loading.value = false
    }
  }

  const indicatorMap = computed(() => new Map(indicators.value.map((item) => [item.indicator_id, item])))

  const cards = computed<MacroMetricCard[]>(() => MACRO_INDICATORS.map((definition) => {
    const indicator = indicatorMap.value.get(definition.id) || null
    const change = changePercent(indicator)
    return {
      definition,
      indicator,
      valueLabel: formatMacroValue(indicator),
      changeLabel: formatSigned(change),
      changeValue: change,
      tone: metricTone(definition, change),
      freshness: formatDateLabel(indicator?.last_updated),
    }
  }))

  const score = computed(() => {
    const values = MACRO_SCORE_IDS
      .map((id) => {
        const definition = MACRO_INDICATORS.find((item) => item.id === id)
        return definition ? rangeScore(indicatorMap.value.get(id) || null, definition.polarity) : null
      })
      .filter((value): value is number => typeof value === 'number' && Number.isFinite(value))
    if (!values.length) return null
    return Math.round(values.reduce((total, value) => total + value, 0) / values.length)
  })

  const scoreLabel = computed(() => {
    if (score.value === null) return '等待数据'
    if (score.value >= 68) return '流动性宽松'
    if (score.value >= 43) return '中性偏松'
    return '流动性收紧'
  })

  const scoreTone = computed(() => {
    if (score.value === null) return 'neutral'
    if (score.value >= 68) return 'support'
    if (score.value >= 43) return 'neutral'
    return 'pressure'
  })

  const heroCards = computed(() => cards.value.filter((card) => HERO_IDS.includes(card.definition.id)))

  const groups = computed(() => (Object.keys(GROUP_TITLES) as MacroGroupId[]).map((group) => ({
    id: group,
    title: GROUP_TITLES[group],
    description: GROUP_DESCRIPTIONS[group],
    cards: cards.value.filter((card) => card.definition.group === group),
  })).filter((group) => group.cards.length > 0))

  const drivers = computed(() => cards.value
    .filter((card) => MACRO_SCORE_IDS.includes(card.definition.id))
    .map((card) => {
      const rawScore = rangeScore(card.indicator, card.definition.polarity)
      const driverScore = rawScore ?? 50
      return {
        ...card,
        score: Math.round(driverScore),
        pressure: Math.round(100 - driverScore),
      }
    })
    .sort((left, right) => Math.abs(right.score - 50) - Math.abs(left.score - 50)))

  const alerts = computed(() => {
    const items = drivers.value.slice(0, 4)
    if (!items.length) return ['等待后台采集宏观指标后生成评分。']
    return items.map((item) => {
      const direction = item.score >= 50 ? '支撑' : '压制'
      return `${item.definition.shortLabel} 当前对风险资产形成${direction}，30 日变化 ${item.changeLabel}。`
    })
  })

  const lastUpdated = computed(() => {
    const latest = indicators.value
      .map((item) => toDate(item.last_updated))
      .filter((value): value is number => typeof value === 'number')
      .sort((left, right) => right - left)[0]
    if (!latest) return '未更新'
    return new Intl.DateTimeFormat('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    }).format(new Date(latest))
  })

  return {
    indicators,
    loading,
    error,
    cards,
    score,
    scoreLabel,
    scoreTone,
    heroCards,
    groups,
    drivers,
    alerts,
    lastUpdated,
    load,
  }
}
