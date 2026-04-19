import type {
  FactorBlendComponentResponse,
  FactorBlendResponse,
  FactorCatalogItemResponse,
  FactorCatalogResponse,
  FactorDetailResponse,
  FactorDroppedComponentResponse,
  FactorExecutionRequest,
  FactorExecutionResponse,
  FactorForwardMetricResponse,
  FactorLagPointResponse,
  FactorNormalizedPointResponse,
  FactorQuantileBucketResponse,
  FactorResearchRequest,
  FactorResearchResponse,
  FactorResearchRunDetailResponse,
  FactorResearchRunListItemResponse,
  FactorResearchSummaryResponse,
  FactorRollingPointResponse,
  FactorScorecardResponse,
} from '@/types'

export type FactorCatalogItem = FactorCatalogItemResponse
export type FactorResearchSummary = FactorResearchSummaryResponse
export type FactorForwardMetric = FactorForwardMetricResponse
export type FactorScorecard = FactorScorecardResponse
export type FactorLagPoint = FactorLagPointResponse
export type FactorRollingPoint = FactorRollingPointResponse
export type FactorQuantileBucket = FactorQuantileBucketResponse
export type FactorNormalizedPoint = FactorNormalizedPointResponse
export type FactorDetail = FactorDetailResponse
export type FactorBlendComponent = FactorBlendComponentResponse
export type FactorDroppedComponent = FactorDroppedComponentResponse
export type FactorBlend = FactorBlendResponse
export type FactorResearchRun = FactorResearchRunListItemResponse
export type FactorResearchRunDetail = FactorResearchRunDetailResponse

export type {
  FactorCatalogResponse,
  FactorExecutionRequest,
  FactorExecutionResponse,
  FactorResearchRequest,
  FactorResearchResponse,
}
