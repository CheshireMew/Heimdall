import { useUserPreferences } from './useUserPreferences'

type DateInput = string | number | Date | null | undefined

const isDateOnly = (value: DateInput) => typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value)

const parseDateInput = (value: DateInput) => {
  if (value === null || value === undefined || value === '') return null
  if (value instanceof Date) return Number.isNaN(value.getTime()) ? null : value
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
}

export function useDateTime() {
  const { timezone } = useUserPreferences()

  const formatDateTime = (
    value: DateInput,
    options: Intl.DateTimeFormatOptions = {},
  ) => {
    const date = parseDateInput(value)
    if (!date) return '--'
    return date.toLocaleString(undefined, {
      timeZone: timezone.value,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      ...options,
    })
  }

  const formatDate = (
    value: DateInput,
    options: Intl.DateTimeFormatOptions = {},
  ) => {
    if (isDateOnly(value)) return String(value)
    const date = parseDateInput(value)
    if (!date) return '--'
    return date.toLocaleDateString(undefined, {
      timeZone: timezone.value,
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      ...options,
    })
  }

  const formatDateRange = (
    value: { start?: string; end?: string } | null | undefined,
  ) => {
    if (!value?.start || !value?.end) return '--'
    return `${formatDate(value.start)} ~ ${formatDate(value.end)}`
  }

  return {
    timezone,
    formatDate,
    formatDateTime,
    formatDateRange,
  }
}
