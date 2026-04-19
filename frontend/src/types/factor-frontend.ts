import type {
  FactorBlendComponentResponse,
  FactorBlendResponse,
  FactorCatalogItemResponse,
  FactorDetailResponse,
  FactorDroppedComponentResponse,
  FactorForwardMetricResponse,
  FactorLagPointResponse,
  FactorNormalizedPointResponse,
  FactorQuantileBucketResponse,
  FactorResearchRunDetailResponse,
  FactorResearchSummaryResponse,
  FactorRollingPointResponse,
  FactorScorecardResponse,
} from './factor'

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
export type FactorResearchRun = Omit<FactorResearchRunDetailResponse, 'details'> & {
  details?: FactorResearchRunDetailResponse['details']
}
