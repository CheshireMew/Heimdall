// This file is generated from backend FastAPI route contracts.
// Do not edit manually.

export interface SystemConfigResponse {
  exchange: string
  symbols: Array<string>
  timeframe: string
  indicators: SystemIndicatorConfigResponse
  runtime: SystemRuntimeConfigResponse
}

export interface LlmProviderConfigResponse {
  provider: string
  apiKey?: string
  apiKeySet?: boolean
  apiKeyPreview?: string
  baseUrl: string
  modelId: string
  reasoningEnabled?: boolean
  presets?: Array<LlmProviderPresetResponse>
}

export interface LlmProviderConfigUpdateRequest {
  provider: string
  apiKey?: string | null
  baseUrl?: string
  modelId?: string
  reasoningEnabled?: boolean
}

export interface LlmProviderPresetResponse {
  id: string
  label: string
  baseUrl: string
  defaultModel: string
  supportsReasoning?: boolean
}

export interface SystemIndicatorConfigResponse {
  ema_period: number
  rsi_period: number
  macd_fast: number
  macd_slow: number
  macd_signal: number
}

export interface SystemRuntimeConfigResponse {
  app_role: string
  database_engine: string
  cache_backend: string
}
