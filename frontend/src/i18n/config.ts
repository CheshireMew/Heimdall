export const LOCALE_STORAGE_KEY = 'locale'
export const DEFAULT_LOCALE = 'zh-CN'
export const FALLBACK_LOCALE = 'zh-CN'

export const SUPPORTED_LOCALES = ['zh-CN', 'en'] as const

export type AppLocale = (typeof SUPPORTED_LOCALES)[number]

export const LOCALE_OPTIONS: Array<{ value: AppLocale; label: string }> = [
  { value: 'zh-CN', label: '简体中文' },
  { value: 'en', label: 'English' },
]

const canUseStorage = () => typeof window !== 'undefined' && !!window.localStorage

const normalizeLocale = (value: string | null | undefined): AppLocale => (
  SUPPORTED_LOCALES.includes(value as AppLocale) ? value as AppLocale : DEFAULT_LOCALE
)

export const readStoredLocale = (): AppLocale => {
  if (!canUseStorage()) return DEFAULT_LOCALE
  return normalizeLocale(window.localStorage.getItem(LOCALE_STORAGE_KEY))
}

export const persistLocale = (value: string | null | undefined): AppLocale => {
  const locale = normalizeLocale(value)
  if (canUseStorage()) window.localStorage.setItem(LOCALE_STORAGE_KEY, locale)
  return locale
}

export const resolveInitialLocale = (): AppLocale => readStoredLocale()

export const toggleAppLocale = (value: string | null | undefined): AppLocale => (
  normalizeLocale(value) === 'zh-CN' ? 'en' : 'zh-CN'
)

export const setAppLocale = (
  localeRef: { value: string },
  value: string | null | undefined,
): AppLocale => {
  const locale = persistLocale(value)
  localeRef.value = locale
  return locale
}
