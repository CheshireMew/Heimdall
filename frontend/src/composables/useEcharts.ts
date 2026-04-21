import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts/core'

export function useEcharts(buildOption: () => Record<string, unknown>) {
  const chartContainer = ref<HTMLElement | null>(null)
  let chartInstance: echarts.ECharts | null = null

  const renderChart = async () => {
    await nextTick()
    if (!chartContainer.value) return
    if (!chartInstance) chartInstance = echarts.init(chartContainer.value)
    chartInstance.setOption(buildOption())
  }

  const resizeChart = () => {
    chartInstance?.resize()
  }

  onMounted(() => {
    window.addEventListener('resize', resizeChart)
    renderChart()
  })

  onBeforeUnmount(() => {
    window.removeEventListener('resize', resizeChart)
    if (!chartInstance) return
    chartInstance.dispose()
    chartInstance = null
  })

  return {
    chartContainer,
    renderChart,
    resizeChart,
  }
}
