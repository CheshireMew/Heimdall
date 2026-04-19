<template>
  <div ref="chartContainer" class="h-full w-full"></div>
</template>

<script setup>
import { onMounted, watch } from 'vue'
import * as echarts from 'echarts/core'
import { BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { useEcharts } from '@/composables/useEcharts'

echarts.use([BarChart, GridComponent, TooltipComponent, CanvasRenderer])

const props = defineProps({
  categories: { type: Array, default: () => [] },
  values: { type: Array, default: () => [] },
  dark: { type: Boolean, default: false },
  positiveColor: { type: String, default: '#10b981' },
  negativeColor: { type: String, default: '#ef4444' },
})

const { chartContainer, renderChart } = useEcharts(() => ({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' },
    grid: { left: 16, right: 16, top: 16, bottom: 16, containLabel: true },
    xAxis: {
      type: 'category',
      data: props.categories,
      axisLabel: { color: props.dark ? '#9ca3af' : '#6b7280' },
      axisLine: { lineStyle: { color: props.dark ? '#374151' : '#d1d5db' } },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: props.dark ? '#9ca3af' : '#6b7280' },
      splitLine: { lineStyle: { color: props.dark ? '#374151' : '#e5e7eb' } },
    },
    series: [
      {
        type: 'bar',
        data: props.values.map((value) => ({
          value,
          itemStyle: { color: value >= 0 ? props.positiveColor : props.negativeColor },
        })),
        barMaxWidth: 32,
      },
    ],
  }))

watch(() => [props.categories, props.values, props.dark], renderChart, { deep: true })

onMounted(renderChart)
</script>
