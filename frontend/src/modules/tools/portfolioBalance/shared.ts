import type { PortfolioReviewFrequency } from './contracts'
import { USD_EQUIVALENT_SYMBOLS } from '@/modules/market/baseSymbolCatalog'
import { addDaysToLocalIsoDate, localIsoDateDaysAgo, parseLocalIsoDate, todayLocalIsoDate, toLocalIsoDate } from '@/utils/localDate'

export const PERCENT_BASE = 100
export const DEFAULT_REVIEW_FREQUENCY: PortfolioReviewFrequency = 'weekly'
export const PORTFOLIO_SYNTHETIC_PRICE_BY_SYMBOL: Record<string, number> = Object.fromEntries(
  USD_EQUIVALENT_SYMBOLS.map((symbol) => [symbol, 1])
)

export const round = (value: number, digits = 2) => {
  const base = 10 ** digits
  return Math.round((value + Number.EPSILON) * base) / base
}

export const clamp = (value: number, min: number, max: number) => Math.min(max, Math.max(min, value))

export const sanitizeNumber = (value: unknown, fallback = 0) => {
  const candidate = typeof value === 'number' && Number.isFinite(value) ? value : fallback
  return candidate >= 0 ? candidate : fallback
}

export const daysAgoIso = localIsoDateDaysAgo

export const todayIso = todayLocalIsoDate

export const parseIsoDate = (value: string) => {
  return parseLocalIsoDate(value)
}

export const shiftReviewDate = (dateText: string, frequency: PortfolioReviewFrequency) => {
  const source = parseIsoDate(dateText)
  if (!source) return todayIso()

  if (frequency === 'daily') return addDaysToLocalIsoDate(dateText, 1)
  if (frequency === 'weekly') return addDaysToLocalIsoDate(dateText, 7)
  const next = new Date(source)
  next.setMonth(next.getMonth() + (frequency === 'monthly' ? 1 : 3))
  return toLocalIsoDate(next)
}

export const diffDaysFromToday = (dateText: string) => {
  const target = parseIsoDate(dateText)
  if (!target) return 0
  const today = new Date()
  const current = new Date(today.getFullYear(), today.getMonth(), today.getDate())
  return Math.ceil((target.getTime() - current.getTime()) / 86400000)
}
