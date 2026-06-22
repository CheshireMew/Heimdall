import { isRecord, readBoolean, readEnum } from '@/composables/pageSnapshot'

export interface HalvingPageSnapshot {
  showPhases: boolean
  scaleType: 'logarithmic' | 'linear'
}

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

