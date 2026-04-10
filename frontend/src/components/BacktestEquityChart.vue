<template>
  <div class="w-full h-full" ref="chartContainer"></div>
</template>

<script setup>
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { useTheme } from '@/composables/useTheme'
import { useI18n } from 'vue-i18n'

echarts.use([LineChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer])

const props = defineProps({
  points: {
    type: Array,
    default: () => [],
  },
})

const chartContainer = ref(null)
const { theme } = useTheme()
const { t, locale } = useI18n()
let chartInstance = null

const formatTimestamp = (value) => {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '--'
  return date.toLocaleString(locale.value)
}

const getOption = () => {
  const isDark = theme.value === 'dark'
  const axisColor = isDark ? '#9ca3af' : '#4b5563'
  const splitLineColor = isDark ? '#374151' : '#e5e7eb'
  const equityColor = isDark ? '#60a5fa' : '#2563eb'
  const drawdownColor = isDark ? '#fca5a5' : '#dc2626'
  const data = props.points || []
  const equityLabel = t('backtest.equity')
  const drawdownLabel = t('backtest.drawdown')

  return {
    animation: false,
    tooltip: {
      trigger: 'axis',
      backgroundColor: isDark ? 'rgba(31, 41, 55, 0.95)' : 'rgba(255, 255, 255, 0.95)',
      borderColor: isDark ? '#4b5563' : '#e5e7eb',
      textStyle: {
        color: isDark ? '#f3f4f6' : '#111827',
      },
      formatter(params) {
        const point = data[params[0]?.dataIndex ?? 0]
        if (!point) return ''
        return [
          formatTimestamp(point.timestamp),
          `${equityLabel}: ${point.equity.toFixed(2)}`,
          `${t('backtest.pnlAbs')}: ${point.pnl_abs.toFixed(2)}`,
          `${drawdownLabel}: ${point.drawdown_pct.toFixed(2)}%`,
        ].join('<br/>')
      },
    },
    legend: {
      top: 0,
      data: [equityLabel, drawdownLabel],
      textStyle: { color: axisColor },
    },
    grid: {
      left: '4%',
      right: '4%',
      top: '12%',
      bottom: '6%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: data.map((item) => formatTimestamp(item.timestamp)),
      axisLabel: { color: axisColor },
      axisLine: { lineStyle: { color: splitLineColor } },
    },
    yAxis: [
      {
        type: 'value',
        scale: true,
        axisLabel: { color: axisColor },
        splitLine: {
          lineStyle: {
            color: splitLineColor,
            type: 'dashed',
          },
        },
      },
      {
        type: 'value',
        scale: true,
        axisLabel: { color: axisColor, formatter: '{value}%' },
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: equityLabel,
        color: equityColor,
        type: 'line',
        smooth: true,
        symbol: 'none',
        data: data.map((item) => item.equity),
        lineStyle: { color: equityColor, width: 2 },
        itemStyle: { color: equityColor },
        areaStyle: {
          color: isDark ? 'rgba(96, 165, 250, 0.18)' : 'rgba(37, 99, 235, 0.12)',
        },
      },
      {
        name: drawdownLabel,
        color: drawdownColor,
        type: 'line',
        smooth: true,
        symbol: 'none',
        yAxisIndex: 1,
        data: data.map((item) => item.drawdown_pct),
        lineStyle: { color: drawdownColor, width: 2 },
        itemStyle: { color: drawdownColor },
      },
    ],
  }
}

const renderChart = () => {
  if (!chartContainer.value) return
  if (!chartInstance) {
    chartInstance = echarts.init(chartContainer.value)
  }
  chartInstance.setOption(getOption())
}

const handleResize = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
}

watch(
  () => props.points,
  async () => {
    await nextTick()
    renderChart()
  },
  { deep: true },
)

watch(theme, () => {
  renderChart()
})

watch(locale, () => {
  renderChart()
})

onMounted(() => {
  renderChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
  window.removeEventListener('resize', handleResize)
})
</script>
