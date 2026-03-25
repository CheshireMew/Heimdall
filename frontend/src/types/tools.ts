import type { CandlestickData } from './market'

export interface DCASimulationConfig {
  symbol?: string
  amount?: number
  start_date?: string | null
  investment_time?: string
  timezone?: string
  days?: number | null
  strategy?: string
  strategy_params?: Record<string, unknown>
}

export interface DCAHistoryPoint {
  date: string
  price: number
  invested: number
  value: number
  coins: number
  roi: number
  avg_cost: number
}

export interface DCASimulationResponse {
  symbol: string
  start_date: string
  end_date: string
  target_time: string
  total_days: number
  total_invested: number
  final_value: number
  total_coins: number
  roi: number
  average_cost: number
  profit_loss: number
  current_price: number
  history: DCAHistoryPoint[]
}

export interface PairCompareParams {
  symbol_a: string
  symbol_b: string
  days?: number
  timeframe?: string
}

export interface PairCompareResponse {
  symbol_a: string
  symbol_b: string
  data_a: CandlestickData[]
  data_b: CandlestickData[]
  ratio_ohlc: CandlestickData[]
  ratio_symbol: string
}
