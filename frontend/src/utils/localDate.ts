const padDatePart = (value: number) => String(value).padStart(2, '0')

// 日期输入按用户本地日历解释，不能用 toISOString() 走 UTC 后再截断。
export const toLocalIsoDate = (date: Date) => (
  `${date.getFullYear()}-${padDatePart(date.getMonth() + 1)}-${padDatePart(date.getDate())}`
)

export const todayLocalIsoDate = () => toLocalIsoDate(new Date())

export const localIsoDateDaysAgo = (days: number) => {
  const date = new Date()
  date.setDate(date.getDate() - days)
  return toLocalIsoDate(date)
}

export const addDaysToLocalIsoDate = (value: string, days: number) => {
  const [year, month, day] = value.split('-').map((part) => Number(part))
  if (!Number.isInteger(year) || !Number.isInteger(month) || !Number.isInteger(day)) return value
  const date = new Date(year, month - 1, day)
  date.setDate(date.getDate() + days)
  return toLocalIsoDate(date)
}

export const parseLocalIsoDate = (value: string) => {
  const [year, month, day] = value.split('-').map((part) => Number(part))
  if (!Number.isInteger(year) || !Number.isInteger(month) || !Number.isInteger(day)) return null
  const date = new Date(year, month - 1, day)
  return Number.isNaN(date.getTime()) ? null : date
}

export const diffLocalIsoDateDays = (start: string, end: string) => {
  const startDate = parseLocalIsoDate(start)
  const endDate = parseLocalIsoDate(end)
  if (!startDate || !endDate) return 0
  return Math.round((endDate.getTime() - startDate.getTime()) / 86400000)
}
