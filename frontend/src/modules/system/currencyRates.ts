import { computed, ref } from 'vue'

import type { CurrencyRatesResponse, DisplayCurrencyResponse } from './contracts'

import { systemApi } from './api'

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

export const currencyRates = ref<Record<string, number>>({ ...fallbackRates })
export const supportedCurrencies = ref<DisplayCurrencyResponse[]>(fallbackSupported)
export const ratesSource = ref('fallback')
export const ratesUpdatedAt = ref('')
export const ratesAreFallback = ref(true)
export const loadingRates = ref(false)

let ratesPromise: Promise<void> | null = null

export const currencyMetaByCode = computed(() => {
  const map = new Map<string, DisplayCurrencyResponse>()
  supportedCurrencies.value.forEach((item) => map.set(item.code, item))
  return map
})

export const loadCurrencyRates = async () => {
  if (ratesPromise) return ratesPromise
  loadingRates.value = true
  ratesPromise = systemApi.getCurrencyRates()
    .then((response) => {
      applyCurrencyRates(response.data)
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

const applyCurrencyRates = (payload: CurrencyRatesResponse) => {
  if (payload?.rates) currencyRates.value = { ...fallbackRates, ...payload.rates }
  if (payload?.supported?.length) supportedCurrencies.value = payload.supported
  ratesSource.value = payload?.source || 'fallback'
  ratesUpdatedAt.value = payload?.updated_at || ''
  ratesAreFallback.value = !!payload?.is_fallback
}

export const readCurrencyMeta = (code: string) => (
  currencyMetaByCode.value.get(code) || fallbackSupported.find((item) => item.code === code) || fallbackSupported[0]
)
