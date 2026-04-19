import request, { longTaskRequest } from '@/api/request'
import type { AxiosResponse } from 'axios'
import type {
  BacktestDetailResponse,
  BacktestDeleteResponse,
  BacktestRun,
  BacktestStartRequest,
  BacktestStartResponse,
  IndicatorDefinitionCreateRequest,
  PaperStartRequest,
  PaperStartResponse,
  PaperStopResponse,
  StrategyEditorContract,
  StrategyDefinition,
  StrategyIndicatorEngine,
  StrategyIndicatorRegistryItem,
  StrategyTemplate,
  StrategyTemplateCreateRequest,
  StrategyVersion,
  StrategyVersionCreateRequest,
} from './contracts'

export const backtestApi = {
  listRuns(): Promise<AxiosResponse<BacktestRun[]>> {
    return request.get('/backtest/list')
  },

  startRun(body: BacktestStartRequest): Promise<AxiosResponse<BacktestStartResponse>> {
    return longTaskRequest.post('/backtest/start', body)
  },

  listPaperRuns(): Promise<AxiosResponse<BacktestRun[]>> {
    return request.get('/paper/list')
  },

  startPaperRun(body: PaperStartRequest): Promise<AxiosResponse<PaperStartResponse>> {
    return request.post('/paper/start', body)
  },

  stopPaperRun(runId: number): Promise<AxiosResponse<PaperStopResponse>> {
    return request.post(`/paper/${runId}/stop`)
  },

  deleteRun(backtestId: number): Promise<AxiosResponse<BacktestDeleteResponse>> {
    return request.delete(`/backtest/${backtestId}`)
  },

  deletePaperRun(runId: number): Promise<AxiosResponse<BacktestDeleteResponse>> {
    return request.delete(`/paper/${runId}`)
  },

  listStrategies(): Promise<AxiosResponse<StrategyDefinition[]>> {
    return request.get('/backtest/strategies')
  },

  listTemplates(): Promise<AxiosResponse<StrategyTemplate[]>> {
    return request.get('/backtest/templates')
  },

  getEditorContract(): Promise<AxiosResponse<StrategyEditorContract>> {
    return request.get('/backtest/editor-contract')
  },

  createTemplate(body: StrategyTemplateCreateRequest): Promise<AxiosResponse<StrategyTemplate>> {
    return request.post('/backtest/templates', body)
  },

  listIndicators(): Promise<AxiosResponse<StrategyIndicatorRegistryItem[]>> {
    return request.get('/backtest/indicators')
  },

  listIndicatorEngines(): Promise<AxiosResponse<StrategyIndicatorEngine[]>> {
    return request.get('/backtest/indicator-engines')
  },

  createIndicator(body: IndicatorDefinitionCreateRequest): Promise<AxiosResponse<StrategyIndicatorRegistryItem>> {
    return request.post('/backtest/indicators', body)
  },

  createStrategyVersion(body: StrategyVersionCreateRequest): Promise<AxiosResponse<StrategyVersion>> {
    return request.post('/backtest/strategies', body)
  },

  getRun(backtestId: number, page: number = 1, pageSize: number = 100): Promise<AxiosResponse<BacktestDetailResponse>> {
    return request.get(`/backtest/${backtestId}`, {
      params: {
        page,
        page_size: pageSize,
      },
    })
  },

  getPaperRun(runId: number, page: number = 1, pageSize: number = 100): Promise<AxiosResponse<BacktestDetailResponse>> {
    return request.get(`/paper/${runId}`, {
      params: {
        page,
        page_size: pageSize,
      },
    })
  },
}
