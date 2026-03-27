import request from '@/api/request'
import type { AxiosResponse } from 'axios'
import type {
  FactorCatalogResponse,
  FactorExecutionRequest,
  FactorExecutionResponse,
  FactorResearchRequest,
  FactorResearchResponse,
  FactorResearchRun,
} from '@/types'

export const factorApi = {
  getCatalog(): Promise<AxiosResponse<FactorCatalogResponse>> {
    return request.get('/factor-research/catalog')
  },

  analyze(body: FactorResearchRequest): Promise<AxiosResponse<FactorResearchResponse>> {
    return request.post('/factor-research/analyze', body)
  },

  listRuns(limit: number = 20): Promise<AxiosResponse<FactorResearchRun[]>> {
    return request.get('/factor-research/runs', { params: { limit } })
  },

  getRun(runId: number): Promise<AxiosResponse<FactorResearchRun>> {
    return request.get(`/factor-research/runs/${runId}`)
  },

  startBacktest(runId: number, body: FactorExecutionRequest): Promise<AxiosResponse<FactorExecutionResponse>> {
    return request.post(`/factor-research/runs/${runId}/backtest`, body)
  },

  startPaper(runId: number, body: FactorExecutionRequest): Promise<AxiosResponse<FactorExecutionResponse>> {
    return request.post(`/factor-research/runs/${runId}/paper`, body)
  },
}
