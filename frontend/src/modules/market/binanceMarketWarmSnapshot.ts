import type { BinanceMarketPageResponse } from './contracts'
import { readMarketWarmSnapshot, writeMarketWarmSnapshot } from './warmSnapshotStorage'

const MARKET_KEY_PREFIX = 'heimdall_binance_market_warm_snapshot:market-page'
const MARKET_SNAPSHOT_LABEL = 'Binance market warm snapshot'

const marketPageKey = (minRisePct: number, quoteAsset: string) => (
  `${MARKET_KEY_PREFIX}:${quoteAsset.toUpperCase()}:${Number(minRisePct).toFixed(2)}`
)

export const restoreBinanceMarketWarmSnapshot = (
  minRisePct: number,
  quoteAsset: string,
): BinanceMarketPageResponse | null => {
  const payload = readMarketWarmSnapshot<BinanceMarketPageResponse>(
    marketPageKey(minRisePct, quoteAsset),
    MARKET_SNAPSHOT_LABEL,
  )
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
  writeMarketWarmSnapshot(marketPageKey(minRisePct, quoteAsset), MARKET_SNAPSHOT_LABEL, payload)
}
