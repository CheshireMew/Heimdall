import { apiGet, apiPut } from '@/api/request'
import type { AxiosResponse } from 'axios'
import type {
  CurrencyRatesResponse,
  FredApiConfigResponse,
  FredApiConfigUpdateRequest,
  LlmProviderConfigResponse,
  LlmProviderConfigUpdateRequest,
  SystemConfigResponse,
} from './contracts'

export const systemApi = {
  getConfig(): Promise<AxiosResponse<SystemConfigResponse>> {
    return apiGet('get_config')
  },

  getCurrencyRates(): Promise<AxiosResponse<CurrencyRatesResponse>> {
    return apiGet('get_currencies')
  },

  getLlmConfig(): Promise<AxiosResponse<LlmProviderConfigResponse>> {
    return apiGet('get_llm_config')
  },

  updateLlmConfig(body: LlmProviderConfigUpdateRequest): Promise<AxiosResponse<LlmProviderConfigResponse>> {
    return apiPut('update_llm_config', body)
  },

  getFredApiConfig(): Promise<AxiosResponse<FredApiConfigResponse>> {
    return apiGet('get_fred_api_config')
  },

  updateFredApiConfig(body: FredApiConfigUpdateRequest): Promise<AxiosResponse<FredApiConfigResponse>> {
    return apiPut('update_fred_api_config', body)
  },
}
