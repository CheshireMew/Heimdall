import { isRecord, readNumber, readString } from '@/composables/pageSnapshot'
import { API_BODY_DEFAULTS } from '@/api/routes'

import type { DCARequestSchema } from './contracts'

export interface DcaPageSnapshot {
  config: DcaPageConfig
}

export type DcaPageConfig = Required<Pick<DCARequestSchema, 'symbol' | 'amount' | 'investment_time' | 'timezone' | 'strategy'>> & {
  start_date: string
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

export const createDefaultDcaConfig = (): DcaPageConfig => ({
  symbol: API_BODY_DEFAULTS.dca_simulate.symbol,
  amount: API_BODY_DEFAULTS.dca_simulate.amount,
  start_date: '',
  investment_time: API_BODY_DEFAULTS.dca_simulate.investment_time,
  timezone: API_BODY_DEFAULTS.dca_simulate.timezone,
  strategy: API_BODY_DEFAULTS.dca_simulate.strategy,
  strategy_params: {
    multiplier: 3,
  },
})

export const normalizeDcaConfig = (
  value: unknown,
  fallback = createDefaultDcaConfig(),
): DcaPageConfig => {
  const defaults = fallback
  if (!isRecord(value)) return defaults

  const strategyParams = isRecord(value.strategy_params) ? value.strategy_params : {}
  return {
    symbol: readString(value.symbol, defaults.symbol),
    amount: readNumber(value.amount, defaults.amount),
    start_date: readString(value.start_date, defaults.start_date),
    investment_time: readString(value.investment_time, defaults.investment_time),
    timezone: readString(value.timezone, defaults.timezone),
    strategy: ['standard', 'ema_deviation', 'rsi_dynamic', 'fear_greed', 'ahr999'].includes(readString(value.strategy, defaults.strategy))
      ? readString(value.strategy, defaults.strategy) as DcaPageConfig['strategy']
      : defaults.strategy,
    strategy_params: {
      multiplier: readNumber(strategyParams.multiplier, defaults.strategy_params.multiplier),
    },
  }
}

export const createDefaultDcaSnapshot = (): DcaPageSnapshot => ({
  config: createDefaultDcaConfig(),
})

export const normalizeDcaSnapshot = (
  value: unknown,
  fallback = createDefaultDcaSnapshot(),
): DcaPageSnapshot => {
  if (!isRecord(value)) return fallback
  return {
    config: normalizeDcaConfig(value.config, fallback.config),
  }
}

export const buildDcaSnapshot = (config: DcaPageConfig): DcaPageSnapshot => ({
  config: normalizeDcaConfig(config),
})

export const createDefaultCompareSnapshot = (): ComparePageSnapshot => ({
  config: {
    symbolA: API_BODY_DEFAULTS.compare_pairs.symbol_a,
    symbolB: API_BODY_DEFAULTS.compare_pairs.symbol_b,
    days: API_BODY_DEFAULTS.compare_pairs.days,
    timeframe: API_BODY_DEFAULTS.compare_pairs.timeframe,
  },
})

export const normalizeCompareSnapshot = (
  value: unknown,
  fallback = createDefaultCompareSnapshot(),
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

export const buildCompareSnapshot = (config: ComparePageSnapshot['config']): ComparePageSnapshot => (
  normalizeCompareSnapshot({ config })
)
