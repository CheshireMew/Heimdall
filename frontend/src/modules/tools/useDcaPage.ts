import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Chart, registerables } from 'chart.js'

import { useTheme } from '@/composables/useTheme'
import { marketApi } from '../market/api'
import { toolsApi } from './api'


Chart.register(...registerables)


export function useDcaPage() {
  const { theme } = useTheme()
  const { t } = useI18n()

  const config = reactive({
    symbol: 'BTC/USDT',
    amount: 100,
    start_date: '2025-04-25',
    investment_time: '23:00',
    timezone: 'Asia/Shanghai',
    strategy: 'standard',
    strategy_params: {
      multiplier: 3,
    },
  })

  const loading = ref(false)
  const result = ref<any | null>(null)
  const marketData = reactive({
    rsi: null as string | null,
    sentiment: null as number | null,
    sentimentLabel: '',
  })
  const roiChartCanvas = ref<HTMLCanvasElement | null>(null)
  const priceChartCanvas = ref<HTMLCanvasElement | null>(null)
  const investmentChartCanvas = ref<HTMLCanvasElement | null>(null)

  let roiChart: Chart | null = null
  let priceChart: Chart | null = null
  let investmentChart: Chart | null = null

  const destroyCharts = () => {
    roiChart?.destroy()
    priceChart?.destroy()
    investmentChart?.destroy()
    roiChart = null
    priceChart = null
    investmentChart = null
  }

  const renderCharts = () => {
    if (!result.value?.history) {
      return
    }

    const history = result.value.history
    const labels = history.map((item) => item.date)
    const isDark = theme.value === 'dark'
    const textColor = isDark ? '#9ca3af' : '#6b7280'
    const gridColor = isDark ? '#374151' : '#e5e7eb'

    nextTick(() => {
      if (roiChartCanvas.value) {
        roiChart?.destroy()
        const ctx = roiChartCanvas.value.getContext('2d')
        const roiData = history.map((item) => item.roi)
        if (ctx) {
          roiChart = new Chart(ctx, {
            type: 'line',
            data: {
              labels,
              datasets: [{
                label: 'ROI (%)',
                data: roiData,
                borderColor: (context) => (context.parsed?.y >= 0 ? 'rgb(16, 185, 129)' : 'rgb(239, 68, 68)'),
                backgroundColor: (context) => (context.parsed?.y >= 0 ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)'),
                segment: {
                  borderColor: (context) => (context.p1.parsed.y >= 0 ? 'rgb(16, 185, 129)' : 'rgb(239, 68, 68)'),
                  backgroundColor: (context) => (context.p1.parsed.y >= 0 ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)'),
                },
                fill: true,
                tension: 0.4,
                pointRadius: 0,
              }],
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                legend: { display: false },
                tooltip: {
                  callbacks: {
                    label: (context) => `ROI: ${context.parsed.y.toFixed(2)}%`,
                  },
                  backgroundColor: isDark ? 'rgba(0, 0, 0, 0.8)' : 'rgba(255, 255, 255, 0.9)',
                  titleColor: isDark ? '#fff' : '#000',
                  bodyColor: isDark ? '#fff' : '#000',
                  borderColor: gridColor,
                  borderWidth: 1,
                },
              },
              scales: {
                x: {
                  display: true,
                  ticks: { maxTicksLimit: 6, color: textColor, font: { size: 10 } },
                  grid: { color: gridColor, display: false },
                },
                y: {
                  display: true,
                  ticks: { color: textColor, font: { size: 10 } },
                  grid: { color: gridColor },
                },
              },
            },
          })
        }
      }

      if (priceChartCanvas.value) {
        priceChart?.destroy()
        const ctx = priceChartCanvas.value.getContext('2d')
        if (ctx) {
          priceChart = new Chart(ctx, {
            type: 'line',
            data: {
              labels,
              datasets: [
                {
                  label: t('dca.btcPrice'),
                  data: history.map((item) => item.price),
                  borderColor: 'rgb(59, 130, 246)',
                  backgroundColor: 'rgba(59, 130, 246, 0.1)',
                  tension: 0.4,
                  pointRadius: 0,
                  yAxisID: 'y',
                },
                {
                  label: t('dca.averageCost'),
                  data: history.map((item) => item.avg_cost),
                  borderColor: 'rgb(251, 191, 36)',
                  backgroundColor: 'rgba(251, 191, 36, 0.1)',
                  tension: 0.4,
                  pointRadius: 0,
                  yAxisID: 'y',
                },
              ],
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              interaction: { mode: 'index', intersect: false },
              plugins: {
                legend: {
                  display: true,
                  labels: { color: textColor, boxWidth: 20 },
                },
                tooltip: {
                  backgroundColor: isDark ? 'rgba(0, 0, 0, 0.8)' : 'rgba(255, 255, 255, 0.9)',
                  titleColor: isDark ? '#fff' : '#000',
                  bodyColor: isDark ? '#fff' : '#000',
                  borderColor: gridColor,
                  borderWidth: 1,
                },
              },
              scales: {
                x: {
                  ticks: { maxTicksLimit: 6, color: textColor, font: { size: 10 } },
                  grid: { color: gridColor, display: false },
                },
                y: {
                  type: 'linear',
                  display: true,
                  position: 'left',
                  ticks: { color: textColor, font: { size: 10 } },
                  grid: { color: gridColor },
                },
              },
            },
          })
        }
      }

      if (investmentChartCanvas.value) {
        investmentChart?.destroy()
        const ctx = investmentChartCanvas.value.getContext('2d')
        if (ctx) {
          investmentChart = new Chart(ctx, {
            type: 'bar',
            data: {
              labels,
              datasets: [{
                label: t('dca.investAmount'),
                data: history.map((item, index) => item.invested - (history[index - 1]?.invested || 0)),
                backgroundColor: 'rgba(167, 139, 250, 0.6)',
                borderColor: 'rgb(167, 139, 250)',
                borderWidth: 0,
              }],
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                legend: { display: false },
                tooltip: {
                  callbacks: {
                    label: (context) => `${t('dca.invested')}: $${context.parsed.y.toFixed(2)}`,
                  },
                  backgroundColor: isDark ? 'rgba(0, 0, 0, 0.8)' : 'rgba(255, 255, 255, 0.9)',
                  titleColor: isDark ? '#fff' : '#000',
                  bodyColor: isDark ? '#fff' : '#000',
                  borderColor: gridColor,
                  borderWidth: 1,
                },
              },
              scales: {
                x: {
                  ticks: { maxTicksLimit: 6, color: textColor, font: { size: 10 } },
                  grid: { color: gridColor, display: false },
                },
                y: {
                  ticks: { color: textColor, font: { size: 10 } },
                  grid: { color: gridColor },
                },
              },
            },
          })
        }
      }
    })
  }

  const fetchMarketIndicators = async () => {
    try {
      const [realtimeRes, indicatorsRes] = await Promise.all([
        marketApi.getRealtime({ symbol: config.symbol, timeframe: '1d', limit: 100 }),
        marketApi.getIndicators({ days: 7 }),
      ])

      marketData.rsi = realtimeRes.data?.indicators?.rsi?.toFixed(2) || '--'
      const fearGreed = (indicatorsRes.data || []).find((item) => item.indicator_id === 'FEAR_GREED')
      if (!fearGreed || fearGreed.current_value === null) {
        return
      }

      marketData.sentiment = fearGreed.current_value
      if (fearGreed.current_value <= 25) {
        marketData.sentimentLabel = t('dca.fgLabels.extremeFear')
      } else if (fearGreed.current_value <= 45) {
        marketData.sentimentLabel = t('dca.fgLabels.fear')
      } else if (fearGreed.current_value <= 55) {
        marketData.sentimentLabel = t('dca.fgLabels.neutral')
      } else if (fearGreed.current_value <= 75) {
        marketData.sentimentLabel = t('dca.fgLabels.greed')
      } else {
        marketData.sentimentLabel = t('dca.fgLabels.extremeGreed')
      }
    } catch (error) {
      console.warn('Failed to fetch market indicators:', error)
    }
  }

  const runSimulation = async () => {
    loading.value = true
    try {
      const response = await toolsApi.runSimulation(config)
      result.value = {
        ...response.data,
        current_price: typeof response.data.current_price !== 'undefined'
          ? response.data.current_price
          : response.data.history?.[response.data.history.length - 1]?.price,
        total_days: response.data.history?.length ?? response.data.total_days,
      }
      await fetchMarketIndicators()
      renderCharts()
    } catch (error: any) {
      console.error('DCA Error:', error)
      alert(`${t('dca.simFailed')}: ${error.response?.data?.detail || error.message}`)
    } finally {
      loading.value = false
    }
  }

  watch(() => config.strategy, (nextStrategy) => {
    if (nextStrategy === 'ema_deviation') {
      config.strategy_params.multiplier = 3
    } else if (['rsi_dynamic', 'fear_greed', 'ahr999'].includes(nextStrategy)) {
      config.strategy_params.multiplier = 1
    }
  })

  watch(theme, () => {
    if (result.value) {
      renderCharts()
    }
  })

  onMounted(() => {
    try {
      const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone
      if (userTimezone) {
        config.timezone = userTimezone
      }
    } catch (error) {
      console.warn('Timezone detection failed:', error)
    }
    fetchMarketIndicators()
  })

  onBeforeUnmount(() => {
    destroyCharts()
  })

  const isPositiveRoi = computed(() => (result.value?.roi || 0) >= 0)
  const sentimentClass = computed(() => ((marketData.sentiment || 0) >= 50
    ? 'text-green-600 dark:text-green-400'
    : 'text-red-500 dark:text-red-400'))

  return {
    config,
    loading,
    result,
    marketData,
    roiChartCanvas,
    priceChartCanvas,
    investmentChartCanvas,
    runSimulation,
    isPositiveRoi,
    sentimentClass,
  }
}
