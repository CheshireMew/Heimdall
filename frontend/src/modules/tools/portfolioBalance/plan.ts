import type {
  PortfolioBalanceAssetInput,
  PortfolioBalancePlan,
  PortfolioBalanceStrategyConfig,
  PortfolioBalanceTrackingConfig,
  PortfolioSuggestedAction,
  PortfolioSuggestedReason,
  PortfolioReviewFrequency,
} from '@/types'

import {
  buildNormalizedPortfolioWeights,
  computePortfolioAssetHoldingValue,
  normalizePortfolioBalanceAsset,
} from './model'
import { clamp, diffDaysFromToday, parseIsoDate, PERCENT_BASE, round, shiftReviewDate, todayIso } from './shared'

const decideSuggestedAction = (args: {
  hasAssets: boolean
  capitalIncrease: number
  minTradeAmount: number
  reviewDue: boolean
  outOfBandCount: number
  projectedOutOfBandCount: number
  turnoverAmount: number
}): { action: PortfolioSuggestedAction; reason: PortfolioSuggestedReason } => {
  if (!args.hasAssets) return { action: 'wait', reason: 'below_threshold' }
  if (args.outOfBandCount === 0 && !args.reviewDue) return { action: 'wait', reason: 'on_track' }
  if (args.capitalIncrease >= args.minTradeAmount && args.projectedOutOfBandCount < args.outOfBandCount) {
    return { action: 'cashflow', reason: args.outOfBandCount > 0 ? 'cashflow_first' : 'scheduled_review' }
  }
  if (args.turnoverAmount >= args.minTradeAmount) {
    return { action: 'full', reason: args.outOfBandCount > 0 ? 'full_rebalance' : 'scheduled_review' }
  }
  if (args.reviewDue) return { action: 'wait', reason: 'below_threshold' }
  return { action: 'wait', reason: args.outOfBandCount > 0 ? 'band_breach' : 'below_threshold' }
}

const resolveReviewSchedule = (
  inceptionDateText: string,
  frequency: PortfolioReviewFrequency,
) => {
  const todayText = todayIso()
  const inceptionDate = parseIsoDate(inceptionDateText)
  const todayDate = parseIsoDate(todayText)
  if (!inceptionDate || !todayDate) {
    return {
      reviewDue: false,
      nextReviewDate: todayText,
      daysUntilReview: 0,
    }
  }

  let currentAnchor = inceptionDateText
  let nextReviewDate = shiftReviewDate(currentAnchor, frequency)
  while ((parseIsoDate(nextReviewDate)?.getTime() || 0) <= todayDate.getTime()) {
    currentAnchor = nextReviewDate
    nextReviewDate = shiftReviewDate(currentAnchor, frequency)
  }

  return {
    reviewDue: currentAnchor === todayText,
    nextReviewDate,
    daysUntilReview: diffDaysFromToday(nextReviewDate),
  }
}

export const computePortfolioBalancePlan = (
  rawAssets: PortfolioBalanceAssetInput[],
  strategy: PortfolioBalanceStrategyConfig,
  tracking: PortfolioBalanceTrackingConfig,
): PortfolioBalancePlan => {
  const assets = rawAssets
    .map(normalizePortfolioBalanceAsset)
    .filter((asset) => asset.symbol || asset.targetWeight > 0 || asset.units > 0 || asset.currentPrice > 0)

  const { normalizedWeights, targetWeightInputSum, usesEqualWeightFallback } = buildNormalizedPortfolioWeights(assets)
  const assetValues = assets.map((asset) => round(computePortfolioAssetHoldingValue(asset), 2))
  const totalValue = round(assetValues.reduce((sum, value) => sum + value, 0), 2)
  const trackingCapital = round(tracking.virtualCapital, 2)
  const targetTotalValue = totalValue > 0 ? totalValue : trackingCapital
  const rebalanceBand = clamp(strategy.rebalanceBand / PERCENT_BASE, 0, 1)

  const draftAssets = assets.map((asset, index) => {
    const currentValue = assetValues[index] || 0
    const normalizedTargetWeight = normalizedWeights[index] || 0
    const currentWeight = totalValue > 0 ? currentValue / totalValue : 0
    const targetValue = targetTotalValue * normalizedTargetWeight
    const driftValue = targetValue - currentValue
    const driftWeight = normalizedTargetWeight - currentWeight
    const rebalanceAmount = Math.abs(driftValue) >= strategy.minTradeAmount ? driftValue : 0
    const rebalanceUnits = asset.currentPrice > 0 ? rebalanceAmount / asset.currentPrice : 0
    const bandLowerWeight = clamp(normalizedTargetWeight - rebalanceBand, 0, 1)
    const bandUpperWeight = clamp(normalizedTargetWeight + rebalanceBand, 0, 1)

    return {
      id: asset.id,
      symbol: asset.symbol || `Asset ${index + 1}`,
      units: round(asset.units, 8),
      seedValue: round(asset.seedValue, 2),
      currentValue,
      trackingDiffValue: round(currentValue - asset.seedValue, 2),
      price: round(asset.currentPrice, 4),
      currentWeight,
      normalizedTargetWeight,
      targetValue: round(targetValue, 2),
      driftValue: round(driftValue, 2),
      driftWeight,
      rebalanceAmount: round(rebalanceAmount, 2),
      rebalanceUnits: round(rebalanceUnits, 6),
      primaryAction: rebalanceAmount > 0 ? 'buy' : rebalanceAmount < 0 ? 'sell' : 'hold',
      bandLowerWeight,
      bandUpperWeight,
      bandLowerValue: round(totalValue * bandLowerWeight, 2),
      bandUpperValue: round(totalValue * bandUpperWeight, 2),
      isOutOfBand: currentWeight < bandLowerWeight || currentWeight > bandUpperWeight,
      cashflowAmount: 0,
      projectedValue: currentValue,
      projectedWeight: currentWeight,
      projectedIsOutOfBand: currentWeight < bandLowerWeight || currentWeight > bandUpperWeight,
    }
  })

  const projectedTotalValue = targetTotalValue
  const assetsWithProjection = draftAssets.map((asset) => {
    const cashflowAmount = round(asset.rebalanceAmount, 2)
    const projectedValue = round(asset.currentValue + cashflowAmount, 2)
    const projectedWeight = projectedTotalValue > 0 ? projectedValue / projectedTotalValue : 0
    return {
      ...asset,
      cashflowAmount,
      projectedValue,
      projectedWeight,
      projectedIsOutOfBand: projectedWeight < asset.bandLowerWeight || projectedWeight > asset.bandUpperWeight,
    }
  })

  const totalBuyAmount = round(assetsWithProjection.reduce((sum, asset) => sum + Math.max(asset.rebalanceAmount, 0), 0), 2)
  const totalSellAmount = round(assetsWithProjection.reduce((sum, asset) => sum + Math.max(-asset.rebalanceAmount, 0), 0), 2)
  const maxDriftWeight = assetsWithProjection.reduce((maxValue, asset) => Math.max(maxValue, Math.abs(asset.driftWeight)), 0)
  const outOfBandCount = assetsWithProjection.filter((asset) => asset.isOutOfBand).length
  const projectedOutOfBandCount = assetsWithProjection.filter((asset) => asset.projectedIsOutOfBand).length
  const { reviewDue, nextReviewDate, daysUntilReview } = resolveReviewSchedule(
    tracking.inceptionDate,
    strategy.reviewFrequency,
  )

  const suggestion = decideSuggestedAction({
    hasAssets: assetsWithProjection.length > 0,
    capitalIncrease: Math.max(targetTotalValue - totalValue, 0),
    minTradeAmount: strategy.minTradeAmount,
    reviewDue,
    outOfBandCount,
    projectedOutOfBandCount,
    turnoverAmount: round(totalBuyAmount + totalSellAmount, 2),
  })

  return {
    totalValue,
    trackingCapital,
    targetWeightInputSum: round(targetWeightInputSum, 2),
    usesEqualWeightFallback,
    totalBuyAmount,
    totalSellAmount,
    turnoverAmount: round(totalBuyAmount + totalSellAmount, 2),
    maxDriftWeight: round(maxDriftWeight * PERCENT_BASE, 2),
    outOfBandCount,
    projectedOutOfBandCount,
    reviewDue,
    shouldReviewNow: reviewDue || outOfBandCount > 0,
    reviewFrequency: strategy.reviewFrequency,
    nextReviewDate,
    daysUntilReview,
    suggestedAction: suggestion.action,
    suggestedReason: suggestion.reason,
    assets: assetsWithProjection,
  }
}
