// This file is generated from backend Pydantic schemas.
// Do not edit manually.

export interface FactorCatalogItem {
  factor_id: string
  name: string
  category: string
  source: string
  unit?: string | null
  feature_mode: string
  description?: string | null
}

export interface FactorCatalogResponse {
  symbols: Array<string>
  timeframes: Array<string>
  categories: Array<string>
  factors: Array<FactorCatalogItem>
  forward_horizons: Array<number>
  cleaning: { [key: string]: unknown }
}

export interface FactorResearchRequest {
  symbol?: string
  timeframe?: "1h" | "4h" | "1d"
  days?: number
  horizon_bars?: number
  max_lag_bars?: number
  categories?: Array<string>
  factor_ids?: Array<string>
}

export interface FactorForwardMetric {
  horizon: number
  sample_size: number
  target_mean?: number | null
  target_std?: number | null
  correlation: number
  rank_correlation: number
  ic_mean: number
  ic_std: number
  ic_ir: number
  ic_t_stat: number
  quantile_spread: number
  hit_rate: number
}

export interface FactorResearchSummary {
  symbol: string
  timeframe: string
  days: number
  horizon_bars: number
  max_lag_bars: number
  factor_count: number
  dataset_id: number
  forward_horizons: Array<number>
  sample_range: FactorSampleRange
  target_label: string
  blend_factor_count: number
}

export interface FactorScorecard {
  factor_id: string
  name: string
  category: string
  feature_mode: string
  sample_size: number
  latest_value: number
  correlation: number
  rank_correlation: number
  best_lag: number
  best_lag_correlation: number
  stability: number
  quantile_spread: number
  hit_rate: number
  turnover: number
  ic_ir: number
  direction: string
  score: number
}

export interface FactorLagPoint {
  lag: number
  correlation: number
}

export interface FactorRollingPoint {
  date: string
  value: number
}

export interface FactorQuantileBucket {
  bucket: number
  label: string
  avg_future_return: number
  count: number
}

export interface FactorNormalizedPoint {
  date: string
  price_z: number
  factor_z: number
  future_return: number
}

export interface FactorDetail {
  factor_id: string
  name: string
  category: string
  unit?: string | null
  feature_mode: string
  description?: string | null
  sample_range: FactorSampleRange
  sample_size: number
  latest_raw_value: number
  latest_feature_value: number
  target_mean: number
  target_std: number
  correlation: number
  rank_correlation: number
  best_lag: number
  best_lag_correlation: number
  stability: number
  quantile_spread: number
  hit_rate: number
  turnover: number
  ic_mean: number
  ic_std: number
  ic_ir: number
  ic_t_stat: number
  forward_metrics: Array<FactorForwardMetric>
  lag_profile: Array<FactorLagPoint>
  rolling_correlation: Array<FactorRollingPoint>
  quantiles: Array<FactorQuantileBucket>
  normalized_series: Array<FactorNormalizedPoint>
}

export interface FactorBlendComponent {
  factor_id: string
  name: string
  category: string
  score: number
  correlation: number
  stability: number
  turnover: number
  weight: number
}

export interface FactorDroppedComponent {
  factor_id: string
  name: string
  reason: string
}

export interface FactorBlend {
  selected_factors: Array<FactorBlendComponent>
  dropped_factors: Array<FactorDroppedComponent>
  weights: Array<FactorBlendComponent>
  forward_metrics: Array<FactorForwardMetric>
  quantiles: Array<FactorQuantileBucket>
  normalized_series: Array<FactorNormalizedPoint>
  entry_threshold: number
  exit_threshold: number
  score_std: number
  score_mean: number
}

export interface FactorResearchResponse {
  run_id: number
  dataset_id: number
  summary: FactorResearchSummary
  ranking: Array<FactorScorecard>
  details: Array<FactorDetail>
  blend: FactorBlend
}

export interface FactorResearchRun {
  id: number
  dataset_id: number
  status: string
  request: FactorResearchRequest
  summary: FactorResearchSummary
  ranking: Array<FactorScorecard>
  blend: FactorBlend
  error?: string | null
  created_at: string | null
  details?: Array<FactorDetail>
}

export interface FactorExecutionRequest {
  initial_cash?: number
  fee_rate?: number
  position_size_pct?: number
  stake_mode?: "fixed" | "unlimited"
  entry_threshold?: number | null
  exit_threshold?: number | null
  stoploss_pct?: number
  takeprofit_pct?: number
  max_hold_bars?: number
}

export interface FactorExecutionResponse {
  success: boolean
  run_id: number
  message: string
}

export interface FactorSampleRange {
  start: string
  end: string
}

