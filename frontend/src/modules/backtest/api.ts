import request from '@/api/request'
import type { AxiosResponse } from 'axios'
import type {
  BacktestDetailResponse,
  BacktestRun,
  BacktestStartRequest,
  BacktestStartResponse,
  IndicatorDefinitionCreateRequest,
  StrategyEditorContract,
  StrategyDefinition,
  StrategyIndicatorEngine,
  StrategyIndicatorRegistryItem,
  StrategyTemplate,
  StrategyTemplateCreateRequest,
  StrategyVersion,
  StrategyVersionCreateRequest,
} from '@/types'

export const backtestApi = {
  listRuns(): Promise<AxiosResponse<BacktestRun[]>> {
    return request.get('/backtest/list')
  },

  startRun(body: BacktestStartRequest): Promise<AxiosResponse<BacktestStartResponse>> {
    return request.post('/backtest/start', body)
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
}
