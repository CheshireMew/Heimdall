import { getLocalStorage } from '@/utils/storage'
import type { BinanceMarketPageResponse } from '../../types/market'

const WARM_SNAPSHOT_VERSION = 2
const WARM_SNAPSHOT_TTL_MS = 1000 * 60 * 60 * 12
const MARKET_KEY_PREFIX = 'heimdall_binance_market_warm_snapshot:market-page'

interface WarmSnapshotEnvelope<TPayload> {
  version: number
  savedAt: number
  payload: TPayload
}

const isRecord = (value: unknown): value is Record<string, unknown> => typeof value === 'object' && value !== null

const readEnvelope = <TPayload>(storageKey: string): TPayload | null => {
  const storage = getLocalStorage()
  if (storage === null) return null
  try {
    const stored = storage.getItem(storageKey)
    if (!stored) return null
    const parsed = JSON.parse(stored)
    if (!isRecord(parsed)) return null
    if (parsed.version !== WARM_SNAPSHOT_VERSION) return null
    if (typeof parsed.savedAt !== 'number' || Date.now() - parsed.savedAt > WARM_SNAPSHOT_TTL_MS) return null
    return parsed.payload as TPayload
  } catch (error) {
    console.warn(`Failed to restore Binance market warm snapshot: ${storageKey}`, error)
    return null
  }
}

const writeEnvelope = <TPayload>(storageKey: string, payload: TPayload) => {
  const storage = getLocalStorage()
  if (storage === null) return
  try {
    const envelope: WarmSnapshotEnvelope<TPayload> = {
      version: WARM_SNAPSHOT_VERSION,
      savedAt: Date.now(),
      payload,
    }
    storage.setItem(storageKey, JSON.stringify(envelope))
  } catch (error) {
    console.warn(`Failed to save Binance market warm snapshot: ${storageKey}`, error)
  }
}

const marketPageKey = (minRisePct: number, quoteAsset: string) => (
  `${MARKET_KEY_PREFIX}:${quoteAsset.toUpperCase()}:${Number(minRisePct).toFixed(2)}`
)

export const restoreBinanceMarketWarmSnapshot = (
  minRisePct: number,
  quoteAsset: string,
): BinanceMarketPageResponse | null => {
  const payload = readEnvelope<BinanceMarketPageResponse>(marketPageKey(minRisePct, quoteAsset))
  if (!payload || payload.exchange !== 'binance' || payload.quote_asset !== quoteAsset.toUpperCase()) return null
  if (!payload.monitor || !payload.spot_boards || !payload.contract_boards) return null
  return payload
}

export const saveBinanceMarketWarmSnapshot = (
  minRisePct: number,
  quoteAsset: string,
  payload: BinanceMarketPageResponse,
) => {
  const hasSpotRows = Object.values(payload.spot_boards || {}).some((board) => Boolean(board.items?.length))
  const hasContractRows = Object.values(payload.contract_boards || {}).some((board) => Boolean(board.items?.length))
  if (!payload.monitor?.items?.length && !hasSpotRows && !hasContractRows) return
  writeEnvelope(marketPageKey(minRisePct, quoteAsset), payload)
}
