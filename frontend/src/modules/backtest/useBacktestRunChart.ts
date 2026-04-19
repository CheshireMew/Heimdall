import { reactive } from 'vue'

import { marketApi } from '@/modules/market'
import type { BacktestDetailResponse, CandlestickData, OhlcvPointResponse, VolumeData } from '@/types'

import type { BacktestChartData } from './viewTypes'

export const useBacktestRunChart = () => {
  const chartData = reactive<BacktestChartData>({ candles: [], volume: [] })

  const loadChart = async (run: BacktestDetailResponse) => {
    const targetSymbol = Array.isArray(run?.metadata?.symbols) && run.metadata.symbols.length ? run.metadata.symbols[0] : run?.symbol
    if (!targetSymbol || targetSymbol === 'PORTFOLIO' || !run?.start_date) {
      chartData.candles = []
      chartData.volume = []
      return
    }
    const startDate = run.start_date.slice(0, 10)
    const endTs = run.end_date ? new Date(run.end_date).getTime() : Date.now()
    const res = await marketApi.getPriceHistory({
      symbol: targetSymbol,
      timeframe: run.timeframe,
      start_date: startDate,
      fetch_policy: 'hydrate',
    })
    const candles = (res.data.items || []).filter((item: OhlcvPointResponse) => item.timestamp <= endTs)
    chartData.candles = candles.map<CandlestickData>((item) => ({
      time: item.timestamp / 1000,
      open: item.open,
      high: item.high,
      low: item.low,
      close: item.close,
    }))
    chartData.volume = candles.map<VolumeData>((item) => ({
      time: item.timestamp / 1000,
      value: item.volume,
      color: item.close >= item.open ? 'rgba(16, 185, 129, 0.5)' : 'rgba(239, 68, 68, 0.5)',
    }))
  }

  const clearChart = () => {
    chartData.candles = []
    chartData.volume = []
  }

  return {
    chartData,
    loadChart,
    clearChart,
  }
}
