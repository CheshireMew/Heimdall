// This file is generated from backend FastAPI route contracts.
// Do not edit manually.

export interface SystemConfigResponse {
  exchange: string
  symbols: Array<string>
  timeframe: string
  indicators: SystemIndicatorConfigResponse
  runtime: SystemRuntimeConfigResponse
}

export interface CurrencyRatesResponse {
  base: string
  rates: { [key: string]: number }
  supported: Array<DisplayCurrencyResponse>
  updated_at: string
  source: string
  is_fallback?: boolean
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

export interface DisplayCurrencyResponse {
  code: string
  name: string
  symbol: string
  locale: string
  fraction_digits: number
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
