import { computed, type ComputedRef } from 'vue'
import type { DliThresholdsResponse } from './contracts'

export type MacroTone = 'support' | 'pressure' | 'neutral'

export const macroScoreToneClass = (tone: MacroTone) => {
  if (tone === 'support') return 'text-[#0f6b4f] dark:text-emerald-300'
  if (tone === 'pressure') return 'text-[#c84c28] dark:text-orange-300'
  return 'text-[#8a6a24] dark:text-amber-300'
}

export const macroPressureClass = (value: number | null) => {
  if (typeof value !== 'number' || Math.abs(value) < 0.001) return 'text-slate-500 dark:text-slate-400'
  return value >= 0 ? 'text-[#c84c28] dark:text-orange-300' : 'text-[#0f6b4f] dark:text-emerald-300'
}

export const macroThresholdValues = (thresholds: DliThresholdsResponse | null | undefined) => ({
  p20: thresholds?.p20 ?? 43,
  p50: thresholds?.p50 ?? 50,
  p80: thresholds?.p80 ?? 68,
})

export const useMacroRegimes = (thresholds: ComputedRef<DliThresholdsResponse | null>) => computed(() => {
  const values = macroThresholdValues(thresholds.value)
  return [
    {
      title: '流动性宽松',
      range: `≤ P20 (${values.p20.toFixed(1)})`,
      color: '#0f6b4f',
      description: '压力分处于历史低分位，说明关键指标整体偏向释放流动性或缓和融资压力。',
    },
    {
      title: '中性偏松',
      range: `P20-P50 (${values.p20.toFixed(1)}-${values.p50.toFixed(1)})`,
      color: '#8a8f56',
      description: '未进入极端宽松，但压力低于历史中位数，流动性背景偏友好。',
    },
    {
      title: '中性偏紧',
      range: `P50-P80 (${values.p50.toFixed(1)}-${values.p80.toFixed(1)})`,
      color: '#c9873a',
      description: '压力高于历史中位数，但尚未进入极端收紧区间。',
    },
    {
      title: '流动性收紧',
      range: `≥ P80 (${values.p80.toFixed(1)})`,
      color: '#c84c28',
      description: '压力分处于历史高分位，美元流动性通常对风险资产形成明显逆风。',
    },
  ]
})
