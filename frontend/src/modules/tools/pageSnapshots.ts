import { isRecord, readNumber, readString } from '@/composables/pageSnapshot'

import type { DCARequestSchema, ToolsPageContractResponse } from '../../types/tools'

export interface DcaPageSnapshot {
  config: DcaPageConfig
}

export type DcaStrategyValue = NonNullable<DCARequestSchema['strategy']> | ''

export type DcaPageConfig = Required<Pick<DCARequestSchema, 'symbol' | 'amount' | 'investment_time' | 'timezone'>> & {
  start_date: string
  strategy: DcaStrategyValue
  strategy_params: {
    multiplier: number
  }
}

export interface ComparePageSnapshot {
  config: {
    symbolA: string
    symbolB: string
    days: number
    timeframe: string
  }
}

export const createEmptyDcaConfig = (): DcaPageConfig => ({
  symbol: '',
  amount: 0,
  start_date: '',
  investment_time: '',
  timezone: '',
  strategy: '',
  strategy_params: {
    multiplier: 0,
  },
})

export const createDefaultDcaConfig = (contract: ToolsPageContractResponse): DcaPageConfig => ({
  symbol: contract.dca_defaults.symbol || '',
  amount: contract.dca_defaults.amount ?? 0,
  start_date: contract.dca_defaults.start_date || '',
  investment_time: contract.dca_defaults.investment_time || '',
  timezone: contract.dca_defaults.timezone || '',
  strategy: contract.dca_defaults.strategy || '',
  strategy_params: {
    multiplier: contract.dca_multiplier_default,
  },
})

export const normalizeDcaConfig = (
  value: unknown,
  fallback = createEmptyDcaConfig(),
  strategyKeys: readonly string[] = [],
): DcaPageConfig => {
  const defaults = fallback
  if (!isRecord(value)) return defaults

  const strategyParams = isRecord(value.strategy_params) ? value.strategy_params : {}
  const strategy = readString(value.strategy, defaults.strategy)
  const resolvedStrategy = strategyKeys.length > 0
    ? (strategyKeys.includes(strategy) ? strategy : defaults.strategy)
    : strategy

  return {
    symbol: readString(value.symbol, defaults.symbol),
    amount: readNumber(value.amount, defaults.amount),
    start_date: readString(value.start_date, defaults.start_date),
    investment_time: readString(value.investment_time, defaults.investment_time),
    timezone: readString(value.timezone, defaults.timezone),
    strategy: resolvedStrategy as DcaPageConfig['strategy'],
    strategy_params: {
      multiplier: readNumber(strategyParams.multiplier, defaults.strategy_params.multiplier),
    },
  }
}

export const createEmptyDcaSnapshot = (): DcaPageSnapshot => ({
  config: createEmptyDcaConfig(),
})

export const createDefaultDcaSnapshot = (contract: ToolsPageContractResponse): DcaPageSnapshot => ({
  config: createDefaultDcaConfig(contract),
})

export const normalizeDcaSnapshot = (
  value: unknown,
  fallback = createEmptyDcaSnapshot(),
  strategyKeys: readonly string[] = [],
): DcaPageSnapshot => {
  if (!isRecord(value)) return fallback
  return {
    config: normalizeDcaConfig(value.config, fallback.config, strategyKeys),
  }
}

export const buildDcaSnapshot = (
  config: DcaPageConfig,
  fallback = createEmptyDcaConfig(),
  strategyKeys: readonly string[] = [],
): DcaPageSnapshot => ({
  config: normalizeDcaConfig(config, fallback, strategyKeys),
})

export const createEmptyCompareSnapshot = (): ComparePageSnapshot => ({
  config: {
    symbolA: '',
    symbolB: '',
    days: 0,
    timeframe: '',
  },
})

export const createDefaultCompareSnapshot = (contract: ToolsPageContractResponse): ComparePageSnapshot => ({
  config: {
    symbolA: contract.compare_defaults.symbol_a || '',
    symbolB: contract.compare_defaults.symbol_b || '',
    days: contract.compare_defaults.days ?? 0,
    timeframe: contract.compare_defaults.timeframe || '',
  },
})

export const normalizeCompareSnapshot = (
  value: unknown,
  fallback = createEmptyCompareSnapshot(),
): ComparePageSnapshot => {
  const defaults = fallback
  if (!isRecord(value) || !isRecord(value.config)) return defaults
  return {
    config: {
      symbolA: readString(value.config.symbolA, defaults.config.symbolA),
      symbolB: readString(value.config.symbolB, defaults.config.symbolB),
      days: readNumber(value.config.days, defaults.config.days),
      timeframe: readString(value.config.timeframe, defaults.config.timeframe),
    },
  }
}

export const buildCompareSnapshot = (config: ComparePageSnapshot['config'], fallback = createEmptyCompareSnapshot()): ComparePageSnapshot => (
  normalizeCompareSnapshot({ config }, fallback)
)
