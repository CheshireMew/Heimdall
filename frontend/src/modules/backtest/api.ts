import request, { longTaskRequest } from '@/api/request'
import { apiRoute } from '@/api/routes'
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
    return request.get(apiRoute('list_backtests'))
  },

  startRun(body: BacktestStartRequest): Promise<AxiosResponse<BacktestStartResponse>> {
    return longTaskRequest.post(apiRoute('start_backtest'), body)
  },

  listPaperRuns(): Promise<AxiosResponse<BacktestRun[]>> {
    return request.get(apiRoute('list_paper_runs'))
  },

  startPaperRun(body: PaperStartRequest): Promise<AxiosResponse<PaperStartResponse>> {
    return longTaskRequest.post(apiRoute('start_paper_run'), body)
  },

  stopPaperRun(runId: number): Promise<AxiosResponse<PaperStopResponse>> {
    return request.post(apiRoute('stop_paper_run', { run_id: runId }))
  },

  deleteRun(backtestId: number): Promise<AxiosResponse<BacktestDeleteResponse>> {
    return request.delete(apiRoute('delete_backtest', { backtest_id: backtestId }))
  },

  deletePaperRun(runId: number): Promise<AxiosResponse<BacktestDeleteResponse>> {
    return request.delete(apiRoute('delete_paper_run', { run_id: runId }))
  },

  listStrategies(): Promise<AxiosResponse<StrategyDefinition[]>> {
    return request.get(apiRoute('list_strategies'))
  },

  listTemplates(): Promise<AxiosResponse<StrategyTemplate[]>> {
    return request.get(apiRoute('list_strategy_templates'))
  },

  getEditorContract(): Promise<AxiosResponse<StrategyEditorContract>> {
    return request.get(apiRoute('get_strategy_editor_contract'))
  },

  createTemplate(body: StrategyTemplateCreateRequest): Promise<AxiosResponse<StrategyTemplate>> {
    return request.post(apiRoute('create_strategy_template'), body)
  },

  listIndicators(): Promise<AxiosResponse<StrategyIndicatorRegistryItem[]>> {
    return request.get(apiRoute('list_indicators'))
  },

  listIndicatorEngines(): Promise<AxiosResponse<StrategyIndicatorEngine[]>> {
    return request.get(apiRoute('list_indicator_engines'))
  },

  createIndicator(body: IndicatorDefinitionCreateRequest): Promise<AxiosResponse<StrategyIndicatorRegistryItem>> {
    return request.post(apiRoute('create_indicator'), body)
  },

  createStrategyVersion(body: StrategyVersionCreateRequest): Promise<AxiosResponse<StrategyVersion>> {
    return request.post(apiRoute('create_strategy_version'), body)
  },

  getRun(backtestId: number, page: number = 1, pageSize: number = 100): Promise<AxiosResponse<BacktestDetailResponse>> {
    return request.get(apiRoute('get_backtest', { backtest_id: backtestId }), {
      params: {
        page,
        page_size: pageSize,
      },
    })
  },

  getPaperRun(runId: number, page: number = 1, pageSize: number = 100): Promise<AxiosResponse<BacktestDetailResponse>> {
    return request.get(apiRoute('get_paper_run', { run_id: runId }), {
      params: {
        page,
        page_size: pageSize,
      },
    })
  },
}
