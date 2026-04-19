import { isRecord, readBoolean, readEnum, readNumber } from '@/composables/pageSnapshot'

export interface CryptoIndexSnapshot {
  topN: number
  days: number
}

export interface HalvingPageSnapshot {
  showPhases: boolean
  scaleType: 'logarithmic' | 'linear'
}

export const createDefaultCryptoIndexSnapshot = (): CryptoIndexSnapshot => ({
  topN: 20,
  days: 90,
})

export const normalizeCryptoIndexSnapshot = (
  value: unknown,
  fallback = createDefaultCryptoIndexSnapshot(),
): CryptoIndexSnapshot => {
  const defaults = fallback
  if (!isRecord(value)) return defaults
  return {
    topN: readNumber(value.topN, defaults.topN),
    days: readNumber(value.days, defaults.days),
  }
}

export const buildCryptoIndexSnapshot = (snapshot: CryptoIndexSnapshot): CryptoIndexSnapshot => (
  normalizeCryptoIndexSnapshot(snapshot)
)

export const createDefaultHalvingSnapshot = (): HalvingPageSnapshot => ({
  showPhases: true,
  scaleType: 'logarithmic',
})

export const normalizeHalvingSnapshot = (
  value: unknown,
  fallback = createDefaultHalvingSnapshot(),
): HalvingPageSnapshot => {
  const defaults = fallback
  if (!isRecord(value)) return defaults
  return {
    showPhases: readBoolean(value.showPhases, defaults.showPhases),
    scaleType: readEnum(value.scaleType, ['logarithmic', 'linear'] as const, defaults.scaleType),
  }
}

export const buildHalvingSnapshot = (snapshot: HalvingPageSnapshot): HalvingPageSnapshot => (
  normalizeHalvingSnapshot(snapshot)
)
