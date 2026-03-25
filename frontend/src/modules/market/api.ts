import request from '@/api/request'
import type { AxiosResponse } from 'axios'
import type {
  RealtimeParams,
  RealtimeResponse,
  HistoryParams,
  FullHistoryParams,
  IndicatorParams,
  IndicatorItem,
  OHLCVRaw,
  CryptoIndexParams,
  CryptoIndexResponse,
} from '@/types'

export const marketApi = {
  getRealtime(params: RealtimeParams): Promise<AxiosResponse<RealtimeResponse>> {
    return request.get('/realtime', { params })
  },

  getIndicators(params: IndicatorParams): Promise<AxiosResponse<IndicatorItem[]>> {
    return request.get('/indicators', { params })
  },

  getHistory(params: HistoryParams): Promise<AxiosResponse<OHLCVRaw[]>> {
    return request.get('/history', { params })
  },

  getFullHistory(params: FullHistoryParams): Promise<AxiosResponse<OHLCVRaw[]>> {
    return request.get('/full_history', { params })
  },

  getCryptoIndex(params: CryptoIndexParams): Promise<AxiosResponse<CryptoIndexResponse>> {
    return request.get('/crypto_index', { params })
  },
}
