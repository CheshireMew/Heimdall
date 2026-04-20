import { watch, type WatchSource, type WatchStopHandle } from 'vue'
import { getLocalStorage } from '@/utils/storage'

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

export interface PersistentPageSnapshot<TSnapshot> {
  initial: TSnapshot
  bind: (sources: WatchSource | WatchSource[] | object, buildSnapshot: () => TSnapshot) => WatchStopHandle
  clear: () => void
}

export const createPersistentPageSnapshot = <TSnapshot>(
  key: string,
  normalize: (value: unknown, fallback: TSnapshot) => TSnapshot,
  fallback: TSnapshot,
): PersistentPageSnapshot<TSnapshot> => {
  const storageKey = `${PAGE_SNAPSHOT_PREFIX}${key}`
  const load = (): TSnapshot => {
    const storage = getLocalStorage()
    if (storage === null) return fallback
    try {
      const stored = storage.getItem(storageKey)
      if (!stored) return fallback
      const data = readSnapshotEnvelopeData(JSON.parse(stored))
      return data === null ? fallback : normalize(data, fallback)
    } catch (error) {
      console.warn(`Failed to load page snapshot: ${storageKey}`, error)
      return fallback
    }
  }

  const save = (snapshot: TSnapshot) => {
    const storage = getLocalStorage()
    if (storage === null) return
    try {
      // 本地快照跟随页面结构变化；版本不匹配时直接丢弃，避免旧字段重新灌回新页面。
      storage.setItem(storageKey, JSON.stringify({
        version: PAGE_SNAPSHOT_VERSION,
        savedAt: Date.now(),
        data: normalize(snapshot, fallback),
      }))
    } catch (error) {
      console.warn(`Failed to save page snapshot: ${storageKey}`, error)
    }
  }

  return {
    initial: load(),
    bind(sources: WatchSource | WatchSource[] | object, buildSnapshot: () => TSnapshot) {
      return watch(sources, () => save(buildSnapshot()), { deep: true, immediate: true })
    },
    clear() {
      const storage = getLocalStorage()
      if (storage === null) return
      try {
        storage.removeItem(storageKey)
      } catch (error) {
        console.warn(`Failed to clear page snapshot: ${storageKey}`, error)
      }
    },
  }
}
