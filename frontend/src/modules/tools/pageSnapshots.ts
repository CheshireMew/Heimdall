import { isRecord, readNumber, readString } from '@/composables/pageSnapshot'

import type { DCARequestSchema } from '@/types'

export interface DcaPageSnapshot {
  config: DCARequestSchema
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
  symbol: 'BTC/USDT',
  amount: 100,
  start_date: '2025-04-25',
  investment_time: '23:00',
  timezone: 'Asia/Shanghai',
  strategy: 'standard',
  strategy_params: {
    multiplier: 3,
  },
})

export const normalizeDcaConfig = (value: unknown): DcaPageConfig => {
  const defaults = createDefaultDcaConfig()
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

export const normalizeDcaSnapshot = (value: unknown): DcaPageSnapshot => {
  if (!isRecord(value)) return createDefaultDcaSnapshot()
  return {
    config: normalizeDcaConfig(value.config),
  }
}

export const createDefaultCompareSnapshot = (): ComparePageSnapshot => ({
  config: {
    symbolA: 'BTC',
    symbolB: 'ETH',
    days: 30,
    timeframe: '1h',
  },
})

export const normalizeCompareSnapshot = (value: unknown): ComparePageSnapshot => {
  const defaults = createDefaultCompareSnapshot()
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
