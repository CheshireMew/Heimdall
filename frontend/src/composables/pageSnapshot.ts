import { watch, type WatchSource, type WatchStopHandle } from 'vue'

const PAGE_SNAPSHOT_PREFIX = 'heimdall_page_snapshot:'
const PAGE_SNAPSHOT_VERSION = 2
const PAGE_SNAPSHOT_TTL_MS = 1000 * 60 * 60 * 24 * 30

export const PAGE_SNAPSHOT_KEYS = {
  dca: 'tools:dca',
  compare: 'tools:compare',
  portfolioBalance: 'tools:portfolio-balance',
  factorResearch: 'tools:factor-research',
  halving: 'tools:halving',
  cryptoIndex: 'indicators:crypto-index',
  binanceMarket: 'indicators:binance-market',
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

export const readEnum = <TValue extends string>(
  value: unknown,
  allowed: readonly TValue[],
  fallback: TValue,
): TValue => (
  typeof value === 'string' && (allowed as readonly string[]).includes(value) ? value as TValue : fallback
)

const readSnapshotEnvelopeData = (value: unknown): unknown | null => {
  if (!isRecord(value)) return null
  if (value.version !== PAGE_SNAPSHOT_VERSION) return null
  if (typeof value.savedAt !== 'number' || Date.now() - value.savedAt > PAGE_SNAPSHOT_TTL_MS) return null
  if (!('data' in value)) return null
  return value.data
}

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
        const data = readSnapshotEnvelopeData(JSON.parse(stored))
        return data === null ? fallback : normalize(data)
      } catch (error) {
        console.warn(`Failed to load page snapshot: ${storageKey}`, error)
        return fallback
      }
    },

    save(snapshot: TSnapshot) {
      if (typeof window === 'undefined') return
      try {
        // 本地快照会跟随页面结构变化，版本不匹配时直接丢弃，避免把旧字段重新灌回新页面。
        window.localStorage.setItem(storageKey, JSON.stringify({
          version: PAGE_SNAPSHOT_VERSION,
          savedAt: Date.now(),
          data: snapshot,
        }))
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
