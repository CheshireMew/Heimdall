import { getLocalStorage } from '@/utils/storage'

const STORAGE_SCHEMA_VERSION = 2
const STORAGE_TTL_MS = 1000 * 60 * 60 * 12

interface MarketSnapshotStorageEnvelope<TPayload> {
  version: number
  savedAt: number
  payload: TPayload
}

const isRecord = (value: unknown): value is Record<string, unknown> => typeof value === 'object' && value !== null

export const readMarketWarmSnapshot = <TPayload>(storageKey: string, label: string): TPayload | null => {
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

export const writeMarketWarmSnapshot = <TPayload>(storageKey: string, label: string, payload: TPayload) => {
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
