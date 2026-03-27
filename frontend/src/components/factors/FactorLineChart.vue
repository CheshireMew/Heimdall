<template>
  <div ref="chartContainer" class="h-full w-full"></div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([LineChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer])

const props = defineProps({
  categories: { type: Array, default: () => [] },
  series: { type: Array, default: () => [] },
  dark: { type: Boolean, default: false },
  yAxisLabel: { type: String, default: '' },
})

const chartContainer = ref(null)
let chartInstance = null

const renderChart = async () => {
  await nextTick()
  if (!chartContainer.value) return
  if (!chartInstance) chartInstance = echarts.init(chartContainer.value)
  chartInstance.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' },
    legend: {
      top: 0,
      textStyle: { color: props.dark ? '#d1d5db' : '#374151' },
    },
    grid: { left: 16, right: 16, top: 40, bottom: 16, containLabel: true },
    xAxis: {
      type: 'category',
      data: props.categories,
      axisLabel: { color: props.dark ? '#9ca3af' : '#6b7280', hideOverlap: true },
      axisLine: { lineStyle: { color: props.dark ? '#374151' : '#d1d5db' } },
    },
    yAxis: {
      type: 'value',
      name: props.yAxisLabel,
      nameTextStyle: { color: props.dark ? '#9ca3af' : '#6b7280', padding: [0, 0, 0, 8] },
      axisLabel: { color: props.dark ? '#9ca3af' : '#6b7280' },
      splitLine: { lineStyle: { color: props.dark ? '#374151' : '#e5e7eb' } },
    },
    series: props.series.map((item) => ({
      type: 'line',
      name: item.name,
      data: item.data,
      smooth: true,
      showSymbol: false,
      lineStyle: { color: item.color, width: 2 },
      itemStyle: { color: item.color },
      areaStyle: item.area ? { color: item.area } : undefined,
    })),
  })
}

watch(() => [props.categories, props.series, props.dark, props.yAxisLabel], renderChart, { deep: true })

onMounted(renderChart)

onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})
</script>
