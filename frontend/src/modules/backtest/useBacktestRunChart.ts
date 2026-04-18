import { reactive } from 'vue'

import { marketApi } from '@/modules/market'


export const useBacktestRunChart = () => {
  const chartData = reactive({ candles: [] as any[], volume: [] as any[] })

  const loadChart = async (run: any) => {
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
    const candles = (res.data || []).filter((item: any[]) => item[0] <= endTs)
    chartData.candles = candles.map((item: any[]) => ({ time: item[0] / 1000, open: item[1], high: item[2], low: item[3], close: item[4] }))
    chartData.volume = candles.map((item: any[]) => ({
      time: item[0] / 1000,
      value: item[5],
      color: item[4] >= item[1] ? 'rgba(16, 185, 129, 0.5)' : 'rgba(239, 68, 68, 0.5)',
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
