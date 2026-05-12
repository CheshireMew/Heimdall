import { formatCompactNumber, formatLocalizedNumber } from '@/modules/format'
import type { MarketIndicatorResponse } from './contracts'

const formatFixed = (value: number, digits = 2) => (
  value.toLocaleString(undefined, {
    maximumFractionDigits: digits,
    minimumFractionDigits: value % 1 === 0 ? 0 : Math.min(2, digits),
  })
)

const formatUsd = (value: number) => {
  const absolute = Math.abs(value)
  if (absolute >= 1_000_000_000) return `$${formatCompactNumber(value)}`
  return `$${formatLocalizedNumber(value, absolute >= 100 ? 0 : 2)}`
}

export const formatIndicatorDisplayValue = (
  indicator: Pick<MarketIndicatorResponse, 'indicator_id' | 'unit'>,
  value: number | null | undefined,
) => {
  if (typeof value !== 'number' || !Number.isFinite(value)) return '--'

  if (indicator.indicator_id === 'HASHRATE') return `${formatFixed(value, 2)} EH/s`
  if (indicator.indicator_id === 'DIFFICULTY') return `${formatFixed(value, 2)} T`

  const unit = indicator.unit || ''
  if (unit === '%') return `${formatFixed(value, 2)}%`
  if (unit === 'USD') return formatUsd(value)
  if (Math.abs(value) >= 1_000_000) return `${formatCompactNumber(value)}${unit ? ` ${unit}` : ''}`
  return `${formatLocalizedNumber(value, Math.abs(value) >= 100 ? 2 : 3)}${unit ? ` ${unit}` : ''}`
}

export const formatIndicatorAxisValue = (
  indicator: Pick<MarketIndicatorResponse, 'indicator_id' | 'unit'>,
  value: number,
) => {
  if (!Number.isFinite(value)) return ''

  if (indicator.indicator_id === 'HASHRATE') return `${formatFixed(value, 0)} EH/s`
  if (indicator.indicator_id === 'DIFFICULTY') return `${formatFixed(value, 2)} T`

  const unit = indicator.unit || ''
  if (unit === 'USD') return formatUsd(value)
  if (unit === '%') return `${formatFixed(value, 2)}%`
  if (Math.abs(value) >= 1_000_000) return `${formatCompactNumber(value)}${unit ? ` ${unit}` : ''}`
  return `${formatLocalizedNumber(value, Math.abs(value) >= 100 ? 0 : 2)}${unit ? ` ${unit}` : ''}`
}
