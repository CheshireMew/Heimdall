import type {
  BinanceBreakoutMonitorItemResponse,
  BinanceBreakoutMonitorResponse,
  BinanceMarkPriceItemResponse,
  BinanceTickerStatsItemResponse,
  BinanceWeb3HeatRankItemResponse,
} from './contracts'
import { isRecord, readBoolean, readNumber, readString } from '@/composables/pageSnapshot'
import { toBaseSymbol } from './symbolCatalog'

export type MonitorMode = 'all' | 'natural' | 'momentum' | 'focus'
export type MarketFilter = 'all' | 'spot' | 'usdm'
export type ContractSortField = 'price_change_pct' | 'funding_rate_pct'
export type SortDirection = 'desc' | 'asc'

export type ContractBoardRow = DerivativeBoardRow & {
  market: 'usdm'
  market_label: string
}

export type DerivativeBoardRow = BinanceTickerStatsItemResponse & {
  mark_price: number | null
  index_price: number | null
  funding_rate_pct: number | null
}

export type ContractSortState = {
  field: ContractSortField
  direction: SortDirection
}

export type ChartDialogState = {
  open: boolean
  rawSymbol: string
  marketLabel: string
}

export type Web3TokenDialogState = {
  open: boolean
  token: BinanceWeb3HeatRankItemResponse | null
}

export type BinanceMarketSnapshot = {
  minRisePct: number
  mode: MonitorMode
  marketFilter: MarketFilter
  autoRefresh: boolean
  spotSortDirection: SortDirection
  contractSortField: ContractSortField
  contractSortDirection: SortDirection
  selectedKey: string
  web3ChainId: string
}

export const EMPTY_RESPONSE: BinanceBreakoutMonitorResponse = {
  exchange: 'binance',
  min_rise_pct: 5,
  quote_asset: 'USDT',
  updated_at: 0,
  summary: {
    monitored_count: 0,
    natural_count: 0,
    momentum_count: 0,
    focus_count: 0,
    advancing_count: 0,
    spot_count: 0,
    contract_count: 0,
  },
  items: [],
}

export const WEB3_CHAIN_OPTIONS = [
  { label: 'BSC', value: '56' },
  { label: 'Base', value: '8453' },
  { label: 'Solana', value: 'CT_501' },
]

export const WEB3_KLINE_INTERVALS = ['5min', '15min', '1h', '4h', '1d']

export const createDefaultSnapshot = (): BinanceMarketSnapshot => ({
  minRisePct: 5,
  mode: 'focus',
  marketFilter: 'all',
  autoRefresh: true,
  spotSortDirection: 'desc',
  contractSortField: 'price_change_pct',
  contractSortDirection: 'desc',
  selectedKey: '',
  web3ChainId: '56',
})

export const normalizeMode = (value: unknown): MonitorMode => (
  value === 'all' || value === 'natural' || value === 'momentum' || value === 'focus'
    ? value
    : 'focus'
)

export const normalizeMarketFilter = (value: unknown): MarketFilter => (
  value === 'all' || value === 'spot' || value === 'usdm'
    ? value
    : 'all'
)

export const normalizeContractSortField = (value: unknown): ContractSortField => (
  value === 'price_change_pct' || value === 'funding_rate_pct'
    ? value
    : 'price_change_pct'
)

export const normalizeSortDirection = (value: unknown): SortDirection => (
  value === 'asc' || value === 'desc'
    ? value
    : 'desc'
)

export const normalizeSnapshot = (
  value: unknown,
  fallback = createDefaultSnapshot(),
): BinanceMarketSnapshot => {
  const defaults = fallback
  if (!isRecord(value)) return defaults
  return {
    minRisePct: readNumber(value.minRisePct, defaults.minRisePct),
    mode: normalizeMode(value.mode),
    marketFilter: normalizeMarketFilter(value.marketFilter),
    autoRefresh: readBoolean(value.autoRefresh, defaults.autoRefresh),
    spotSortDirection: normalizeSortDirection(value.spotSortDirection),
    contractSortField: normalizeContractSortField(value.contractSortField),
    contractSortDirection: normalizeSortDirection(value.contractSortDirection),
    selectedKey: readString(value.selectedKey, defaults.selectedKey),
    web3ChainId: readString(value.web3ChainId, defaults.web3ChainId),
  }
}

export const buildBinanceMarketSnapshot = (snapshot: BinanceMarketSnapshot): BinanceMarketSnapshot => (
  normalizeSnapshot(snapshot)
)

export const formatSigned = (value: number | null | undefined, digits = 2, suffix = '%', withSign = true) => {
  if (value === null || value === undefined || Number.isNaN(value)) return '--'
  const numeric = Number(value)
  const sign = withSign && numeric > 0 ? '+' : ''
  return `${sign}${numeric.toFixed(digits)}${suffix}`
}

export const formatScore = (value: number | null | undefined) => {
  if (value === null || value === undefined || Number.isNaN(value)) return '--'
  return `${Math.round(Number(value))}`
}

export const formatTime = (timestamp: number | null | undefined) => {
  if (!timestamp) return '--'
  return new Intl.DateTimeFormat('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }).format(new Date(timestamp))
}

export const valueTone = (value: number | null | undefined, positiveIsGood = true) => {
  if (value === null || value === undefined || Number.isNaN(value)) return 'text-slate-500 dark:text-slate-400'
  const rising = positiveIsGood ? value >= 0 : value <= 0
  return rising ? 'text-emerald-500' : 'text-rose-500'
}

export const verdictTone = (verdict: string | null | undefined) => {
  if (verdict === '优先关注') return 'bg-emerald-500/10 text-emerald-600 ring-emerald-500/20 dark:text-emerald-300'
  if (verdict === '继续跟踪') return 'bg-amber-500/10 text-amber-600 ring-amber-500/20 dark:text-amber-300'
  return 'bg-slate-500/10 text-slate-600 ring-slate-500/20 dark:text-slate-300'
}

export const compareNullableNumber = (
  left: number | null | undefined,
  right: number | null | undefined,
  direction: SortDirection,
) => {
  const leftValue = left === null || left === undefined || Number.isNaN(left) ? null : Number(left)
  const rightValue = right === null || right === undefined || Number.isNaN(right) ? null : Number(right)
  if (leftValue === null && rightValue === null) return 0
  if (leftValue === null) return 1
  if (rightValue === null) return -1
  return direction === 'desc' ? rightValue - leftValue : leftValue - rightValue
}

export const sortRowsByMetric = <TRow extends { quote_volume?: number | null; symbol?: string | null }>(
  rows: TRow[],
  selector: (row: TRow) => number | null | undefined,
  direction: SortDirection,
  limit = 15,
) => (
  [...rows]
    .sort((left, right) => {
      const primary = compareNullableNumber(selector(left), selector(right), direction)
      if (primary !== 0) return primary
      const byVolume = compareNullableNumber(left.quote_volume, right.quote_volume, 'desc')
      if (byVolume !== 0) return byVolume
      return String(left.symbol || '').localeCompare(String(right.symbol || ''))
    })
    .slice(0, limit)
)

export const sortContractRows = (rows: ContractBoardRow[], sort: ContractSortState) => (
  sortRowsByMetric(rows, (row) => row[sort.field], sort.direction)
)

export const mergeDerivatives = (
  tickerRows: BinanceTickerStatsItemResponse[] = [],
  markRows: BinanceMarkPriceItemResponse[] = [],
) => {
  const markMap = new Map(markRows.map((item) => [item.symbol, item]))
  return tickerRows
    .map((item) => {
      const mark = markMap.get(item.symbol || '')
      return {
        ...item,
        mark_price: mark?.mark_price ?? null,
        index_price: mark?.index_price ?? null,
        funding_rate_pct: mark?.last_funding_rate != null ? mark.last_funding_rate * 100 : null,
      } satisfies DerivativeBoardRow
    })
    .sort((left, right) => (right.quote_volume || 0) - (left.quote_volume || 0))
}

export const toItemKey = (
  item: Pick<BinanceBreakoutMonitorItemResponse, 'market' | 'symbol'> | Pick<ContractBoardRow, 'market' | 'symbol'> | null | undefined,
) => (item ? `${item.market}:${item.symbol}` : '')

export const formatLoadFailure = (labels: string[]) => {
  if (!labels.length) return ''
  return `${labels.join('、')}加载失败`
}

export const displaySymbol = (value: string | null | undefined) => {
  const symbol = String(value || '').trim().toUpperCase()
  if (!symbol) return '--'
  return toBaseSymbol(symbol) || symbol
}
