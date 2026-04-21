import { apiDelete, apiGet, apiPost, longTaskRequest } from '@/api/request'
import { apiRoute } from '@/api/routes'
import type { AxiosResponse } from 'axios'
import type {
  BacktestDetailResponse,
  BacktestDeleteResponse,
  BacktestRunResponse,
  BacktestStartRequest,
  BacktestStartResponse,
  IndicatorDefinitionCreateRequest,
  PaperStartRequest,
  PaperStartResponse,
  PaperStopResponse,
  StrategyEditorContractResponse,
  StrategyDefinitionResponse,
  StrategyIndicatorEngineResponse,
  StrategyIndicatorRegistryResponse,
  StrategyTemplateResponse,
  StrategyTemplateCreateRequest,
  StrategyVersionResponse,
  StrategyVersionCreateRequest,
} from '../../types/backtest'

export const backtestApi = {
  listRuns(): Promise<AxiosResponse<BacktestRunResponse[]>> {
    return apiGet('list_backtests')
  },

  startRun(body: BacktestStartRequest): Promise<AxiosResponse<BacktestStartResponse>> {
    return longTaskRequest.post(apiRoute('start_backtest'), body)
  },

  listPaperRuns(): Promise<AxiosResponse<BacktestRunResponse[]>> {
    return apiGet('list_paper_runs')
  },

  startPaperRun(body: PaperStartRequest): Promise<AxiosResponse<PaperStartResponse>> {
    return longTaskRequest.post(apiRoute('start_paper_run'), body)
  },

  stopPaperRun(runId: number): Promise<AxiosResponse<PaperStopResponse>> {
    return apiPost('stop_paper_run', undefined, { path: { run_id: runId } })
  },

  deleteRun(backtestId: number): Promise<AxiosResponse<BacktestDeleteResponse>> {
    return apiDelete('delete_backtest', { path: { backtest_id: backtestId } })
  },

  deletePaperRun(runId: number): Promise<AxiosResponse<BacktestDeleteResponse>> {
    return apiDelete('delete_paper_run', { path: { run_id: runId } })
  },

  listStrategies(): Promise<AxiosResponse<StrategyDefinitionResponse[]>> {
    return apiGet('list_strategies')
  },

  listTemplates(): Promise<AxiosResponse<StrategyTemplateResponse[]>> {
    return apiGet('list_strategy_templates')
  },

  getEditorContract(): Promise<AxiosResponse<StrategyEditorContractResponse>> {
    return apiGet('get_strategy_editor_contract')
  },

  createTemplate(body: StrategyTemplateCreateRequest): Promise<AxiosResponse<StrategyTemplateResponse>> {
    return apiPost('create_strategy_template', body)
  },

  listIndicators(): Promise<AxiosResponse<StrategyIndicatorRegistryResponse[]>> {
    return apiGet('list_indicators')
  },

  listIndicatorEngines(): Promise<AxiosResponse<StrategyIndicatorEngineResponse[]>> {
    return apiGet('list_indicator_engines')
  },

  createIndicator(body: IndicatorDefinitionCreateRequest): Promise<AxiosResponse<StrategyIndicatorRegistryResponse>> {
    return apiPost('create_indicator', body)
  },

  createStrategyVersion(body: StrategyVersionCreateRequest): Promise<AxiosResponse<StrategyVersionResponse>> {
    return apiPost('create_strategy_version', body)
  },

  getRun(backtestId: number, page: number = 1, pageSize: number = 100): Promise<AxiosResponse<BacktestDetailResponse>> {
    return apiGet('get_backtest', {
      path: { backtest_id: backtestId },
      query: {
        page,
        page_size: pageSize,
      },
    })
  },

  getPaperRun(runId: number, page: number = 1, pageSize: number = 100): Promise<AxiosResponse<BacktestDetailResponse>> {
    return apiGet('get_paper_run', {
      path: { run_id: runId },
      query: {
        page,
        page_size: pageSize,
      },
    })
  },
}
