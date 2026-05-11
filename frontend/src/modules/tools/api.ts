import { apiGet, apiPost } from '@/api/request'
import type {
  DCARequestSchema,
  DCAResponse,
  PairCompareRequestSchema,
  PairCompareToolResponse,
  ToolsPageContractResponse,
} from './contracts'

export const toolsApi = {
  getContract(): Promise<ToolsPageContractResponse> {
    return apiGet('get_tools_contract')
  },

  runSimulation(config: DCARequestSchema): Promise<DCAResponse> {
    return apiPost('dca_simulate', config)
  },

  comparePairs(params: PairCompareRequestSchema): Promise<PairCompareToolResponse> {
    return apiPost('compare_pairs', params)
  },
}


