import { isRecord } from '@/composables/pageSnapshot'
import { getLocalStorage } from '@/utils/storage'

const STORAGE_SCHEMA_VERSION = 2
const STORAGE_TTL_MS = 1000 * 60 * 60 * 12

interface MarketSnapshotStorageEnvelope<TPayload> {
  version: number
  savedAt: number
  payload: TPayload
}

const readMarketWarmSnapshot = <TPayload>(storageKey: string, label: string): TPayload | null => {
  const storage = getLocalStorage()
  if (storage === null) return null
  try {
    const stored = storage.getItem(storageKey)
    if (!stored) return null
    const parsed = JSON.parse(stored)
    if (!isRecord(parsed)) return null
    if (parsed.version !== STORAGE_SCHEMA_VERSION) return null
    if (typeof parsed.savedAt !== 'number' || Date.now() - parsed.savedAt > STORAGE_TTL_MS) return null
    return parsed.payload as TPayload
  } catch (error) {
    console.warn(`Failed to restore ${label}: ${storageKey}`, error)
    return null
  }
}

const writeMarketWarmSnapshot = <TPayload>(storageKey: string, label: string, payload: TPayload) => {
  const storage = getLocalStorage()
  if (storage === null) return
  try {
    const envelope: MarketSnapshotStorageEnvelope<TPayload> = {
      version: STORAGE_SCHEMA_VERSION,
      savedAt: Date.now(),
      payload,
    }
    storage.setItem(storageKey, JSON.stringify(envelope))
  } catch (error) {
    console.warn(`Failed to save ${label}: ${storageKey}`, error)
  }
}

export const createWarmSnapshotStore = <TPayload, TArgs extends readonly unknown[]>(options: {
  label: string
  key: (...args: TArgs) => string
  validate: (payload: TPayload, ...args: TArgs) => boolean
  hasContent: (payload: TPayload) => boolean
}) => ({
  read(...args: TArgs): TPayload | null {
    const payload = readMarketWarmSnapshot<TPayload>(options.key(...args), options.label)
    if (!payload || !options.validate(payload, ...args)) return null
    return payload
  },
  write(payload: TPayload, ...args: TArgs) {
    if (!options.hasContent(payload)) return
    writeMarketWarmSnapshot(options.key(...args), options.label, payload)
  },
})
