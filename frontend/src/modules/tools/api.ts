import request from '@/api/request'
import type { AxiosResponse } from 'axios'
import type {
  DCARequestSchema,
  DCAResponse,
  PairCompareRequestSchema,
  PairCompareToolResponse,
} from '@/types'

export const toolsApi = {
  runSimulation(config: DCARequestSchema): Promise<AxiosResponse<DCAResponse>> {
    return request.post('/tools/dca_simulate', config)
  },

  comparePairs(params: PairCompareRequestSchema): Promise<AxiosResponse<PairCompareToolResponse>> {
    return request.post('/tools/compare_pairs', params)
  },
}
