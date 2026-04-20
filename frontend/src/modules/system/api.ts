import request from '@/api/request'
import { apiRoute } from '@/api/routes'
import type { AxiosResponse } from 'axios'
import type { CurrencyRatesResponse, LlmProviderConfigResponse, LlmProviderConfigUpdateRequest, SystemConfigResponse } from './contracts'

export const systemApi = {
  getConfig(): Promise<AxiosResponse<SystemConfigResponse>> {
    return request.get(apiRoute('get_config'))
  },

  getCurrencyRates(): Promise<AxiosResponse<CurrencyRatesResponse>> {
    return request.get(apiRoute('get_currencies'))
  },

  getLlmConfig(): Promise<AxiosResponse<LlmProviderConfigResponse>> {
    return request.get(apiRoute('get_llm_config'))
  },

  updateLlmConfig(body: LlmProviderConfigUpdateRequest): Promise<AxiosResponse<LlmProviderConfigResponse>> {
    return request.put(apiRoute('update_llm_config'), body)
  },
}
