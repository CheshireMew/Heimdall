import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Chart from 'chart.js/auto'
import annotationPlugin from 'chartjs-plugin-annotation'
import 'chartjs-adapter-date-fns'

import { useTheme } from '@/composables/useTheme'
import { marketApi } from './api'


Chart.register(annotationPlugin)


export function useHalvingPage() {
  const { t } = useI18n()
  const { theme } = useTheme()

  const loading = ref(true)
  const chartCanvas = ref<HTMLCanvasElement | null>(null)
  const historyData = ref<any[]>([])
  const currentPrice = ref(0)
  const showPhases = ref(true)
  const scaleType = ref<'logarithmic' | 'linear'>('logarithmic')
  const lastHalvingDate = new Date('2024-04-20')
  const nextHalvingEst = new Date('2028-04-17')
  const halvingDates = [
    { date: '2012-11-28', label: 'H1' },
    { date: '2016-07-09', label: 'H2' },
    { date: '2020-05-11', label: 'H3' },
    { date: '2024-04-20', label: 'H4' },
    { date: '2028-04-17', label: 'H5 (Est)', future: true },
  ]

  let chartInstance: Chart | null = null

  const nextHalvingDate = computed(() => nextHalvingEst.toISOString().split('T')[0])
  const daysToHalving = computed(() => Math.ceil((nextHalvingEst.getTime() - Date.now()) / (1000 * 60 * 60 * 24)))
  const cycleProgress = computed(() => {
    const totalDuration = nextHalvingEst.getTime() - lastHalvingDate.getTime()
    const elapsed = Date.now() - lastHalvingDate.getTime()
    return Math.min(Math.max((elapsed / totalDuration) * 100, 0), 100).toFixed(1)
  })

  const formatPrice = (price: number) => new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(price)

  const calculatePhaseAnnotations = (isDark: boolean) => {
    if (!showPhases.value) {
      return {}
    }

    const annotations = {}
    const oneDay = 24 * 60 * 60 * 1000
    halvingDates.forEach((halving, index) => {
      const halvingTime = new Date(halving.date).getTime()
      annotations[`acc_${index}`] = {
        type: 'box',
        xMin: halvingTime - (500 * oneDay),
        xMax: halvingTime,
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        borderWidth: 0,
        label: {
          display: true,
          content: t('halving.accumulation'),
          color: isDark ? 'rgba(34, 197, 94, 0.8)' : 'rgba(21, 128, 61, 0.8)',
          font: { size: 10 },
          position: 'start',
          yAdjust: -20,
        },
      }
      annotations[`exp_${index}`] = {
        type: 'box',
        xMin: halvingTime,
        xMax: halvingTime + (540 * oneDay),
        backgroundColor: 'rgba(249, 115, 22, 0.1)',
        borderWidth: 0,
        label: {
          display: true,
          content: t('halving.bullRun'),
          color: isDark ? 'rgba(249, 115, 22, 0.8)' : 'rgba(194, 65, 12, 0.8)',
          font: { size: 10 },
          position: 'start',
          yAdjust: -20,
        },
      }
    })
    return annotations
  }

  const renderChart = () => {
    chartInstance?.destroy()
    if (!chartCanvas.value) {
      return
    }

    const isDark = theme.value === 'dark'
    const gridColor = isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)'
    const textColor = isDark ? '#9CA3AF' : '#6B7280'
    const datasets = [{
      label: t('halving.btcPrice'),
      data: historyData.value.map((row) => ({ x: row[0], y: row[4] })),
      borderColor: isDark ? '#FCD34D' : '#F59E0B',
      borderWidth: 1.5,
      pointRadius: 0,
      tension: 0.1,
    }]

    let annotations = {}
    halvingDates.forEach((halving, index) => {
      annotations[`halving_${index}`] = {
        type: 'line',
        scaleID: 'x',
        value: new Date(halving.date).getTime(),
        borderColor: isDark ? 'rgba(255, 255, 255, 0.3)' : 'rgba(0,0,0,0.3)',
        borderWidth: 2,
        borderDash: [6, 6],
        label: {
          display: true,
          content: halving.label,
          position: 'start',
          backgroundColor: isDark ? 'rgba(30, 41, 59, 1)' : 'rgba(255, 255, 255, 1)',
          color: isDark ? '#fff' : '#000',
          font: { size: 11, weight: 'bold' },
          yAdjust: 0,
        },
      }
    })
    annotations = { ...annotations, ...calculatePhaseAnnotations(isDark) }

    const now = Date.now()
    const oneDay = 24 * 60 * 60 * 1000
    const h4 = new Date(halvingDates[3].date).getTime()
    const h5 = new Date(halvingDates[4].date).getTime()
    const bullEnd = h4 + (540 * oneDay)
    const accStart = h5 - (500 * oneDay)
    let nextPhaseLabel = ''
    let nextPhaseDays = 0

    if (now < bullEnd) {
      nextPhaseLabel = t('halving.bullRunEnds')
      nextPhaseDays = Math.ceil((bullEnd - now) / oneDay)
    } else if (now < accStart) {
      nextPhaseLabel = t('halving.accStarts')
      nextPhaseDays = Math.ceil((accStart - now) / oneDay)
    } else {
      nextPhaseLabel = t('halving.nextHalvingPhase')
      nextPhaseDays = Math.ceil((h5 - now) / oneDay)
    }

    if (now > h4) {
      annotations.current_countdown = {
        type: 'line',
        scaleID: 'x',
        value: now,
        borderColor: isDark ? '#3B82F6' : '#2563EB',
        borderWidth: 2,
        borderDash: [2, 4],
        label: {
          display: true,
          content: [t('halving.today'), t('halving.daysTo', { days: nextPhaseDays, phase: nextPhaseLabel })],
          position: 'center',
          backgroundColor: isDark ? 'rgba(59, 130, 246, 0.9)' : 'rgba(37, 99, 235, 0.9)',
          color: '#fff',
          font: { size: 12, weight: 'bold' },
          yAdjust: 100,
        },
      }
    }

    const context = chartCanvas.value.getContext('2d')
    if (!context) {
      return
    }
    chartInstance = new Chart(context, {
      type: 'line',
      data: { datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: 'nearest',
          axis: 'x',
          intersect: false,
        },
        scales: {
          x: {
            type: 'time',
            time: { unit: 'year' },
            grid: { color: gridColor, borderColor: gridColor },
            ticks: { color: textColor },
          },
          y: {
            type: scaleType.value,
            position: 'right',
            grid: { color: gridColor, borderColor: gridColor },
            ticks: {
              color: textColor,
              callback(value) {
                return `$${value.toLocaleString()}`
              },
            },
          },
        },
        plugins: {
          annotation: { annotations },
          legend: { display: false },
          tooltip: {
            enabled: true,
            backgroundColor: isDark ? 'rgba(17, 24, 39, 0.9)' : 'rgba(255, 255, 255, 0.9)',
            titleColor: isDark ? '#fff' : '#000',
            bodyColor: isDark ? '#fff' : '#000',
            borderColor: isDark ? '#374151' : '#E5E7EB',
            borderWidth: 1,
          },
        },
      },
    })
  }

  const fetchData = async () => {
    loading.value = true
    try {
      const response = await marketApi.getFullHistory({
        symbol: 'BTC/USDT',
        start_date: '2010-07-01',
        timeframe: '1d',
      })
      if (Array.isArray(response.data)) {
        historyData.value = response.data.filter((row) => row[4] > 0)
        if (response.data.length > 0) {
          currentPrice.value = response.data[response.data.length - 1][4]
        }
      }
    } catch (error) {
      console.error('Fetch halving data failed', error)
    } finally {
      loading.value = false
      renderChart()
    }
  }

  watch([showPhases, scaleType], () => {
    renderChart()
  })

  watch(theme, () => {
    renderChart()
  })

  onMounted(() => {
    fetchData()
  })

  onBeforeUnmount(() => {
    chartInstance?.destroy()
    chartInstance = null
  })

  return {
    loading,
    chartCanvas,
    currentPrice,
    showPhases,
    scaleType,
    nextHalvingDate,
    daysToHalving,
    cycleProgress,
    formatPrice,
  }
}
