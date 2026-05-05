import { apiDelete, apiGet, apiPost } from '@/api/request'
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
  StrategyEvolutionRequest,
  StrategyEvolutionResponse,
  StrategyDefinitionResponse,
  StrategyIndicatorEngineResponse,
  StrategyIndicatorRegistryResponse,
  StrategyTemplateResponse,
  StrategyTemplateCreateRequest,
  StrategyVersionResponse,
  StrategyVersionCreateRequest,
} from './contracts'

export const backtestApi = {
  listRuns(): Promise<AxiosResponse<BacktestRunResponse[]>> {
    return apiGet('list_backtests')
  },

  startRun(body: BacktestStartRequest): Promise<AxiosResponse<BacktestStartResponse>> {
    return apiPost('start_backtest', body, { client: 'longTask' })
  },

  listPaperRuns(): Promise<AxiosResponse<BacktestRunResponse[]>> {
    return apiGet('list_paper_runs')
  },

  startPaperRun(body: PaperStartRequest): Promise<AxiosResponse<PaperStartResponse>> {
    return apiPost('start_paper_run', body, { client: 'longTask' })
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

  evolveStrategyFromBacktest(backtestId: number, body: StrategyEvolutionRequest): Promise<AxiosResponse<StrategyEvolutionResponse>> {
    return apiPost('evolve_strategy_from_backtest', body, {
      client: 'longTask',
      path: { backtest_id: backtestId },
    })
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
