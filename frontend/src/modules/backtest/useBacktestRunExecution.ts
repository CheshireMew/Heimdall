import type { Ref } from 'vue'

import { backtestApi } from './api'


interface UseBacktestRunExecutionOptions {
  t: (key: string) => string
  config: any
  backtestLoading: Ref<boolean>
  paperLoading: Ref<boolean>
  historyMode: Ref<'backtest' | 'paper'>
  symbolsText: Ref<string>
  fetchHistory: () => Promise<void>
  fetchPaperHistory: () => Promise<void>
}

export const useBacktestRunExecution = ({
  t,
  config,
  backtestLoading,
  paperLoading,
  historyMode,
  symbolsText,
  fetchHistory,
  fetchPaperHistory,
}: UseBacktestRunExecutionOptions) => {
  const splitSymbols = () => symbolsText.value.split(',').map((item) => item.trim()).filter(Boolean)
  const isBusy = () => backtestLoading.value || paperLoading.value

  const buildPayload = () => ({
    strategy_key: config.strategy_key,
    strategy_version: config.strategy_version,
    timeframe: config.timeframe,
    days: config.days,
    initial_cash: config.initial_cash,
    fee_rate: config.fee_rate,
    portfolio: {
      symbols: splitSymbols(),
      max_open_trades: config.portfolio.max_open_trades,
      position_size_pct: config.portfolio.position_size_pct,
      stake_mode: config.portfolio.stake_mode,
    },
    research: {
      slippage_bps: config.research.slippage_bps,
      funding_rate_daily: config.research.funding_rate_daily,
      in_sample_ratio: config.research.in_sample_ratio,
      optimize_metric: config.research.optimize_metric,
      optimize_trials: config.research.optimize_trials,
      rolling_windows: config.research.rolling_windows,
    },
  })

  const buildPaperPayload = () => ({
    strategy_key: config.strategy_key,
    strategy_version: config.strategy_version,
    timeframe: config.timeframe,
    initial_cash: config.initial_cash,
    fee_rate: config.fee_rate,
    portfolio: {
      symbols: splitSymbols(),
      max_open_trades: config.portfolio.max_open_trades,
      position_size_pct: config.portfolio.position_size_pct,
      stake_mode: config.portfolio.stake_mode,
    },
  })

  const startBacktest = async () => {
    if (isBusy()) return null
    backtestLoading.value = true
    try {
      const res = await backtestApi.startRun(buildPayload())
      if (res.data.success) {
        historyMode.value = 'backtest'
        await fetchHistory()
        return { id: res.data.backtest_id, mode: 'backtest' as const }
      }
    } catch (error: any) {
      alert(`${t('backtest.failed')}: ${error.message}`)
    } finally {
      backtestLoading.value = false
    }
    return null
  }

  const startPaperRun = async () => {
    if (isBusy()) return null
    paperLoading.value = true
    try {
      const res = await backtestApi.startPaperRun(buildPaperPayload())
      if (res.data.success) {
        historyMode.value = 'paper'
        await fetchPaperHistory()
        return { id: res.data.run_id, mode: 'paper' as const }
      }
    } catch (error: any) {
      alert(`${t('backtest.paperFailed')}: ${error.message}`)
    } finally {
      paperLoading.value = false
    }
    return null
  }

  return {
    buildPayload,
    buildPaperPayload,
    startBacktest,
    startPaperRun,
  }
}
