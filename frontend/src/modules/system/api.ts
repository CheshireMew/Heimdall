import request from '@/api/request'
import type { AxiosResponse } from 'axios'
import type { CurrencyRatesResponse, LlmProviderConfigResponse, LlmProviderConfigUpdateRequest, SystemConfigResponse } from '@/types'

export const systemApi = {
  getConfig(): Promise<AxiosResponse<SystemConfigResponse>> {
    return request.get('/config')
  },

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
