<template>
  <div ref="chartContainer" class="h-full w-full"></div>
</template>

<script setup>
import { onMounted, watch } from 'vue'
import * as echarts from 'echarts/core'
import { BarChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { useEcharts } from '@/composables/useEcharts'

echarts.use([BarChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer])

const props = defineProps({
  categories: { type: Array, default: () => [] },
  series: { type: Array, default: () => [] },
  dark: { type: Boolean, default: false },
})

const { chartContainer, renderChart } = useEcharts(() => ({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' },
    legend: {
      top: 0,
      textStyle: { color: props.dark ? '#d1d5db' : '#374151' },
    },
    grid: { left: 16, right: 16, top: 36, bottom: 16, containLabel: true },
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
    series: props.series.map((item) => ({
      type: 'bar',
      name: item.name,
      data: item.data,
      itemStyle: { color: item.color },
      barMaxWidth: 26,
    })),
  }))

watch(() => [props.categories, props.series, props.dark], renderChart, { deep: true })

onMounted(renderChart)
</script>
