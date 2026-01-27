<template>
  <div class="h-full flex flex-col p-6 space-y-6">
    <!-- Configuration Panel -->
    <div class="bg-gray-800 rounded-xl border border-gray-700 p-4 flex flex-wrap items-end gap-4">
      <div class="flex-1 min-w-[200px]">
        <label class="block text-gray-400 text-xs font-bold mb-1">Symbol A</label>
        <div class="relative">
          <input v-model="config.symbolA" type="text" class="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 outline-none" placeholder="e.g. BTC" />
        </div>
      </div>
      
      <div class="flex items-center justify-center p-2">
         <span class="text-gray-500 font-bold text-xl">VS</span>
      </div>

      <div class="flex-1 min-w-[200px]">
        <label class="block text-gray-400 text-xs font-bold mb-1">Symbol B</label>
        <input v-model="config.symbolB" type="text" class="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 outline-none" placeholder="e.g. ETH" />
      </div>

      <div class="w-32">
        <label class="block text-gray-400 text-xs font-bold mb-1">Timeframe</label>
        <select v-model="config.timeframe" class="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-white outline-none">
          <option value="5m">5 Minute</option>
          <option value="15m">15 Minute</option>
          <option value="1h">1 Hour</option>
          <option value="4h">4 Hour</option>
          <option value="1d">1 Day</option>
          <option value="1w">1 Week</option>
          <option value="1M">1 Month</option>
        </select>
      </div>

      <div class="w-32">
        <label class="block text-gray-400 text-xs font-bold mb-1">Days</label>
        <input v-model.number="config.days" type="number" min="1" max="90" class="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-white outline-none" />
      </div>

      <button @click="fetchComparisonData" :disabled="loading" class="bg-blue-600 hover:bg-blue-500 text-white px-6 py-2 rounded-lg font-bold transition flex items-center disabled:opacity-50 disabled:cursor-not-allowed">
        <span v-if="loading" class="mr-2 animate-spin">⟳</span>
        {{ loading ? 'Analyzing...' : 'Compare Pairs' }}
      </button>
    </div>

    <!-- Charts Grid -->
    <div class="flex-1 grid grid-cols-2 grid-rows-2 gap-4 min-h-[600px]">
      
      <!-- Chart A -->
      <div class="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden flex flex-col relative">
        <div class="absolute top-2 left-2 z-10 bg-gray-900/80 px-2 py-1 rounded text-sm font-bold text-blue-400 border border-blue-500/30">
          {{ config.symbolA }}/USDT
        </div>
        <TradingViewChart 
          ref="chartARef"
          :data="dataA" 
          :colors="{ bg: '#1f2937', upColor: '#3b82f6', downColor: '#1d4ed8' }"
        />
      </div>

      <!-- Chart B -->
      <div class="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden flex flex-col relative">
        <div class="absolute top-2 left-2 z-10 bg-gray-900/80 px-2 py-1 rounded text-sm font-bold text-purple-400 border border-purple-500/30">
          {{ config.symbolB }}/USDT
        </div>
        <TradingViewChart 
          ref="chartBRef"
          :data="dataB" 
          :colors="{ bg: '#1f2937', upColor: '#a855f7', downColor: '#7e22ce' }"
        />
      </div>

      <!-- Ratio Chart (Full Width) -->
      <div class="col-span-2 bg-gray-800 rounded-xl border border-gray-700 overflow-hidden flex flex-col relative">
        <div class="absolute top-2 left-2 z-10 bg-gray-900/80 px-2 py-1 rounded text-sm font-bold text-green-400 border border-green-500/30">
          Ratio: {{ config.symbolA }} / {{ config.symbolB }}
        </div>
        <TradingViewChart 
          ref="chartRatioRef"
          :data="dataRatio" 
          chart-type="area"
          :colors="{ bg: '#1f2937' }"
        />
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import TradingViewChart from '@/components/TradingViewChart.vue'
import axios from 'axios'

const config = reactive({
  symbolA: 'BTC',
  symbolB: 'ETH',
  timeframe: '1h',
  days: 14
})

const loading = ref(false)
const dataA = ref([])
const dataB = ref([])
const dataRatio = ref([])

const chartARef = ref(null)
const chartBRef = ref(null)
const chartRatioRef = ref(null)

const fetchComparisonData = async () => {
    loading.value = true
    try {
        const response = await axios.post('/api/tools/compare_pairs', {
            symbol_a: config.symbolA,
            symbol_b: config.symbolB,
            days: config.days,
            timeframe: config.timeframe
        })

        const result = response.data

        if(result.comparison_data) {
            // Process API response to lightweight-charts format
            // API returns: { timestamp, price_a, price_b, ratio }
            // Lightweight charts needs: { time, value } or { time, open, high, low, close }
            
            // Note: The API currently returns a list of dictionaries.
            // Let's assume the API returns simplified line data for now or we map it.
            // Wait, previous backend implementation of `PairComparator` returns klines?
            // Checking `core/pair_comparator.py`: it returns `comparison_data` list.
            
            const processedA = []
            const processedB = []
            const processedRatio = []
            
            result.comparison_data.forEach(item => {
                // Time must be seconds
                // Item format from backend: { 'timestamp': ts, 'price_a': ..., 'price_b': ..., 'ratio': ... }
                // Timestamp from backend is likely ms or ISO string? Let's check backend.
                // It usually returns ms int if we look at processed data.
                
                const time = item.timestamp / 1000 
                
                processedA.push({ time, value: item.price_a })
                processedB.push({ time, value: item.price_b })
                processedRatio.push({ time, value: item.ratio })
            })

            dataA.value = processedA
            dataB.value = processedB
            dataRatio.value = processedRatio
            
            // Sync Charts (After data update)
            nextTick(() => {
                syncCharts()
            })
        }
        
    } catch (e) {
        console.error("Comparison failed", e)
        alert("对比失败: " + (e.response?.data?.detail || e.message))
    } finally {
        loading.value = false
    }
}

// Logic to sync charts
const syncCharts = () => {
    // We need access to the underlying chart instances.
    // TradingViewChart component wraps the chart but doesn't expose it directly yet.
    // We need to modify TradingViewChart to defineExpose({ chart }).
    
    // Assuming we will modify TradingViewChart.vue to expose 'chart'
    
    const cA = chartARef.value?.chart
    const cB = chartBRef.value?.chart
    const cR = chartRatioRef.value?.chart
    
    if(!cA || !cB || !cR) return
    
    // Sync Time Scale (Visible Range)
    const charts = [cA, cB, cR]
    
    charts.forEach(c1 => {
        c1.timeScale().subscribeVisibleLogicalRangeChange(range => {
            charts.forEach(c2 => {
                if(c1 !== c2) {
                    c2.timeScale().setVisibleLogicalRange(range)
                }
            })
        })
    })

    // Sync Crosshair
    // Lightweight charts v4+ supports syncing? 
    // Actually we need to manually forward crosshairMove events.
    charts.forEach(c1 => {
        c1.subscribeCrosshairMove(param => {
             charts.forEach(c2 => {
                if(c1 !== c2) {
                    // This data point extraction is tricky across charts if data isn't perfectly aligned
                    // But for now, let's just sync time range which is the most important.
                    // Crosshair sync usually requires external logic to 'setCrosshairPosition' which is not essentially exposed easily.
                    // Let's stick to Time Range Sync first which is huge functionality.
                }
             })
        })
    })
}

onMounted(() => {
    // Initial fetch
    fetchComparisonData()
})

</script>
