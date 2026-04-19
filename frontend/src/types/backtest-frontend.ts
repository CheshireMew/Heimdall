import type {
  BacktestDateRangeResponse,
  BacktestEquityPointResponse,
  BacktestIterationSummaryResponse,
  BacktestMetricsResponse,
  BacktestOptimizationSummaryResponse,
  BacktestOptimizationTrialResponse,
  BacktestPairBreakdownResponse,
  BacktestPaperLiveResponse,
  BacktestPaperPositionResponse,
  BacktestPortfolioPayloadResponse,
  BacktestPortfolioRequest,
  BacktestPortfolioSummaryResponse,
  BacktestReportResponse,
  BacktestReportSnapshotResponse,
  BacktestResearchPayloadResponse,
  BacktestResearchReportResponse,
  BacktestResearchRequest,
  BacktestRollingWindowResponse,
  BacktestRunMetadataResponse,
  BacktestRunDefaultsResponse,
  BacktestRunResponse,
  BacktestRuntimeStateResponse,
  BacktestSampleRangesResponse,
  BacktestSignalResponse,
  BacktestStrategySummaryResponse,
  BacktestTradeResponse,
  PaginationResponse,
  StrategyDefinitionResponse,
  StrategyEditorContractResponse,
  StrategyExecutionConfigResponse,
  StrategyConditionNodeResponse,
  StrategyGroupLogicResponse,
  StrategyGroupNodeResponse,
  StrategyIndicatorConfigResponse,
  StrategyIndicatorEngineResponse,
  StrategyIndicatorOutputResponse,
  StrategyIndicatorParamResponse,
  StrategyIndicatorRegistryResponse,
  StrategyOperatorResponse,
  StrategyPartialExitResponse,
  StrategyRiskConfigResponse,
  StrategyRoiTargetResponse,
  StrategyRuleSourceResponse,
  StrategyStateBranchResponse,
  StrategyTemplateCapabilitiesResponse,
  StrategyTemplateConfigResponse,
  StrategyTemplateResponse,
  StrategyTemplateRuntimeResponse,
  StrategyTrailingConfigResponse,
  StrategyVersionResponse,
} from './backtest'

export type BacktestPortfolioConfig = BacktestPortfolioRequest
export type BacktestResearchConfig = BacktestResearchRequest
export type BacktestMetrics = BacktestMetricsResponse
export type BacktestSignal = BacktestSignalResponse
export type BacktestTrade = BacktestTradeResponse
export type BacktestEquityPoint = BacktestEquityPointResponse
export type BacktestPagination = PaginationResponse
export type BacktestRun = BacktestRunResponse
export type BacktestRunDefaults = BacktestRunDefaultsResponse
export type BacktestRunMetadata = BacktestRunMetadataResponse
export type BacktestReport = BacktestReportResponse
export type BacktestReportSnapshot = BacktestReportSnapshotResponse
export type BacktestDateRange = BacktestDateRangeResponse
export type BacktestPairBreakdown = BacktestPairBreakdownResponse
export type BacktestStrategySummary = BacktestStrategySummaryResponse
export type BacktestPortfolioSummary = BacktestPortfolioSummaryResponse
export type BacktestPortfolioPayload = BacktestPortfolioPayloadResponse
export type BacktestResearchPayload = BacktestResearchPayloadResponse
export type BacktestOptimizationTrial = BacktestOptimizationTrialResponse
export type BacktestOptimizationSummary = BacktestOptimizationSummaryResponse
export type BacktestIterationSummary = BacktestIterationSummaryResponse
export type BacktestRollingWindow = BacktestRollingWindowResponse
export type BacktestResearchReport = BacktestResearchReportResponse
export type BacktestSampleRanges = BacktestSampleRangesResponse
export type BacktestPaperPosition = BacktestPaperPositionResponse
export type BacktestRuntimeState = BacktestRuntimeStateResponse
export type BacktestPaperLive = BacktestPaperLiveResponse
export type StrategyVersion = StrategyVersionResponse
export type StrategyDefinition = StrategyDefinitionResponse
export type StrategyIndicatorRegistryItem = StrategyIndicatorRegistryResponse
export type StrategyOperator = StrategyOperatorResponse
export type StrategyTemplateCapabilities = StrategyTemplateCapabilitiesResponse
export type StrategyTemplateRuntime = StrategyTemplateRuntimeResponse
export type StrategyGroupLogic = StrategyGroupLogicResponse
export type StrategyIndicatorEngine = StrategyIndicatorEngineResponse
export type StrategyTemplate = StrategyTemplateResponse
export type StrategyEditorContract = StrategyEditorContractResponse
export type StrategyRuleSource = StrategyRuleSourceResponse
export type StrategyStateBranch = StrategyStateBranchResponse
export type StrategyIndicatorConfig = StrategyIndicatorConfigResponse
export type StrategyExecutionConfig = StrategyExecutionConfigResponse
export type StrategyIndicatorOutput = StrategyIndicatorOutputResponse
export type StrategyIndicatorParam = StrategyIndicatorParamResponse
export type StrategyRoiTarget = StrategyRoiTargetResponse
export type StrategyPartialExit = StrategyPartialExitResponse
export type StrategyTrailingConfig = StrategyTrailingConfigResponse
export type StrategyRiskConfig = StrategyRiskConfigResponse
export type StrategyTemplateConfig = StrategyTemplateConfigResponse
export type StrategyConditionNode = StrategyConditionNodeResponse
export type StrategyGroupNode = Omit<StrategyGroupNodeResponse, 'children'> & {
  children?: StrategyRuleNode[]
}
export type StrategyRuleNode = StrategyConditionNode | StrategyGroupNode

export type EditableStrategyTemplateConfig = Omit<StrategyTemplateConfig, 'indicators' | 'risk'> & {
  indicators: Record<string, StrategyIndicatorConfig>
  risk: Omit<StrategyRiskConfig, 'roi_targets' | 'partial_exits'> & {
    roi_targets: StrategyRoiTarget[]
    partial_exits: StrategyPartialExit[]
  }
}

export const isStrategyConditionNode = (node: StrategyRuleNode | null | undefined): node is StrategyConditionNode => (
  node?.node_type === 'condition'
)

export const isStrategyGroupNode = (node: StrategyRuleNode | null | undefined): node is StrategyGroupNode => (
  node?.node_type === 'group'
)
