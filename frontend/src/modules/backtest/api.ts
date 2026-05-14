import { apiDelete, apiGet, apiPost } from '@/api/request'
import type {
  BacktestDetailResponse,
  BacktestDeleteResponse,
  BacktestPreviewRequest,
  BacktestPreviewResponse,
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
  listRuns(): Promise<BacktestRunResponse[]> {
    return apiGet('list_backtests')
  },

  startRun(body: BacktestStartRequest): Promise<BacktestStartResponse> {
    return apiPost('start_backtest', body, { client: 'longTask' })
  },

  previewRun(body: BacktestPreviewRequest): Promise<BacktestPreviewResponse> {
    return apiPost('preview_backtest', body, { client: 'longTask' })
  },

  listPaperRuns(): Promise<BacktestRunResponse[]> {
    return apiGet('list_paper_runs')
  },

  startPaperRun(body: PaperStartRequest): Promise<PaperStartResponse> {
    return apiPost('start_paper_run', body, { client: 'longTask' })
  },

  stopPaperRun(runId: number): Promise<PaperStopResponse> {
    return apiPost('stop_paper_run', undefined, { path: { run_id: runId } })
  },

  deleteRun(backtestId: number): Promise<BacktestDeleteResponse> {
    return apiDelete('delete_backtest', { path: { backtest_id: backtestId } })
  },

  deletePaperRun(runId: number): Promise<BacktestDeleteResponse> {
    return apiDelete('delete_paper_run', { path: { run_id: runId } })
  },

  listStrategies(): Promise<StrategyDefinitionResponse[]> {
    return apiGet('list_strategies')
  },

  listTemplates(): Promise<StrategyTemplateResponse[]> {
    return apiGet('list_strategy_templates')
  },

  getEditorContract(): Promise<StrategyEditorContractResponse> {
    return apiGet('get_strategy_editor_contract')
  },

  createTemplate(body: StrategyTemplateCreateRequest): Promise<StrategyTemplateResponse> {
    return apiPost('create_strategy_template', body)
  },

  listIndicators(): Promise<StrategyIndicatorRegistryResponse[]> {
    return apiGet('list_indicators')
  },

  listIndicatorEngines(): Promise<StrategyIndicatorEngineResponse[]> {
    return apiGet('list_indicator_engines')
  },

  createIndicator(body: IndicatorDefinitionCreateRequest): Promise<StrategyIndicatorRegistryResponse> {
    return apiPost('create_indicator', body)
  },

  createStrategyVersion(body: StrategyVersionCreateRequest): Promise<StrategyVersionResponse> {
    return apiPost('create_strategy_version', body)
  },

  evolveStrategyFromBacktest(backtestId: number, body: StrategyEvolutionRequest): Promise<StrategyEvolutionResponse> {
    return apiPost('evolve_strategy_from_backtest', body, {
      client: 'longTask',
      path: { backtest_id: backtestId },
    })
  },

  getRun(backtestId: number, page: number = 1, pageSize: number = 100): Promise<BacktestDetailResponse> {
    return apiGet('get_backtest', {
      path: { backtest_id: backtestId },
      query: {
        page,
        page_size: pageSize,
      },
    })
  },

  getPaperRun(runId: number, page: number = 1, pageSize: number = 100): Promise<BacktestDetailResponse> {
    return apiGet('get_paper_run', {
      path: { run_id: runId },
      query: {
        page,
        page_size: pageSize,
      },
    })
  },
}


