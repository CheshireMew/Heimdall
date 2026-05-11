import { apiGet, apiPut } from '@/api/request'
import type {
  CurrencyRatesResponse,
  FredApiConfigResponse,
  FredApiConfigUpdateRequest,
  LlmProviderConfigResponse,
  LlmProviderConfigUpdateRequest,
  SystemConfigResponse,
} from './contracts'

export const systemApi = {
  getConfig(): Promise<SystemConfigResponse> {
    return apiGet('get_config')
  },

  getCurrencyRates(): Promise<CurrencyRatesResponse> {
    return apiGet('get_currencies')
  },

  getLlmConfig(): Promise<LlmProviderConfigResponse> {
    return apiGet('get_llm_config')
  },

  updateLlmConfig(body: LlmProviderConfigUpdateRequest): Promise<LlmProviderConfigResponse> {
    return apiPut('update_llm_config', body)
  },

  getFredApiConfig(): Promise<FredApiConfigResponse> {
    return apiGet('get_fred_api_config')
  },

  updateFredApiConfig(body: FredApiConfigUpdateRequest): Promise<FredApiConfigResponse> {
    return apiPut('update_fred_api_config', body)
  },
}


