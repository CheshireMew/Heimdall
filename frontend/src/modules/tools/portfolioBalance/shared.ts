import type { PortfolioReviewFrequency } from '@/types'

export const PERCENT_BASE = 100
export const DEFAULT_REVIEW_FREQUENCY: PortfolioReviewFrequency = 'weekly'
export const PORTFOLIO_SYNTHETIC_PRICE_BY_SYMBOL: Record<string, number> = {
  USD: 1,
  USDT: 1,
  USDC: 1,
  FDUSD: 1,
  BUSD: 1,
  DAI: 1,
  TUSD: 1,
  USDP: 1,
  PYUSD: 1,
  USDS: 1,
}

export const round = (value: number, digits = 2) => {
  const base = 10 ** digits
  return Math.round((value + Number.EPSILON) * base) / base
}

export const clamp = (value: number, min: number, max: number) => Math.min(max, Math.max(min, value))

export const sanitizeNumber = (value: unknown, fallback = 0) => {
  const candidate = typeof value === 'number' && Number.isFinite(value) ? value : fallback
  return candidate >= 0 ? candidate : fallback
}

export const formatIsoDate = (value: Date) => {
  const year = value.getFullYear()
  const month = `${value.getMonth() + 1}`.padStart(2, '0')
  const day = `${value.getDate()}`.padStart(2, '0')
  return `${year}-${month}-${day}`
}

export const daysAgoIso = (days: number) => {
  const date = new Date()
  date.setDate(date.getDate() - days)
  return formatIsoDate(date)
}

export const todayIso = () => formatIsoDate(new Date())

export const parseIsoDate = (value: string) => {
  const date = new Date(`${value}T00:00:00`)
  return Number.isNaN(date.getTime()) ? null : date
}

export const shiftReviewDate = (dateText: string, frequency: PortfolioReviewFrequency) => {
  const source = parseIsoDate(dateText)
  if (!source) return todayIso()

  const next = new Date(source)
  if (frequency === 'daily') next.setDate(next.getDate() + 1)
  else if (frequency === 'weekly') next.setDate(next.getDate() + 7)
  else if (frequency === 'monthly') next.setMonth(next.getMonth() + 1)
  else next.setMonth(next.getMonth() + 3)
  return formatIsoDate(next)
}

export const diffDaysFromToday = (dateText: string) => {
  const target = parseIsoDate(dateText)
  if (!target) return 0
  const today = new Date()
  const current = new Date(today.getFullYear(), today.getMonth(), today.getDate())
  return Math.ceil((target.getTime() - current.getTime()) / 86400000)
}
