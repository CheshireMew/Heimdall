import { computed, ref, watch } from 'vue'
import { getLocalStorage } from '@/utils/storage'

export interface TimezoneOption {
  value: string
  label: string
}

export const TIMEZONE_OPTIONS: TimezoneOption[] = [
  { value: 'UTC', label: 'UTC' },
  { value: 'Asia/Shanghai', label: 'Asia/Shanghai (北京)' },
  { value: 'America/New_York', label: 'America/New_York' },
  { value: 'Europe/London', label: 'Europe/London' },
  { value: 'Asia/Tokyo', label: 'Asia/Tokyo' },
]

const STORAGE_KEY = 'heimdall_user_preferences'

interface StoredPreferences {
  timezone?: string
  displayCurrency?: string
}

const readStoredPreferences = (): StoredPreferences => {
  const storage = getLocalStorage()
  if (storage === null) return {}
  try {
    const raw = storage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : {}
  } catch (error) {
    console.warn('Failed to read user preferences:', error)
    return {}
  }
}

const detectTimezone = () => {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || 'Asia/Shanghai'
  } catch {
    return 'Asia/Shanghai'
  }
}

const defaultCurrencyForTimezone = (timezone: string) => (
  timezone === 'Asia/Shanghai' ? 'CNY' : 'USD'
)

const storedPreferences = readStoredPreferences()
const timezone = ref(storedPreferences.timezone || detectTimezone())
const displayCurrency = ref((storedPreferences.displayCurrency || defaultCurrencyForTimezone(timezone.value)).toUpperCase())

watch([timezone, displayCurrency], () => {
  getLocalStorage()?.setItem(STORAGE_KEY, JSON.stringify({
    timezone: timezone.value,
    displayCurrency: displayCurrency.value,
  }))
})

export function useUserPreferences() {
  const timezoneOptions = computed(() => {
    const knownValues = new Set(TIMEZONE_OPTIONS.map((item) => item.value))
    if (knownValues.has(timezone.value)) return TIMEZONE_OPTIONS
    return [{ value: timezone.value, label: timezone.value }, ...TIMEZONE_OPTIONS]
  })

  const setTimezone = (value: string) => {
    timezone.value = value || 'Asia/Shanghai'
  }

  const setDisplayCurrency = (value: string) => {
    displayCurrency.value = (value || 'USD').toUpperCase()
  }

  return {
    timezone,
    displayCurrency,
    timezoneOptions,
    setTimezone,
    setDisplayCurrency,
  }
}
