import request from '@/api/request'
import type { AxiosResponse } from 'axios'
import type {
  DCASimulationConfig,
  DCASimulationResponse,
  PairCompareParams,
  PairCompareResponse,
} from '@/types'

export const toolsApi = {
  runSimulation(config: DCASimulationConfig): Promise<AxiosResponse<DCASimulationResponse>> {
    return request.post('/tools/dca_simulate', config)
  },

  comparePairs(params: PairCompareParams): Promise<AxiosResponse<PairCompareResponse>> {
    return request.post('/tools/compare_pairs', params)
  },
}
