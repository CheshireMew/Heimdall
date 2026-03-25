<template>
  <div class="relative w-full h-full" ref="chartContainer">
    <!-- Overlay/Loading/Tooltip could go here -->
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { createChart, CandlestickSeries, AreaSeries, HistogramSeries } from 'lightweight-charts'

const props = defineProps({
  data: {
    type: Array,
    default: () => []
  },
  volumeData: {
    type: Array,
    default: () => []
  },
  chartType: {
    type: String,
    default: 'candlestick' // 'candlestick' | 'line' | 'area'
  },
  autoResize: {
      type: Boolean,
      default: true
  },
  colors: {
    type: Object,
    default: () => ({
      upColor: '#26a69a',
      downColor: '#ef5350',
      bg: '#1f2937', // gray-800
      text: '#9ca3af', // gray-400
      grid: '#374151'  // gray-700
    })
  }
})

const chartContainer = ref(null)
let chart = null
let mainSeries = null
let volumeSeries = null

const syncVolumeSeries = () => {
    if (!chart) return

    if (props.volumeData.length > 0 && !volumeSeries) {
        volumeSeries = chart.addSeries(HistogramSeries, {
            priceFormat: { type: 'volume' },
            priceScaleId: '',
        })
        volumeSeries.priceScale().applyOptions({
            scaleMargins: { top: 0.8, bottom: 0 },
        })
        return
    }

    if (props.volumeData.length === 0 && volumeSeries) {
        chart.removeSeries(volumeSeries)
        volumeSeries = null
    }
}

const initChart = () => {
    if (!chartContainer.value) return

    chart = createChart(chartContainer.value, {
        width: chartContainer.value.clientWidth,
        height: chartContainer.value.clientHeight,
        layout: {
            background: { color: props.colors.bg },
            textColor: props.colors.text,
        },
        grid: {
            vertLines: { color: props.colors.grid },
            horzLines: { color: props.colors.grid },
        },
        timeScale: {
            borderColor: props.colors.grid,
            timeVisible: true
        },
        rightPriceScale: {
            borderColor: props.colors.grid,
        },
    })

    // Main Series
    if (props.chartType === 'area') {
        mainSeries = chart.addSeries(AreaSeries, {
            lineColor: '#2962FF', topColor: '#2962FF', bottomColor: 'rgba(41, 98, 255, 0.28)',
        });
    } else {
        mainSeries = chart.addSeries(CandlestickSeries, {
            upColor: props.colors.upColor,
            downColor: props.colors.downColor,
            borderVisible: false,
            wickUpColor: props.colors.upColor,
            wickDownColor: props.colors.downColor,
        })
    }

    updateData()
}

const updateData = () => {
    syncVolumeSeries()
    if (mainSeries && props.data.length > 0) mainSeries.setData(props.data)
    if (volumeSeries && props.volumeData.length > 0) volumeSeries.setData(props.volumeData)
}

// Resize Observer
let resizeObserver = null

onMounted(() => {
    initChart()
    
    if (props.autoResize) {
        resizeObserver = new ResizeObserver(entries => {
            if (entries.length === 0 || entries[0].target !== chartContainer.value) { return }
            const newRect = entries[0].contentRect
            chart.applyOptions({ width: newRect.width, height: newRect.height })
        })
        resizeObserver.observe(chartContainer.value)
    }
    
    // Infinite Scroll / Load More
    chart.timeScale().subscribeVisibleLogicalRangeChange(range => {
        if (!range) return
        // If scrolled near the beginning (left side)
        // logical range < 0 means we are scrolling into the past relative to initial data
        // But simpler check: if range.from is small (e.g. < 0 or close to min index)
        // Actually, logic is: pass event to parent, parent decides if need to load.
        // We just emit the range.
        const logicalRange = chart.timeScale().getVisibleLogicalRange();
        if (logicalRange !== null && logicalRange.from < 10) {
             emit('load-more')
        }
    })
})

const emit = defineEmits(['load-more'])

onUnmounted(() => {
    if (chart) {
        chart.remove()
        chart = null
    }
    if (resizeObserver) {
        resizeObserver.disconnect()
    }
})

watch(() => props.data, updateData, { deep: true })
watch(() => props.volumeData, updateData, { deep: true })

watch(() => props.colors, (newColors) => {
    if (!chart) return
    chart.applyOptions({
        layout: {
            background: { color: newColors.bg },
            textColor: newColors.text,
        },
        grid: {
            vertLines: { color: newColors.grid },
            horzLines: { color: newColors.grid },
        },
        timeScale: {
            borderColor: newColors.grid,
        },
        rightPriceScale: {
            borderColor: newColors.grid,
        },
    })
    
    // Update Candlestick colors if needed
    if (mainSeries && props.chartType !== 'area') {
        mainSeries.applyOptions({
            upColor: newColors.upColor,
            downColor: newColors.downColor,
            wickUpColor: newColors.upColor,
            wickDownColor: newColors.downColor,
        })
    }
}, { deep: true })

defineExpose({
    get chart() { return chart }
})

</script>
