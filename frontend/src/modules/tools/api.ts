import request from '@/api/request'
import { apiRoute } from '@/api/routes'
import type { AxiosResponse } from 'axios'
import type {
  DCARequestSchema,
  DCAResponse,
  PairCompareRequestSchema,
  PairCompareToolResponse,
} from './contracts'

export const toolsApi = {
  runSimulation(config: DCARequestSchema): Promise<AxiosResponse<DCAResponse>> {
    return request.post(apiRoute('dca_simulate'), config)
  },

  comparePairs(params: PairCompareRequestSchema): Promise<AxiosResponse<PairCompareToolResponse>> {
    return request.post(apiRoute('compare_pairs'), params)
  },
}
