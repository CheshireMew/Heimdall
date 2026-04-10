import { watch, type WatchSource, type WatchStopHandle } from 'vue'

const PAGE_SNAPSHOT_PREFIX = 'heimdall_page_snapshot:'

export const PAGE_SNAPSHOT_KEYS = {
  dca: 'tools:dca',
  compare: 'tools:compare',
  portfolioBalance: 'tools:portfolio-balance',
  factorResearch: 'tools:factor-research',
  halving: 'tools:halving',
  cryptoIndex: 'indicators:crypto-index',
  backtest: 'backtest:center',
  backtestEditor: 'backtest:editor',
} as const

export const isRecord = (value: unknown): value is Record<string, unknown> => typeof value === 'object' && value !== null

export const readString = (value: unknown, fallback: string) => (typeof value === 'string' && value ? value : fallback)

export const readNumber = (value: unknown, fallback: number) => (typeof value === 'number' && Number.isFinite(value) ? value : fallback)

export const readBoolean = (value: unknown, fallback: boolean) => (typeof value === 'boolean' ? value : fallback)

export const readStringArray = (value: unknown, fallback: string[] = []) => (
  Array.isArray(value)
    ? value.filter((item): item is string => typeof item === 'string' && item.length > 0)
    : fallback
)

export const createPageSnapshot = <TSnapshot>(
  key: string,
  normalize: (value: unknown) => TSnapshot,
  fallback: TSnapshot,
) => {
  const storageKey = `${PAGE_SNAPSHOT_PREFIX}${key}`

  return {
    exists() {
      if (typeof window === 'undefined') return false
      return window.localStorage.getItem(storageKey) !== null
    },

    load(): TSnapshot {
      if (typeof window === 'undefined') return fallback
      try {
        const stored = window.localStorage.getItem(storageKey)
        if (!stored) return fallback
        return normalize(JSON.parse(stored))
      } catch (error) {
        console.warn(`Failed to load page snapshot: ${storageKey}`, error)
        return fallback
      }
    },

    save(snapshot: TSnapshot) {
      if (typeof window === 'undefined') return
      try {
        window.localStorage.setItem(storageKey, JSON.stringify(snapshot))
      } catch (error) {
        console.warn(`Failed to save page snapshot: ${storageKey}`, error)
      }
    },

    clear() {
      if (typeof window === 'undefined') return
      try {
        window.localStorage.removeItem(storageKey)
      } catch (error) {
        console.warn(`Failed to clear page snapshot: ${storageKey}`, error)
      }
    },
  }
}

export const bindPageSnapshot = <TSnapshot>(
  sources: WatchSource | WatchSource[] | object,
  buildSnapshot: () => TSnapshot,
  saveSnapshot: (snapshot: TSnapshot) => void,
): WatchStopHandle => watch(sources, () => saveSnapshot(buildSnapshot()), { deep: true, immediate: true })
