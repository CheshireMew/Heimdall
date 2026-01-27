<template>
  <div class="h-full flex flex-col p-6 space-y-6">
      
    <div class="flex justify-between items-start">
        <!-- Input Form -->
        <div class="bg-gray-800 rounded-xl border border-gray-700 p-6 w-1/3">
            <h2 class="text-xl font-bold mb-4">New Backtest</h2>
            <div class="space-y-4">
                <div>
                    <label class="label">Symbol</label>
                    <input v-model="config.symbol" class="input" type="text" />
                </div>
                <div>
                   <label class="label">Days Lookback</label>
                   <input v-model.number="config.days" class="input" type="number" />
                </div>
                <div class="flex items-center">
                    <input v-model="config.use_ai" type="checkbox" class="w-4 h-4 rounded bg-gray-900 border-gray-600 text-blue-600 focus:ring-blue-500" />
                    <label class="ml-2 text-sm text-gray-300">Enable AI Analysis (Slower)</label>
                </div>
                <button @click="startBacktest" :disabled="loading" class="btn-primary w-full">
                    {{ loading ? 'Running...' : 'Run Backtest' }}
                </button>
            </div>
        </div>

        <!-- History List -->
        <div class="bg-gray-800 rounded-xl border border-gray-700 p-6 w-2/3 ml-6 overflow-hidden flex flex-col h-[300px]">
            <h2 class="text-xl font-bold mb-4">Recent Runs</h2>
            <div class="overflow-y-auto flex-1 space-y-2">
                <div v-for="run in history" :key="run.id" 
                     @click="loadResult(run.id)"
                     class="flex justify-between items-center p-3 bg-gray-900 rounded cursor-pointer hover:bg-gray-700 transition">
                    <div>
                        <span class="font-bold text-blue-400">{{ run.symbol }}</span>
                        <span class="text-xs text-gray-500 ml-2">{{ run.timeframe }}</span>
                    </div>
                    <div class="text-right">
                        <div class="text-sm font-bold" :class="run.total_signals > 0 ? 'text-green-400' : 'text-gray-500'">
                           {{ run.total_signals }} Signals
                        </div>
                        <div class="text-xs text-gray-500">{{ new Date(run.created_at).toLocaleString() }}</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Result View -->
    <div v-if="selectedRun" class="bg-gray-800 rounded-xl border border-gray-700 p-6 flex-1 flex flex-col min-h-[500px]">
        <div class="flex justify-between items-end mb-4">
            <h3 class="text-xl font-bold text-white">Result: #{{ selectedRun.id }}</h3>
            <div class="space-x-4 flex">
                <div class="stat-badge bg-green-900/50 text-green-400 border-green-700">Buy: {{ selectedRun.buy_signals }}</div>
                <div class="stat-badge bg-red-900/50 text-red-400 border-red-700">Sell: {{ selectedRun.sell_signals }}</div>
            </div>
        </div>
        
        <!-- Chart -->
        <div class="flex-1 border border-gray-700 rounded-lg overflow-hidden relative">
             <TradingViewChart 
                :data="chartData.candles" 
                :volume-data="chartData.volume"
             />
             <!-- Markers Logic (Requires ref to chart to add markers) 
                  We will implement markers later or via overlay -->
        </div>
    </div>

  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'
import TradingViewChart from '@/components/TradingViewChart.vue'

const config = reactive({
    symbol: 'BTC/USDT',
    days: 30,
    use_ai: false
})
const loading = ref(false)
const history = ref([])
const selectedRun = ref(null)
const chartData = reactive({ candles: [], volume: [] })

const fetchHistory = async () => {
    try {
        const res = await axios.get('/api/backtest/list')
        history.value = res.data
    } catch (e) { console.error(e) }
}

const startBacktest = async () => {
    loading.value = true
    try {
        const res = await axios.post('/api/backtest/start', config)
        if(res.data.success) {
            await fetchHistory()
            await loadResult(res.data.backtest_id)
        }
    } catch (e) {
        alert("Backtest failed: " + e.message)
    } finally {
        loading.value = false
    }
}

const loadResult = async (id) => {
    try {
        const res = await axios.get(`/api/backtest/${id}`)
        selectedRun.value = res.data
        
        // Parse signals and candles
        // Need to fetch candle data separately or include in response?
        // Standard backtest result usually contains signals list.
        // We need to fetch K-line history to render chart.
        // For now, let's fetch realtime kline for that period to render chart background
        
        // This part needs coordination with backend: result should contain K-line data used.
        // Assuming backend works, let's just show placeholder for data now.
        
    } catch (e) {
        console.error(e)
    }
}

onMounted(() => {
    fetchHistory()
})
</script>

<style scoped>
.label { @apply block text-gray-400 text-xs font-bold mb-1; }
.input { @apply w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-white outline-none focus:border-blue-500; }
.btn-primary { @apply bg-blue-600 hover:bg-blue-500 text-white py-2 rounded-lg font-bold transition disabled:opacity-50; }
.stat-badge { @apply px-3 py-1 rounded text-sm font-bold border; }
</style>
