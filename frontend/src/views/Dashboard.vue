<template>
  <div class="h-full flex flex-col p-6 space-y-6">
    <!-- Header Stats (Fake Data) -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
      <div v-for="stat in stats" :key="stat.label" class="bg-gray-800 p-4 rounded-xl border border-gray-700 shadow-sm">
        <div class="text-gray-400 text-xs uppercase font-bold tracking-wider mb-1">{{ stat.label }}</div>
        <div class="text-2xl font-bold font-mono" :class="stat.color">{{ stat.value }}</div>
        <div class="text-xs mt-1" :class="stat.trend > 0 ? 'text-green-500' : 'text-red-500'">
          {{ stat.trend > 0 ? '+' : '' }}{{ stat.trend }}%
        </div>
      </div>
    </div>

    <!-- Main Chart Area -->
    <div class="flex-1 bg-gray-800 rounded-xl border border-gray-700 overflow-hidden flex flex-col shadow-lg">
      <div class="p-4 border-b border-gray-700 flex justify-between items-center bg-gray-800/50">
         <div class="flex items-center space-x-4">
            <h3 class="font-bold text-lg text-gray-100 flex items-center">
              <span class="w-2 h-2 rounded-full bg-green-500 mr-2 animate-pulse"></span>
              BTC/USDT
            </h3>
            <div class="flex space-x-1 bg-gray-900 rounded-lg p-1">
                <button v-for="tf in timeframes" :key="tf" 
                    @click="currentTimeframe = tf"
                    :class="['px-3 py-1 text-xs rounded-md transition-all', currentTimeframe === tf ? 'bg-blue-600 text-white shadow' : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800']">
                    {{ tf }}
                </button>
            </div>
         </div>
      </div>
      
      <div class="flex-1 relative">
         <div v-if="loadingMore" class="absolute top-4 left-1/2 transform -translate-x-1/2 z-20 bg-blue-600 text-white px-3 py-1 rounded-full text-xs shadow-lg flex items-center">
            <span class="animate-spin mr-2">⟳</span> Loading History...
         </div>
         <TradingViewChart 
            :data="chartData" 
            :volume-data="volumeData"
            :colors="{ bg: '#1f2937', grid: '#374151', text: '#9ca3af', upColor: '#10b981', downColor: '#ef4444' }"
            @load-more="handleLoadMore"
         />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import TradingViewChart from '@/components/TradingViewChart.vue'
import axios from 'axios' // Directly use axios for now, will refactor to api service

const stats = ref([
    { label: 'Current Price', value: '$98,420.50', trend: 2.4, color: 'text-green-400' },
    { label: '24h High', value: '$99,100.00', trend: 0.5, color: 'text-gray-200' },
    { label: 'RSI (14)', value: '68.5', trend: 5.2, color: 'text-yellow-400' },
    { label: 'Fear & Greed', value: '75', trend: -2.0, color: 'text-green-400' },
])

const timeframes = ['5m', '15m', '1h', '4h', '1d', '1w', '1M']
const currentTimeframe = ref('1h')
const chartData = ref([])
const volumeData = ref([])

const loadingMore = ref(false)
const noMoreHistory = ref(false)

const handleLoadMore = async () => {
    if (loadingMore.value || noMoreHistory.value || chartData.value.length === 0) return
    
    // Get timestamp of the first (oldest) candle
    // chartData is sorted asc, so index 0 is oldest.
    // Time in chartData is seconds (TV format), backend expects ms.
    const oldest = chartData.value[0]
    const endTs = oldest.time * 1000
    
    loadingMore.value = true
    try {
        console.log("Loading history before:", new Date(endTs).toLocaleString())
        const res = await axios.get('/api/history', {
            params: {
                symbol: 'BTC/USDT',
                timeframe: currentTimeframe.value,
                end_ts: endTs,
                limit: 500
            }
        })
        
        const newKlines = res.data
        if (newKlines.length === 0) {
            noMoreHistory.value = true
            console.log("No more history in DB")
            return
        }
        
        const formatKlines = (klines) => klines.map(k => ({
            time: k[0] / 1000,
            open: k[1], high: k[2], low: k[3], close: k[4]
        }))
        
        const formatVolume = (klines) => klines.map(k => ({
            time: k[0] / 1000,
            value: k[5],
            color: k[4] >= k[1] ? 'rgba(16, 185, 129, 0.5)' : 'rgba(239, 68, 68, 0.5)'
        }))
        
        const newCandles = formatKlines(newKlines)
        const newVols = formatVolume(newKlines)
        
        // Prepend data
        // For lightweight charts, we reset data? No, that jumps.
        // We should merge and setData. Lightweight charts doesn't support 'prepend' validly without full reset usually?
        // Actually setData is fast.
        
        chartData.value = [...newCandles, ...chartData.value]
        volumeData.value = [...newVols, ...volumeData.value]
        
    } catch (e) {
        console.error("Load history failed", e)
    } finally {
        loadingMore.value = false
    }
}

// Watch for timeframe changes and re-fetch data
import { watch } from 'vue'
watch(currentTimeframe, () => {
    noMoreHistory.value = false // reset flag
    fetchMarketData()
})

// Mock Data Generation (To verify component works before connecting API)
// Or fetch from our real API
const fetchMarketData = async () => {
    try {
        // 1. Fetch Price History
        // Change to Query Param to avoid slash issues in URL path
        const response = await axios.get('/api/realtime', { 
            params: { 
                symbol: 'BTC/USDT',
                timeframe: currentTimeframe.value, 
                limit: 3000 
            }
        })
        
        const klines = response.data.kline_data
        
        chartData.value = klines.map(k => ({
            time: k[0] / 1000, // TV requires seconds
            open: k[1],
            high: k[2],
            low: k[3],
            close: k[4],
        }))
        
        volumeData.value = klines.map(k => ({
            time: k[0] / 1000,
            value: k[5],
            color: k[4] >= k[1] ? 'rgba(16, 185, 129, 0.5)' : 'rgba(239, 68, 68, 0.5)'
        }))
        
        // Update price stats
        if(chartData.value.length > 0) {
            const last = chartData.value[chartData.value.length - 1]
            stats.value[0].value = `$${last.close.toFixed(2)}`
            // Calculate pseudo-24h high from loaded data (last 24 points or max of visible)
            // Ideally backend should return ticker stats. For now use visible max.
            const maxHigh = Math.max(...chartData.value.slice(-24*4).map(k => k.high)) // approx
            stats.value[1].value = `$${maxHigh.toFixed(2)}`
        }
        
        // 2. Fetch Sentiment
        try {
            const sentimentRes = await axios.get('/api/market/sentiment')
            if (sentimentRes.data && sentimentRes.data.value) {
                stats.value[3].value = sentimentRes.data.value
                // Assuming data has classification like "Extreme Greed"
                stats.value[3].label = `Fear & Greed (${sentimentRes.data.value_classification})`
                // Color coding
                const val = parseInt(sentimentRes.data.value)
                stats.value[3].color = val > 50 ? 'text-green-400' : 'text-red-400'
            }
        } catch (e) {
            console.warn("Sentiment fetch failed", e)
        }

    } catch (e) {
        console.error("Fetch failed", e)
    }
}

onMounted(() => {
    fetchMarketData()
})

</script>
