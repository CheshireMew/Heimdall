import { apiGet, longTaskRequest } from '@/api/request'
import { apiRoute } from '@/api/routes'
import type { AxiosResponse } from 'axios'
import type {
  FactorCatalogResponse,
  FactorResearchContractResponse,
  FactorExecutionRequest,
  FactorExecutionResponse,
  FactorResearchRequest,
  FactorResearchResponse,
  FactorResearchRunDetailResponse,
  FactorResearchRunListItemResponse,
} from '../../types/factor'

export const factorApi = {
  getContract(): Promise<AxiosResponse<FactorResearchContractResponse>> {
    return apiGet('get_factor_contract')
  },

  getCatalog(): Promise<AxiosResponse<FactorCatalogResponse>> {
    return apiGet('get_factor_catalog')
  },

  analyze(body: FactorResearchRequest): Promise<AxiosResponse<FactorResearchResponse>> {
    return longTaskRequest.post(apiRoute('analyze_factors'), body)
  },

  listRuns(limit: number = 20): Promise<AxiosResponse<FactorResearchRunListItemResponse[]>> {
    return apiGet('list_factor_runs', { query: { limit } })
  },

  getRun(runId: number): Promise<AxiosResponse<FactorResearchRunDetailResponse>> {
    return apiGet('get_factor_run', { path: { run_id: runId } })
  },

  startBacktest(runId: number, body: FactorExecutionRequest): Promise<AxiosResponse<FactorExecutionResponse>> {
    return longTaskRequest.post(apiRoute('start_factor_backtest', { run_id: runId }), body)
  },

  startPaper(runId: number, body: FactorExecutionRequest): Promise<AxiosResponse<FactorExecutionResponse>> {
    return longTaskRequest.post(apiRoute('start_factor_paper_run', { run_id: runId }), body)
  },
}
