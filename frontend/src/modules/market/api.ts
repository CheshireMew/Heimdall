import request from '@/api/request'
import type { AxiosResponse } from 'axios'
import type {
  RealtimeParams,
  RealtimeResponse,
  HistoryParams,
  LatestKlineParams,
  FullHistoryParams,
  BatchFullHistoryParams,
  BatchFullHistoryResponse,
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

  getLatestKlines(params: LatestKlineParams): Promise<AxiosResponse<OHLCVRaw[]>> {
    return request.get('/klines/latest', { params })
  },

  getFullHistory(params: FullHistoryParams): Promise<AxiosResponse<OHLCVRaw[]>> {
    return request.get('/full_history', { params })
  },

  getBatchFullHistory(params: BatchFullHistoryParams): Promise<AxiosResponse<BatchFullHistoryResponse>> {
    const query = new URLSearchParams()
    params.symbols.forEach((symbol) => {
      query.append('symbols', symbol)
    })
    if (params.timeframe) query.set('timeframe', params.timeframe)
    if (params.start_date) query.set('start_date', params.start_date)
    return request.get(`/full_history/batch?${query.toString()}`)
  },

  getCryptoIndex(params: CryptoIndexParams): Promise<AxiosResponse<CryptoIndexResponse>> {
    return request.get('/crypto_index', { params })
  },
}
