import { computed, ref } from 'vue'
import request from '@/api/request'
import { useUserPreferences } from './useUserPreferences'
import type { CurrencyRatesResponse, DisplayCurrencyResponse } from '@/types'

const USD_EQUIVALENT = new Set(['USD', 'USDT', 'USDC', 'FDUSD', 'BUSD', 'DAI', 'TUSD', 'USDP', 'PYUSD', 'USDS'])

const fallbackSupported: DisplayCurrencyResponse[] = [
  { code: 'USD', name: 'US Dollar', symbol: '$', locale: 'en-US', fraction_digits: 2 },
  { code: 'CNY', name: '人民币', symbol: '¥', locale: 'zh-CN', fraction_digits: 2 },
  { code: 'EUR', name: 'Euro', symbol: '€', locale: 'de-DE', fraction_digits: 2 },
  { code: 'GBP', name: 'British Pound', symbol: '£', locale: 'en-GB', fraction_digits: 2 },
  { code: 'JPY', name: 'Japanese Yen', symbol: '¥', locale: 'ja-JP', fraction_digits: 0 },
  { code: 'HKD', name: 'Hong Kong Dollar', symbol: 'HK$', locale: 'zh-HK', fraction_digits: 2 },
  { code: 'SGD', name: 'Singapore Dollar', symbol: 'S$', locale: 'en-SG', fraction_digits: 2 },
  { code: 'AUD', name: 'Australian Dollar', symbol: 'A$', locale: 'en-AU', fraction_digits: 2 },
]

const fallbackRates: Record<string, number> = {
  USD: 1,
  CNY: 7.25,
  EUR: 0.92,
  GBP: 0.79,
  JPY: 150,
  HKD: 7.8,
  SGD: 1.35,
  AUD: 1.52,
}

const rates = ref<Record<string, number>>({ ...fallbackRates })
const supportedCurrencies = ref<DisplayCurrencyResponse[]>(fallbackSupported)
const ratesSource = ref('fallback')
const ratesUpdatedAt = ref('')
const ratesAreFallback = ref(true)
const loadingRates = ref(false)
let ratesPromise: Promise<void> | null = null

const normalizeCurrency = (value: string | null | undefined) => {
  const code = String(value || 'USD').trim().toUpperCase()
  if (USD_EQUIVALENT.has(code)) return 'USD'
  return code
}

const asNumber = (value: unknown) => {
  const numeric = Number(value)
  return Number.isFinite(numeric) ? numeric : null
}

const metaByCode = computed(() => {
  const map = new Map<string, DisplayCurrencyResponse>()
  supportedCurrencies.value.forEach((item) => map.set(item.code, item))
  return map
})

const readCurrencyMeta = (code: string) => (
  metaByCode.value.get(code) || fallbackSupported.find((item) => item.code === code) || fallbackSupported[0]
)

export const loadCurrencyRates = async () => {
  if (ratesPromise) return ratesPromise
  loadingRates.value = true
  ratesPromise = request.get<CurrencyRatesResponse>('/currencies')
    .then((response) => {
      const payload = response.data
      if (payload?.rates) rates.value = { ...fallbackRates, ...payload.rates }
      if (payload?.supported?.length) supportedCurrencies.value = payload.supported
      ratesSource.value = payload?.source || 'fallback'
      ratesUpdatedAt.value = payload?.updated_at || ''
      ratesAreFallback.value = !!payload?.is_fallback
    })
    .catch((error) => {
      console.warn('Failed to load currency rates:', error)
    })
    .finally(() => {
      loadingRates.value = false
      ratesPromise = null
    })
  return ratesPromise
}

export function useMoney() {
  const { displayCurrency, setDisplayCurrency } = useUserPreferences()

  const currencyOptions = computed(() => supportedCurrencies.value.map((item) => ({
    value: item.code,
    label: `${item.code} · ${item.name}`,
  })))

  const selectedCurrencyMeta = computed(() => readCurrencyMeta(displayCurrency.value))

  const convertMoney = (
    value: unknown,
    sourceCurrency = 'USD',
    targetCurrency = displayCurrency.value,
  ) => {
    const numeric = asNumber(value)
    if (numeric === null) return null
    const source = normalizeCurrency(sourceCurrency)
    const target = normalizeCurrency(targetCurrency)
    const sourceRate = rates.value[source] || 1
    const targetRate = rates.value[target] || 1
    return (numeric / sourceRate) * targetRate
  }

  const fromDisplayAmount = (value: unknown, targetSourceCurrency = 'USD') => (
    convertMoney(value, displayCurrency.value, targetSourceCurrency)
  )

  const toDisplayAmount = (value: unknown, sourceCurrency = 'USD') => (
    convertMoney(value, sourceCurrency, displayCurrency.value)
  )

  const formatMoney = (
    value: unknown,
    sourceCurrency = 'USD',
    options: Intl.NumberFormatOptions = {},
  ) => {
    const converted = toDisplayAmount(value, sourceCurrency)
    if (converted === null) return '--'
    const meta = selectedCurrencyMeta.value
    const absolute = Math.abs(converted)
    const usesSignificantDigits = options.maximumSignificantDigits !== undefined || options.minimumSignificantDigits !== undefined
    const maximumFractionDigits = usesSignificantDigits
      ? undefined
      : options.maximumFractionDigits ?? (absolute >= 1000 ? meta.fraction_digits : Math.max(meta.fraction_digits, 4))
    return new Intl.NumberFormat(meta.locale, {
      ...options,
      style: 'currency',
      currency: meta.code,
      minimumFractionDigits: usesSignificantDigits ? undefined : options.minimumFractionDigits ?? meta.fraction_digits,
      maximumFractionDigits,
    }).format(converted)
  }

  const formatCompactMoney = (value: unknown, sourceCurrency = 'USD') => (
    formatMoney(value, sourceCurrency, { notation: 'compact', maximumFractionDigits: 2 })
  )

  const formatSignedMoney = (value: unknown, sourceCurrency = 'USD') => {
    const numeric = asNumber(value)
    if (numeric === null) return '--'
    return `${numeric >= 0 ? '+' : '-'}${formatMoney(Math.abs(numeric), sourceCurrency)}`
  }

  const formatDisplayNumber = (value: unknown, sourceCurrency = 'USD', maximumFractionDigits = 2) => {
    const converted = toDisplayAmount(value, sourceCurrency)
    if (converted === null) return ''
    return Number(converted.toFixed(maximumFractionDigits))
  }

  return {
    displayCurrency,
    currencyOptions,
    selectedCurrencyMeta,
    rates,
    ratesSource,
    ratesUpdatedAt,
    ratesAreFallback,
    loadingRates,
    setDisplayCurrency,
    loadCurrencyRates,
    normalizeCurrency,
    convertMoney,
    fromDisplayAmount,
    toDisplayAmount,
    formatMoney,
    formatCompactMoney,
    formatSignedMoney,
    formatDisplayNumber,
  }
}
