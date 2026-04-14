import { useMoney } from '@/composables/useMoney'
import { useDateTime } from '@/composables/useDateTime'

const money = useMoney()
const dateTime = useDateTime()

export const asNumber = (value: unknown) => {
  const numeric = Number(value)
  return Number.isFinite(numeric) ? numeric : null
}

export const formatMetric = (value: unknown) => {
  const numeric = asNumber(value)
  return numeric === null ? '-' : numeric.toFixed(2)
}

export const formatPercent = (value: unknown) => {
  const numeric = asNumber(value)
  return numeric === null ? '-' : `${numeric.toFixed(2)}%`
}

export const formatMoney = (value: unknown) => {
  const numeric = asNumber(value)
  return numeric === null ? '-' : money.formatMoney(numeric, 'USDT', { maximumFractionDigits: 2 })
}

export const formatPrice = (value: unknown) => {
  const numeric = asNumber(value)
  return numeric === null ? '-' : money.formatMoney(numeric, 'USDT', { maximumFractionDigits: 4 })
}

export const formatNumber = (value: unknown) => {
  const numeric = asNumber(value)
  return numeric === null ? '-' : numeric.toLocaleString()
}

export const formatDateTime = (value: string | null | undefined) => (value ? dateTime.formatDateTime(value, { hour12: false }) : '-')

export const formatDuration = (minutes: unknown) => {
  const numeric = asNumber(minutes)
  if (numeric === null) return '-'
  const hours = Math.floor(numeric / 60)
  const rest = Math.round(numeric % 60)
  return hours > 0 ? `${hours}h ${rest}m` : `${rest}m`
}

export const formatRange = (value: { start?: string; end?: string } | null | undefined) => {
  if (!value?.start || !value?.end) return '-'
  return dateTime.formatDateRange(value)
}
