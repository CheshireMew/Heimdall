import type { BinanceWeb3HeatRankBoardsResponse } from './contracts'
import { readMarketWarmSnapshot, writeMarketWarmSnapshot } from './warmSnapshotStorage'

const WEB3_KEY_PREFIX = 'heimdall_web3_market_rank_warm_snapshot:heat-rank'
const WEB3_SNAPSHOT_LABEL = 'Web3 market warm snapshot'

const web3HeatRankKey = (chainId: string, size: number) => (
  `${WEB3_KEY_PREFIX}:${chainId}:${size}`
)

export const restoreWeb3HeatRankWarmSnapshot = (
  chainId: string,
  size: number,
): BinanceWeb3HeatRankBoardsResponse | null => {
  const payload = readMarketWarmSnapshot<BinanceWeb3HeatRankBoardsResponse>(
    web3HeatRankKey(chainId, size),
    WEB3_SNAPSHOT_LABEL,
  )
  if (!payload || payload.chain_id !== chainId || payload.size !== size || !payload.boards) return null
  return payload
}

export const saveWeb3HeatRankWarmSnapshot = (
  chainId: string,
  size: number,
  payload: BinanceWeb3HeatRankBoardsResponse,
) => {
  if (!Object.values(payload.boards || {}).some((board) => Boolean(board.items?.length))) return
  writeMarketWarmSnapshot(web3HeatRankKey(chainId, size), WEB3_SNAPSHOT_LABEL, payload)
}
