// This file is generated from backend Pydantic schemas.
// Do not edit manually.

export interface BacktestStartRequest {
  strategy_key?: string
  strategy_version?: number | null
  timeframe?: string
  start_date?: string
  end_date?: string
  initial_cash?: number
  fee_rate?: number
  portfolio?: BacktestPortfolioConfig
  research?: BacktestResearchConfig
}

export interface BacktestStartResponse {
  success: boolean
  backtest_id: number
  message: string
}

export interface PaperStartRequest {
  strategy_key?: string
  strategy_version?: number | null
  timeframe?: string
  initial_cash?: number
  fee_rate?: number
  portfolio?: BacktestPortfolioConfig
}

export interface PaperStartResponse {
  success: boolean
  run_id: number
  message: string
}

export interface PaperStopResponse {
  success: boolean
  run_id: number
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
  indicators?: { [key: string]: unknown } | null
  reasoning?: string | null
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

export interface BacktestRun {
  id: number
  symbol: string
  timeframe: string
  start_date: string | null
  end_date: string | null
  status: string
  metadata?: BacktestRunMetadata | null
  report?: BacktestReport | null
  created_at: string | null
  metrics: BacktestMetrics
  signals?: Array<BacktestSignal> | null
}

export interface BacktestDetailResponse {
  id: number
  symbol: string
  timeframe: string
  start_date: string | null
  end_date: string | null
  status: string
  metadata?: BacktestRunMetadata | null
  report?: BacktestReport | null
  created_at: string | null
  metrics: BacktestMetrics
  signals: Array<BacktestSignal>
  trades: Array<BacktestTrade>
  equity_curve: Array<BacktestEquityPoint>
  pagination: BacktestPagination
}

export interface BacktestRunMetadata {
  schema_version?: number | null
  execution_mode?: string | null
  execution_model?: string | null
  engine?: string | null
  exchange?: string | null
  market_type?: string | null
  direction?: string | null
  strategy_key?: string | null
  strategy_name?: string | null
  strategy_version?: number | null
  strategy_template?: string | null
  strategy_notes?: string | null
  symbols?: Array<string>
  execution_symbols?: Array<string>
  price_source?: string | null
  portfolio_label?: string | null
  initial_cash?: number | null
  fee_rate?: number | null
  fee_ratio?: number | null
  timeframe?: string | null
  stake_currency?: string | null
  portfolio?: BacktestPortfolioPayload | null
  research?: BacktestResearchPayload | BacktestResearchReport | null
  selected_config?: { [key: string]: unknown }
  sample_ranges?: BacktestSampleRanges | null
  runtime_state?: BacktestRuntimeState | null
  paper_live?: BacktestPaperLive | null
  report?: BacktestReport | null
  raw_stats?: BacktestReportSnapshot | null
  error?: string | null
}

export interface BacktestReport {
  initial_cash: number
  final_balance: number
  profit_abs: number
  profit_pct: number
  annualized_return_pct?: number | null
  max_drawdown_pct: number
  sharpe?: number | null
  sortino?: number | null
  calmar?: number | null
  profit_factor?: number | null
  expectancy_ratio?: number | null
  win_rate: number
  total_trades: number
  wins: number
  losses: number
  draws: number
  avg_trade_pct?: number | null
  avg_trade_duration_minutes?: number | null
  best_trade_pct?: number | null
  worst_trade_pct?: number | null
  pair_breakdown?: Array<BacktestPairBreakdown>
  symbols?: Array<string>
  timeframe?: string | null
  strategy?: BacktestStrategySummary | null
  portfolio?: BacktestPortfolioSummary | null
  research?: BacktestResearchReport | null
}

export interface BacktestReportSnapshot {
  profit_pct?: number | null
  profit_abs?: number | null
  final_balance?: number | null
  max_drawdown_pct?: number | null
  sharpe?: number | null
  calmar?: number | null
  profit_factor?: number | null
  win_rate?: number | null
  total_trades?: number | null
}

export interface BacktestDateRange {
  start: string
  end: string
}

export interface BacktestPairBreakdown {
  pair: string
  trades: number
  profit_abs: number
  profit_pct: number
  win_rate: number
}

export interface BacktestStrategySummary {
  key: string
  name: string
  version: number
  template: string
}

export interface BacktestPortfolioSummary {
  symbols?: Array<string>
  max_open_trades?: number | null
  position_size_pct?: number | null
  stake_mode?: string | null
  stake_currency?: string | null
}

export interface BacktestPortfolioPayload {
  symbols?: Array<string>
  max_open_trades?: number | null
  position_size_pct?: number | null
  stake_mode?: string | null
}

export interface BacktestResearchPayload {
  slippage_bps?: number | null
  funding_rate_daily?: number | null
  in_sample_ratio?: number | null
  optimize_metric?: string | null
  optimize_trials?: number | null
  rolling_windows?: number | null
}

export interface BacktestOptimizationTrial {
  trial: number
  score?: number | null
  config?: { [key: string]: unknown }
  report?: BacktestReportSnapshot | null
}

export interface BacktestOptimizationSummary {
  metric: string
  trial_count: number
  best_score?: number | null
  best_config?: { [key: string]: unknown }
  trials?: Array<BacktestOptimizationTrial>
}

export interface BacktestIterationSummary {
  range?: BacktestDateRange | null
  config?: { [key: string]: unknown }
  report?: BacktestReportSnapshot | null
}

export interface BacktestRollingWindow {
  index: number
  train?: BacktestDateRange | null
  test: BacktestDateRange
  config?: { [key: string]: unknown }
  optimization?: BacktestOptimizationSummary | null
  report?: BacktestReportSnapshot | null
}

export interface BacktestResearchReport {
  selected_config?: { [key: string]: unknown }
  in_sample_ratio: number
  slippage_bps: number
  funding_rate_daily: number
  optimization?: BacktestOptimizationSummary | null
  in_sample?: BacktestIterationSummary | null
  out_of_sample?: BacktestIterationSummary | null
  rolling_windows?: Array<BacktestRollingWindow>
}

export interface BacktestSampleRanges {
  requested?: BacktestDateRange | null
  displayed?: BacktestDateRange | null
  in_sample?: BacktestDateRange | null
  out_of_sample?: BacktestDateRange | null
}

export interface BacktestPaperPosition {
  symbol: string
  side?: string
  opened_at: string
  entry_price: number
  remaining_amount: number
  remaining_cost: number
  highest_price: number
  lowest_price: number
  last_price: number
  taken_partial_ids?: Array<string>
}

export interface BacktestRuntimeState {
  cash_balance: number
  last_processed?: { [key: string]: number | null }
  last_synced_end?: number | null
  positions?: { [key: string]: BacktestPaperPosition }
}

export interface BacktestPaperLive {
  cash_balance: number
  open_positions: number
  positions?: Array<BacktestPaperPosition>
  last_updated: string
  stop_reason?: string | null
}

export interface BacktestPortfolioConfig {
  symbols?: Array<string>
  max_open_trades?: number
  position_size_pct?: number
  stake_mode?: "fixed" | "unlimited"
}

export interface BacktestResearchConfig {
  slippage_bps?: number
  funding_rate_daily?: number
  in_sample_ratio?: number
  optimize_metric?: "sharpe" | "profit_pct" | "calmar" | "profit_factor"
  optimize_trials?: number
  rolling_windows?: number
}

export interface StrategyVersion {
  id: number
  version: number
  name: string
  notes?: string | null
  is_default: boolean
  config: StrategyTemplateConfig
  parameter_space: { [key: string]: Array<unknown> }
  runtime: StrategyRunProfile
}

export interface StrategyDefinition {
  key: string
  name: string
  template: string
  category: string
  description?: string | null
  is_active: boolean
  template_runtime?: StrategyTemplateRuntime
  versions: Array<StrategyVersion>
}

export interface StrategyIndicatorRegistryItem {
  key: string
  engine: string
  name: string
  description?: string | null
  outputs: Array<StrategyIndicatorOutput>
  params: Array<StrategyIndicatorParam>
  is_builtin: boolean
}

export interface StrategyOperator {
  key: string
  label: string
}

export interface StrategyTemplateCapabilities {
  signal_runtime?: boolean
  paper?: boolean
  version_editing?: boolean
}

export interface StrategyTemplateRuntime {
  builder_kind?: string
  capabilities?: StrategyTemplateCapabilities
}

export interface StrategyGroupLogic {
  key: string
  label: string
}

export interface StrategyIndicatorEngine {
  key: string
  engine: string
  name: string
  description?: string | null
  outputs: Array<StrategyIndicatorOutput>
  params: Array<StrategyIndicatorParam>
}

export interface StrategyTemplate {
  template: string
  name: string
  category: string
  description?: string | null
  is_builtin?: boolean
  template_runtime?: StrategyTemplateRuntime
  indicator_keys?: Array<string>
  indicator_registry: Array<StrategyIndicatorRegistryItem>
  operators: Array<StrategyOperator>
  group_logics: Array<StrategyGroupLogic>
  default_config: StrategyTemplateConfig
  default_parameter_space: { [key: string]: Array<unknown> }
}

export interface StrategyEditorContract {
  operators: Array<StrategyOperator>
  group_logics: Array<StrategyGroupLogic>
  timeframe_options: Array<StrategyOperator>
  market_type_options: Array<StrategyOperator>
  direction_options: Array<StrategyOperator>
  blank_condition: StrategyConditionNode
  blank_group: StrategyGroupNode
  blank_config: StrategyTemplateConfig
  run_defaults: BacktestRunDefaults
}

export interface StrategyVersionCreateRequest {
  key: string
  name: string
  template: string
  category: string
  description?: string | null
  config: StrategyTemplateConfig
  parameter_space?: { [key: string]: Array<unknown> }
  notes?: string | null
  make_default?: boolean
}

export interface IndicatorDefinitionCreateRequest {
  key: string
  name: string
  engine_key: string
  description?: string | null
  params?: Array<StrategyIndicatorParam>
}

export interface StrategyTemplateCreateRequest {
  key: string
  name: string
  category: string
  description?: string | null
  indicator_keys?: Array<string>
  default_config: StrategyTemplateConfig
  default_parameter_space?: { [key: string]: Array<unknown> }
}

export interface StrategyRuleSource {
  kind: string
  field?: string | null
  indicator?: string | null
  output?: string | null
  bars_ago?: number | null
  value?: number | null
  multiplier?: number | null
  base_indicator?: string | null
  base_output?: string | null
  offset_indicator?: string | null
  offset_output?: string | null
  offset_multiplier?: number | null
}

export interface StrategyStateBranch {
  id: string
  label: string
  enabled?: boolean
  regime: StrategyGroupNode
  long_entry: StrategyGroupNode
  long_exit: StrategyGroupNode
  short_entry: StrategyGroupNode
  short_exit: StrategyGroupNode
}

export interface StrategyIndicatorConfig {
  label: string
  type: string
  timeframe?: string
  params?: { [key: string]: number | boolean }
}

export interface StrategyExecutionConfig {
  market_type?: "spot" | "futures"
  direction?: "long_only" | "long_short"
}

export interface StrategyRoiTarget {
  id: string
  minutes: number
  profit: number
  enabled?: boolean
}

export interface StrategyPartialExit {
  id: string
  profit: number
  size_pct: number
  enabled?: boolean
}

export interface StrategyTrailingConfig {
  enabled?: boolean
  positive: number
  offset: number
  only_offset_reached?: boolean
}

export interface StrategyRiskConfig {
  stoploss: number
  roi_targets?: Array<StrategyRoiTarget>
  trailing: StrategyTrailingConfig
  partial_exits?: Array<StrategyPartialExit>
}

export interface StrategyTemplateConfig {
  indicators?: { [key: string]: StrategyIndicatorConfig }
  execution: StrategyExecutionConfig
  regime_priority?: Array<"trend" | "range">
  trend: StrategyStateBranch
  range: StrategyStateBranch
  risk: StrategyRiskConfig
}

export interface BacktestRunDefaults {
  strategy_key?: string
  timeframe?: string
  start_date?: string
  end_date?: string
  initial_cash?: number
  fee_rate?: number
  portfolio?: BacktestPortfolioConfig
  research?: BacktestResearchConfig
  history_mode?: "backtest" | "paper"
  optimize_metric_options?: Array<StrategyOperator>
}

export interface StrategyIndicatorOutput {
  key: string
  label: string
}

export interface StrategyIndicatorParam {
  key: string
  label: string
  type: "int" | "float" | "bool"
  default: number | boolean
  min?: number | null
  max?: number | null
  step?: number | null
}

export interface StrategyRunProfile {
  indicator_timeframes?: Array<string>
  allowed_run_timeframes?: Array<string>
  preferred_run_timeframe: string
}

export interface StrategyConditionNode {
  id: string
  node_type?: 'condition'
  label: string
  left: StrategyRuleSource
  operator: 'gt' | 'gte' | 'lt' | 'lte'
  right: StrategyRuleSource
  enabled?: boolean
}

export interface StrategyGroupNode {
  id: string
  node_type?: 'group'
  label: string
  logic: 'and' | 'or'
  enabled?: boolean
  children?: Array<StrategyRuleNode>
}

export type StrategyRuleNode = StrategyConditionNode | StrategyGroupNode
