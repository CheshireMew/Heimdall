// This file is generated from backend FastAPI route contracts.
// Do not edit manually.

export interface DCAResponse {
  symbol: string
  asset_class?: string | null
  price_basis?: string | null
  pricing_symbol?: string | null
  pricing_name?: string | null
  pricing_currency?: string | null
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
  history: Array<DCAHistoryPointResponse>
  profit_pct?: number | null
}

export interface DCARequestSchema {
  symbol?: string
  amount?: number
  start_date?: string | null
  investment_time?: string
  timezone?: string
  days?: number | null
  strategy?: string
  strategy_params?: { [key: string]: string | number | boolean | Array<string | number | boolean | null> | { [key: string]: string | number | boolean | null } | Array<{ [key: string]: string | number | boolean | null }> | { [key: string]: Array<string | number | boolean | null> } | null } | null
}

export interface PairCompareToolResponse {
  symbol_a: string
  symbol_b: string
  data_a: Array<ToolCandlestickPointResponse>
  data_b: Array<ToolCandlestickPointResponse>
  ratio_ohlc: Array<ToolCandlestickPointResponse>
  ratio_symbol: string
  timeframe?: string | null
  relative_strength?: number | null
}

export interface PairCompareRequestSchema {
  symbol_a?: string
  symbol_b?: string
  days?: number
  timeframe?: string
}

export interface DCAHistoryPointResponse {
  date: string
  price: number
  invested: number
  value: number
  coins: number
  roi: number
  avg_cost: number
}

export interface ToolCandlestickPointResponse {
  time: number
  open: number
  high: number
  low: number
  close: number
}
