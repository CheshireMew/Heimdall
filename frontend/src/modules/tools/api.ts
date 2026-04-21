import { apiGet, apiPost } from '@/api/request'
import type { AxiosResponse } from 'axios'
import type {
  DCARequestSchema,
  DCAResponse,
  PairCompareRequestSchema,
  PairCompareToolResponse,
  ToolsPageContractResponse,
} from '../../types/tools'

export const toolsApi = {
  getContract(): Promise<AxiosResponse<ToolsPageContractResponse>> {
    return apiGet('get_tools_contract')
  },

  runSimulation(config: DCARequestSchema): Promise<AxiosResponse<DCAResponse>> {
    return apiPost('dca_simulate', config)
  },

  comparePairs(params: PairCompareRequestSchema): Promise<AxiosResponse<PairCompareToolResponse>> {
    return apiPost('compare_pairs', params)
  },
}
