import request from '@/api/request'
import type { AxiosResponse } from 'axios'
import type { CurrencyRatesResponse } from '@/types'

export interface LlmProviderPreset {
  id: string
  label: string
  baseUrl: string
  defaultModel: string
  supportsReasoning: boolean
}

export interface LlmProviderConfigResponse {
  provider: string
  apiKey: string
  apiKeySet: boolean
  apiKeyPreview: string
  baseUrl: string
  modelId: string
  reasoningEnabled: boolean
  presets: LlmProviderPreset[]
}

export interface LlmProviderConfigUpdateRequest {
  provider: string
  apiKey: string | null
  baseUrl: string
  modelId: string
  reasoningEnabled: boolean
}

export const systemApi = {
  getCurrencyRates(): Promise<AxiosResponse<CurrencyRatesResponse>> {
    return request.get('/currencies')
  },

  getLlmConfig(): Promise<AxiosResponse<LlmProviderConfigResponse>> {
    return request.get('/llm-config')
  },

  updateLlmConfig(body: LlmProviderConfigUpdateRequest): Promise<AxiosResponse<LlmProviderConfigResponse>> {
    return request.put('/llm-config', body)
  },
}
