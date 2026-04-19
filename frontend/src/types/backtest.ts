// This file is generated from backend FastAPI route contracts.
// Do not edit manually.

export interface BacktestStartResponse {
  success: boolean
  backtest_id: number
  message: string
}

export interface BacktestStartRequest {
  strategy_key?: string
  strategy_version?: number | null
  timeframe?: string
  start_date?: string
  end_date?: string
  initial_cash?: number
  fee_rate?: number
  portfolio?: BacktestPortfolioRequest
  research?: BacktestResearchRequest
}

export interface PaperStartResponse {
  success: boolean
  run_id: number
  message: string
}

export interface PaperStartRequest {
  strategy_key?: string
  strategy_version?: number | null
  timeframe?: string
  initial_cash?: number
  fee_rate?: number
  portfolio?: BacktestPortfolioRequest
}

export interface PaperStopResponse {
  success: boolean
  run_id: number
  message: string
}

export interface BacktestDeleteResponse {
  success: boolean
  run_id: number
  message: string
}

export interface StrategyDefinitionResponse {
  key: string
  name: string
  template: string
  category: string
  description?: string | null
  is_active: boolean
  template_runtime?: StrategyTemplateRuntimeResponse
  versions: Array<StrategyVersionResponse>
}

export interface StrategyTemplateResponse {
  template: string
  name: string
  category: string
  description?: string | null
  is_builtin?: boolean
  template_runtime?: StrategyTemplateRuntimeResponse
  indicator_keys?: Array<string>
  indicator_registry: Array<StrategyIndicatorRegistryResponse>
  operators: Array<StrategyOperatorResponse>
  group_logics: Array<StrategyGroupLogicResponse>
  default_config: StrategyTemplateConfigResponse
  default_parameter_space: { [key: string]: Array<string | number | boolean | Array<string | number | boolean | null> | { [key: string]: string | number | boolean | null } | Array<{ [key: string]: string | number | boolean | null }> | { [key: string]: Array<string | number | boolean | null> } | null> }
}

export interface StrategyEditorContractResponse {
  operators: Array<StrategyOperatorResponse>
  group_logics: Array<StrategyGroupLogicResponse>
  timeframe_options: Array<StrategyOperatorResponse>
  market_type_options: Array<StrategyOperatorResponse>
  direction_options: Array<StrategyOperatorResponse>
  blank_condition: StrategyConditionNodeResponse
  blank_group: StrategyGroupNodeResponse
  blank_config: StrategyTemplateConfigResponse
  run_defaults: BacktestRunDefaultsResponse
}

export interface StrategyTemplateCreateRequest {
  key: string
  name: string
  category: string
  description?: string | null
  indicator_keys?: Array<string>
  default_config: StrategyTemplateConfigResponse
  default_parameter_space?: { [key: string]: Array<string | number | boolean | Array<string | number | boolean | null> | { [key: string]: string | number | boolean | null } | Array<{ [key: string]: string | number | boolean | null }> | { [key: string]: Array<string | number | boolean | null> } | null> }
}

export interface StrategyIndicatorRegistryResponse {
  key: string
  engine: string
  name: string
  description?: string | null
  outputs: Array<StrategyIndicatorOutputResponse>
  params: Array<StrategyIndicatorParamResponse>
  is_builtin: boolean
}

export interface StrategyIndicatorEngineResponse {
  key: string
  engine: string
  name: string
  description?: string | null
  outputs: Array<StrategyIndicatorOutputResponse>
  params: Array<StrategyIndicatorParamResponse>
}

export interface IndicatorDefinitionCreateRequest {
  key: string
  name: string
  engine_key: string
  description?: string | null
  params?: Array<StrategyIndicatorParamResponse>
}

export interface StrategyVersionResponse {
  id: number | null
  version: number
  name: string
  notes?: string | null
  is_default: boolean
  config: StrategyTemplateConfigResponse
  parameter_space: { [key: string]: Array<string | number | boolean | Array<string | number | boolean | null> | { [key: string]: string | number | boolean | null } | Array<{ [key: string]: string | number | boolean | null }> | { [key: string]: Array<string | number | boolean | null> } | null> }
  runtime: StrategyRunProfileResponse
}

export interface StrategyVersionCreateRequest {
  key: string
  name: string
  template: string
  category: string
  description?: string | null
  config: StrategyTemplateConfigResponse
  parameter_space?: { [key: string]: Array<string | number | boolean | Array<string | number | boolean | null> | { [key: string]: string | number | boolean | null } | Array<{ [key: string]: string | number | boolean | null }> | { [key: string]: Array<string | number | boolean | null> } | null> }
  notes?: string | null
  make_default?: boolean
}

export interface BacktestRunResponse {
  id: number
  symbol: string
  timeframe: string
  start_date: string | null
  end_date: string | null
  status: string
  metadata?: BacktestRunMetadataResponse | null
  report?: BacktestReportResponse | null
  created_at: string | null
  metrics: BacktestMetricsResponse
  signals?: Array<BacktestSignalResponse> | null
}

export interface BacktestDetailResponse {
  id: number
  symbol: string
  timeframe: string
  start_date: string | null
  end_date: string | null
  status: string
  metadata?: BacktestRunMetadataResponse | null
  report?: BacktestReportResponse | null
  created_at: string | null
  metrics: BacktestMetricsResponse
  signals: Array<BacktestSignalResponse>
  trades: Array<BacktestTradeResponse>
  equity_curve: Array<BacktestEquityPointResponse>
  pagination: PaginationResponse
}

export interface BacktestDateRangeResponse {
  start: string
  end: string
}

export interface BacktestEquityPointResponse {
  id: number
  timestamp: string | null
  equity: number
  pnl_abs: number
  drawdown_pct: number
}

export interface BacktestIterationSummaryResponse {
  range?: BacktestDateRangeResponse | null
  config?: { [key: string]: string | number | boolean | Array<string | number | boolean | null> | { [key: string]: string | number | boolean | null } | Array<{ [key: string]: string | number | boolean | null }> | { [key: string]: Array<string | number | boolean | null> } | null }
  report?: BacktestReportSnapshotResponse | null
}

export interface BacktestMetricsResponse {
  total_candles: number
  total_signals: number
  buy_signals: number
  sell_signals: number
  hold_signals: number
}

export interface BacktestOptimizationSummaryResponse {
  metric: string
  trial_count: number
  best_score?: number | null
  best_config?: { [key: string]: string | number | boolean | Array<string | number | boolean | null> | { [key: string]: string | number | boolean | null } | Array<{ [key: string]: string | number | boolean | null }> | { [key: string]: Array<string | number | boolean | null> } | null }
  trials?: Array<BacktestOptimizationTrialResponse>
}

export interface BacktestOptimizationTrialResponse {
  trial: number
  score?: number | null
  config?: { [key: string]: string | number | boolean | Array<string | number | boolean | null> | { [key: string]: string | number | boolean | null } | Array<{ [key: string]: string | number | boolean | null }> | { [key: string]: Array<string | number | boolean | null> } | null }
  report?: BacktestReportSnapshotResponse | null
}

export interface BacktestPairBreakdownResponse {
  pair: string
  trades: number
  profit_abs: number
  profit_pct: number
  win_rate: number
}

export interface BacktestPaperLiveResponse {
  cash_balance: number
  open_positions: number
  positions?: Array<BacktestPaperPositionResponse>
  last_updated: string
  stop_reason?: string | null
}

export interface BacktestPaperPositionResponse {
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

export interface BacktestPortfolioPayloadResponse {
  symbols?: Array<string>
  max_open_trades?: number | null
  position_size_pct?: number | null
  stake_mode?: string | null
}

export interface BacktestPortfolioRequest {
  symbols?: Array<string>
  max_open_trades?: number
  position_size_pct?: number
  stake_mode?: "fixed" | "unlimited"
}

export interface BacktestPortfolioSummaryResponse {
  symbols?: Array<string>
  max_open_trades?: number | null
  position_size_pct?: number | null
  stake_mode?: string | null
  stake_currency?: string | null
}

export interface BacktestReportResponse {
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
  pair_breakdown?: Array<BacktestPairBreakdownResponse>
  symbols?: Array<string>
  timeframe?: string | null
  strategy?: BacktestStrategySummaryResponse | null
  portfolio?: BacktestPortfolioSummaryResponse | null
  research?: BacktestResearchReportResponse | null
}

export interface BacktestReportSnapshotResponse {
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

export interface BacktestResearchPayloadResponse {
  slippage_bps?: number | null
  funding_rate_daily?: number | null
  in_sample_ratio?: number | null
  optimize_metric?: string | null
  optimize_trials?: number | null
  rolling_windows?: number | null
}

export interface BacktestResearchReportResponse {
  selected_config?: { [key: string]: string | number | boolean | Array<string | number | boolean | null> | { [key: string]: string | number | boolean | null } | Array<{ [key: string]: string | number | boolean | null }> | { [key: string]: Array<string | number | boolean | null> } | null }
  in_sample_ratio: number
  slippage_bps: number
  funding_rate_daily: number
  optimization?: BacktestOptimizationSummaryResponse | null
  in_sample?: BacktestIterationSummaryResponse | null
  out_of_sample?: BacktestIterationSummaryResponse | null
  rolling_windows?: Array<BacktestRollingWindowResponse>
}

export interface BacktestResearchRequest {
  slippage_bps?: number
  funding_rate_daily?: number
  in_sample_ratio?: number
  optimize_metric?: "sharpe" | "profit_pct" | "calmar" | "profit_factor"
  optimize_trials?: number
  rolling_windows?: number
}

export interface BacktestRollingWindowResponse {
  index: number
  train?: BacktestDateRangeResponse | null
  test: BacktestDateRangeResponse
  config?: { [key: string]: string | number | boolean | Array<string | number | boolean | null> | { [key: string]: string | number | boolean | null } | Array<{ [key: string]: string | number | boolean | null }> | { [key: string]: Array<string | number | boolean | null> } | null }
  optimization?: BacktestOptimizationSummaryResponse | null
  report?: BacktestReportSnapshotResponse | null
}

export interface BacktestRunDefaultsResponse {
  strategy_key?: string
  timeframe?: string
  start_date?: string
  end_date?: string
  initial_cash?: number
  fee_rate?: number
  portfolio?: BacktestPortfolioRequest
  research?: BacktestResearchRequest
  history_mode?: "backtest" | "paper"
  optimize_metric_options?: Array<StrategyOperatorResponse>
}

export interface BacktestRunMetadataResponse {
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
  portfolio?: BacktestPortfolioPayloadResponse | null
  research?: BacktestResearchPayloadResponse | BacktestResearchReportResponse | null
  selected_config?: { [key: string]: string | number | boolean | Array<string | number | boolean | null> | { [key: string]: string | number | boolean | null } | Array<{ [key: string]: string | number | boolean | null }> | { [key: string]: Array<string | number | boolean | null> } | null }
  sample_ranges?: BacktestSampleRangesResponse | null
  runtime_state?: BacktestRuntimeStateResponse | null
  paper_live?: BacktestPaperLiveResponse | null
  report?: BacktestReportResponse | null
  raw_stats?: BacktestReportSnapshotResponse | null
  error?: string | null
}

export interface BacktestRuntimeStateResponse {
  cash_balance: number
  last_processed?: { [key: string]: number | null }
  last_synced_end?: number | null
  positions?: { [key: string]: BacktestPaperPositionResponse }
}

export interface BacktestSampleRangesResponse {
  requested?: BacktestDateRangeResponse | null
  displayed?: BacktestDateRangeResponse | null
  in_sample?: BacktestDateRangeResponse | null
  out_of_sample?: BacktestDateRangeResponse | null
}

export interface BacktestSignalResponse {
  id: number
  timestamp: string | null
  price: number
  signal: string
  confidence: number
  indicators?: { [key: string]: string | number | boolean | Array<string | number | boolean | null> | { [key: string]: string | number | boolean | null } | Array<{ [key: string]: string | number | boolean | null }> | { [key: string]: Array<string | number | boolean | null> } | null } | null
  reasoning?: string | null
}

export interface BacktestStrategySummaryResponse {
  key: string
  name: string
  version: number
  template: string
}

export interface BacktestTradeResponse {
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

export interface PaginationResponse {
  page: number
  page_size: number
  total: number
  total_pages: number
}

export interface StrategyConditionNodeResponse {
  id: string
  node_type?: string
  label: string
  left: StrategyRuleSourceResponse
  operator: "gt" | "gte" | "lt" | "lte"
  right: StrategyRuleSourceResponse
  enabled?: boolean
}

export interface StrategyExecutionConfigResponse {
  market_type?: "spot" | "futures"
  direction?: "long_only" | "long_short"
}

export interface StrategyGroupLogicResponse {
  key: string
  label: string
}

export interface StrategyGroupNodeResponse {
  id: string
  node_type?: string
  label: string
  logic: "and" | "or"
  enabled?: boolean
  children?: Array<StrategyConditionNodeResponse | StrategyGroupNodeResponse>
}

export interface StrategyIndicatorConfigResponse {
  label: string
  type: string
  timeframe?: string
  params?: { [key: string]: number | boolean }
}

export interface StrategyIndicatorOutputResponse {
  key: string
  label: string
}

export interface StrategyIndicatorParamResponse {
  key: string
  label: string
  type: "int" | "float" | "bool"
  default: number | boolean
  min?: number | null
  max?: number | null
  step?: number | null
}

export interface StrategyOperatorResponse {
  key: string
  label: string
}

export interface StrategyPartialExitResponse {
  id: string
  profit: number
  size_pct: number
  enabled?: boolean
}

export interface StrategyRiskConfigResponse {
  stoploss: number
  roi_targets?: Array<StrategyRoiTargetResponse>
  trailing: StrategyTrailingConfigResponse
  partial_exits?: Array<StrategyPartialExitResponse>
  trade_plan?: StrategyTradePlanConfigResponse
}

export interface StrategyRoiTargetResponse {
  id: string
  minutes: number
  profit: number
  enabled?: boolean
}

export interface StrategyRuleSourceResponse {
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

export interface StrategyRunProfileResponse {
  indicator_timeframes?: Array<string>
  allowed_run_timeframes?: Array<string>
  preferred_run_timeframe: string
}

export interface StrategyStateBranchResponse {
  id: string
  label: string
  enabled?: boolean
  regime: StrategyGroupNodeResponse
  long_entry: StrategyGroupNodeResponse
  long_exit: StrategyGroupNodeResponse
  short_entry: StrategyGroupNodeResponse
  short_exit: StrategyGroupNodeResponse
}

export interface StrategyTemplateCapabilitiesResponse {
  signal_runtime?: boolean
  paper?: boolean
  version_editing?: boolean
}

export interface StrategyTemplateConfigResponse {
  indicators?: { [key: string]: StrategyIndicatorConfigResponse }
  execution: StrategyExecutionConfigResponse
  regime_priority?: Array<"trend" | "range">
  trend: StrategyStateBranchResponse
  range: StrategyStateBranchResponse
  risk: StrategyRiskConfigResponse
}

export interface StrategyTemplateRuntimeResponse {
  builder_kind?: string
  capabilities?: StrategyTemplateCapabilitiesResponse
}

export interface StrategyTradePlanConfigResponse {
  enabled?: boolean
  stop_multiplier?: number
  min_stop_pct?: number
  reward_multiplier?: number
  atr_indicator?: string
  support_indicator?: string
  resistance_indicator?: string
}

export interface StrategyTrailingConfigResponse {
  enabled?: boolean
  positive: number
  offset: number
  only_offset_reached?: boolean
}
