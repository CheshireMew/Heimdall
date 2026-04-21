<template>
  <div class="w-full" :class="height" ref="chartContainer"></div>
</template>

<script setup>
import { watch } from 'vue'
import * as echarts from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { useEcharts } from '@/composables/useEcharts'
import { useTheme } from '@/composables/useTheme'
import { useDateTime } from '@/composables/useDateTime'

echarts.use([LineChart, GridComponent, TooltipComponent, CanvasRenderer])

const props = defineProps({
  indicator: {
    type: Object,
    required: true
  },
  height: {
    type: String,
    default: 'h-48'
  }
})

const { theme } = useTheme()
const { timezone, formatDate } = useDateTime()

const getChartOption = (indicator, isDark) => {
  const textColor = isDark ? '#9ca3af' : '#4b5563'
  const lineColor = isDark ? '#3b82f6' : '#2563eb' // Blue
  const areaColor = isDark ? 'rgba(59, 130, 246, 0.2)' : 'rgba(37, 99, 235, 0.2)'
  const splitLineColor = isDark ? '#374151' : '#e5e7eb'

  const dataDates = indicator.history.map(item => formatDate(item.date))
  const dataValues = indicator.history.map(item => item.value)

  return {
    tooltip: {
      trigger: 'axis',
       backgroundColor: isDark ? 'rgba(31, 41, 55, 0.9)' : 'rgba(255, 255, 255, 0.9)',
      borderColor: isDark ? '#4b5563' : '#e5e7eb',
      textStyle: {
        color: isDark ? '#f3f4f6' : '#111827'
      },
      formatter: function (params) {
        return `${params[0].axisValue}<br/><b>${params[0].data}</b> ${indicator.unit || ''}`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dataDates,
      axisLabel: { color: textColor },
      axisLine: { lineStyle: { color: splitLineColor } },
      splitLine: { show: false }
    },
    yAxis: {
      type: 'value',
      scale: true,
      axisLabel: { color: textColor },
      splitLine: { 
        show: true,
        lineStyle: {
          color: splitLineColor,
          type: 'dashed'
        }
      }
    },
    series: [
      {
        name: indicator.name,
        type: 'line',
        smooth: true,
        symbol: 'none',
        sampling: 'lttb', // downsample large datasets
        itemStyle: { color: lineColor },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: areaColor },
            { offset: 1, color: isDark ? 'rgba(59, 130, 246, 0)' : 'rgba(37, 99, 235, 0)' }
          ])
        },
        data: dataValues
      }
    ]
  }
}

const { chartContainer, renderChart } = useEcharts(() => (
  props.indicator?.history ? getChartOption(props.indicator, theme.value === 'dark') : {}
))

watch(() => props.indicator, () => {
  renderChart()
}, { deep: true })

watch(theme, () => {
  renderChart()
})

watch(timezone, () => {
  renderChart()
})
</script>
