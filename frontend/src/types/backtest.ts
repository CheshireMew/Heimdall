export interface BacktestStartRequest {
  strategy_key: string
  strategy_version?: number | null
  timeframe: string
  days: number
  initial_cash: number
  fee_rate: number
  portfolio: BacktestPortfolioConfig
  research: BacktestResearchConfig
}

export interface BacktestStartResponse {
  success: boolean
  backtest_id: number
  message: string
}

export interface BacktestMetrics {
  total_candles: number
  total_signals: number
  buy_signals: number
  sell_signals: number
  hold_signals: number
}

export interface BacktestSignal {
  id: number
  timestamp: string | null
  price: number
  signal: string
  confidence: number
  indicators?: Record<string, unknown> | null
  reasoning?: string | null
}

export interface BacktestRun {
  id: number
  symbol: string
  timeframe: string
  start_date: string | null
  end_date: string | null
  status: string
  metadata?: Record<string, unknown> | null
  report?: Record<string, unknown> | null
  created_at: string | null
  metrics: BacktestMetrics
  signals?: BacktestSignal[] | null
}

export interface BacktestTrade {
  id: number
  pair: string
  opened_at: string | null
  closed_at: string | null
  entry_price: number
  exit_price: number | null
  stake_amount: number
  amount: number
  profit_abs: number
  profit_pct: number
  max_drawdown_pct?: number | null
  duration_minutes?: number | null
  entry_tag?: string | null
  exit_reason?: string | null
  leverage: number
}

export interface BacktestEquityPoint {
  id: number
  timestamp: string | null
  equity: number
  pnl_abs: number
  drawdown_pct: number
}

export interface BacktestPagination {
  page: number
  page_size: number
  total: number
  total_pages: number
}

export interface BacktestDetailResponse extends BacktestRun {
  signals: BacktestSignal[]
  trades: BacktestTrade[]
  equity_curve: BacktestEquityPoint[]
  pagination: BacktestPagination
}

export interface BacktestPortfolioConfig {
  symbols: string[]
  max_open_trades: number
  position_size_pct: number
  stake_mode: 'fixed' | 'unlimited'
}

export interface BacktestResearchConfig {
  slippage_bps: number
  funding_rate_daily: number
  in_sample_ratio: number
  optimize_metric: 'sharpe' | 'profit_pct' | 'calmar' | 'profit_factor'
  optimize_trials: number
  rolling_windows: number
}

export interface StrategyVersion {
  id: number
  version: number
  name: string
  notes?: string | null
  is_default: boolean
  config: Record<string, unknown>
  parameter_space: Record<string, unknown[]>
}

export interface StrategyDefinition {
  key: string
  name: string
  template: string
  category: string
  description?: string | null
  is_active: boolean
  versions: StrategyVersion[]
}

export interface StrategyIndicatorRegistryItem {
  key: string
  engine: string
  name: string
  description?: string | null
  outputs: Array<{ key: string; label: string }>
  params: Array<{
    key: string
    label: string
    type: 'int' | 'float' | 'bool'
    default: number | boolean
    min?: number | null
    max?: number | null
    step?: number | null
  }>
  is_builtin: boolean
}

export interface StrategyRuleSource {
  kind: string
  field?: string | null
  indicator?: string | null
  output?: string | null
  value?: number | null
  multiplier?: number | null
  base_indicator?: string | null
  base_output?: string | null
  offset_indicator?: string | null
  offset_output?: string | null
  offset_multiplier?: number | null
}

export interface StrategyConditionNode {
  id: string
  node_type: 'condition'
  label: string
  left: StrategyRuleSource
  operator: 'gt' | 'gte' | 'lt' | 'lte'
  right: StrategyRuleSource
  enabled: boolean
}

export interface StrategyGroupNode {
  id: string
  node_type: 'group'
  label: string
  logic: 'and' | 'or'
  enabled: boolean
  children: StrategyRuleNode[]
}

export type StrategyRuleNode = StrategyConditionNode | StrategyGroupNode

export interface StrategyOperator {
  key: 'gt' | 'gte' | 'lt' | 'lte'
  label: string
}

export interface StrategyGroupLogic {
  key: 'and' | 'or'
  label: string
}

export interface StrategyRoiTarget {
  id: string
  minutes: number
  profit: number
  enabled: boolean
}

export interface StrategyPartialExit {
  id: string
  profit: number
  size_pct: number
  enabled: boolean
}

export interface StrategyTrailingConfig {
  enabled: boolean
  positive: number
  offset: number
  only_offset_reached: boolean
}

export interface StrategyRiskConfig {
  stoploss: number
  roi_targets: StrategyRoiTarget[]
  trailing: StrategyTrailingConfig
  partial_exits: StrategyPartialExit[]
}

export interface StrategyTemplateConfig {
  indicators: Record<string, {
    label: string
    type: string
    params: Record<string, number | boolean>
  }>
  entry: StrategyGroupNode
  exit: StrategyGroupNode
  risk: StrategyRiskConfig
}

export interface StrategyTemplate {
  template: string
  name: string
  category: string
  description?: string | null
  is_builtin: boolean
  indicator_keys: string[]
  indicator_registry: StrategyIndicatorRegistryItem[]
  operators: StrategyOperator[]
  group_logics: StrategyGroupLogic[]
  default_config: StrategyTemplateConfig
  default_parameter_space: Record<string, unknown[]>
}

export interface StrategyEditorContract {
  operators: StrategyOperator[]
  group_logics: StrategyGroupLogic[]
  blank_condition: StrategyConditionNode
  blank_group: StrategyGroupNode
  blank_config: StrategyTemplateConfig
}

export interface StrategyIndicatorEngine {
  key: string
  engine: string
  name: string
  description?: string | null
  outputs: Array<{ key: string; label: string }>
  params: Array<{
    key: string
    label: string
    type: 'int' | 'float' | 'bool'
    default: number | boolean
    min?: number | null
    max?: number | null
    step?: number | null
  }>
}

export interface IndicatorDefinitionCreateRequest {
  key: string
  name: string
  engine_key: string
  description?: string | null
  params: Array<Record<string, unknown>>
}

export interface StrategyTemplateCreateRequest {
  key: string
  name: string
  category: string
  description?: string | null
  indicator_keys: string[]
  default_config: StrategyTemplateConfig
  default_parameter_space: Record<string, unknown[]>
}

export interface StrategyVersionCreateRequest {
  key: string
  name: string
  template: string
  category: string
  description?: string | null
  config: Record<string, unknown>
  parameter_space: Record<string, unknown[]>
  notes?: string | null
  make_default: boolean
}
