import { getLocalStorage } from '@/utils/storage'
import type { BinanceWeb3HeatRankResponse } from '../../types/market'

const WARM_SNAPSHOT_VERSION = 1
const WARM_SNAPSHOT_TTL_MS = 1000 * 60 * 60 * 12
const WEB3_KEY_PREFIX = 'heimdall_web3_market_rank_warm_snapshot:heat-rank'

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
    console.warn(`Failed to restore Web3 market warm snapshot: ${storageKey}`, error)
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
    console.warn(`Failed to save Web3 market warm snapshot: ${storageKey}`, error)
  }
}

const web3HeatRankKey = (chainId: string, size: number) => (
  `${WEB3_KEY_PREFIX}:${chainId}:${size}`
)

export const restoreWeb3HeatRankWarmSnapshot = (
  chainId: string,
  size: number,
): BinanceWeb3HeatRankResponse | null => {
  const payload = readEnvelope<BinanceWeb3HeatRankResponse>(web3HeatRankKey(chainId, size))
  if (!payload || payload.chain_id !== chainId || payload.size !== size || !Array.isArray(payload.items)) return null
  return payload
}

export const saveWeb3HeatRankWarmSnapshot = (
  chainId: string,
  size: number,
  payload: BinanceWeb3HeatRankResponse,
) => {
  if (!payload.items?.length) return
  writeEnvelope(web3HeatRankKey(chainId, size), payload)
}
