import request, { longTaskRequest } from '@/api/request'
import { apiRoute } from '@/api/routes'
import type { AxiosResponse } from 'axios'
import type {
  FactorCatalogResponse,
  FactorExecutionRequest,
  FactorExecutionResponse,
  FactorResearchRequest,
  FactorResearchResponse,
  FactorResearchRun,
  FactorResearchRunDetail,
} from './contracts'

export const factorApi = {
  getCatalog(): Promise<AxiosResponse<FactorCatalogResponse>> {
    return request.get(apiRoute('get_factor_catalog'))
  },

  analyze(body: FactorResearchRequest): Promise<AxiosResponse<FactorResearchResponse>> {
    return longTaskRequest.post(apiRoute('analyze_factors'), body)
  },

  listRuns(limit: number = 20): Promise<AxiosResponse<FactorResearchRun[]>> {
    return request.get(apiRoute('list_factor_runs'), { params: { limit } })
  },

  getRun(runId: number): Promise<AxiosResponse<FactorResearchRunDetail>> {
    return request.get(apiRoute('get_factor_run', { run_id: runId }))
  },

  startBacktest(runId: number, body: FactorExecutionRequest): Promise<AxiosResponse<FactorExecutionResponse>> {
    return longTaskRequest.post(apiRoute('start_factor_backtest', { run_id: runId }), body)
  },

  startPaper(runId: number, body: FactorExecutionRequest): Promise<AxiosResponse<FactorExecutionResponse>> {
    return longTaskRequest.post(apiRoute('start_factor_paper_run', { run_id: runId }), body)
  },
}
