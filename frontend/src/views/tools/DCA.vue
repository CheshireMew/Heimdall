<template>
  <div class="h-full flex flex-col p-6 space-y-4">
    <!-- Configuration -->
    <div class="bg-gray-800 rounded-xl border border-gray-700 p-6">
      <h2 class="text-xl font-bold mb-4 flex items-center">
        <BanknotesIcon class="w-6 h-6 mr-2 text-green-400" />
        定投模拟配置
      </h2>
      
      <div class="grid grid-cols-1 md:grid-cols-6 gap-4 items-end">
        <div>
          <label class="block text-gray-400 text-xs font-bold mb-1">交易对</label>
          <input v-model="config.symbol" type="text" class="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-white outline-none" />
        </div>
        <div>
          <label class="block text-gray-400 text-xs font-bold mb-1">开始日期</label>
          <input v-model="config.start_date" type="date" class="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-white outline-none" />
        </div>
        <div>
          <label class="block text-gray-400 text-xs font-bold mb-1">定投时间</label>
          <select v-model="config.investment_time" class="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-white outline-none">
            <option value="00:00">00:00</option>
            <option value="02:00">02:00</option>
            <option value="04:00">04:00</option>
            <option value="06:00">06:00</option>
            <option value="08:00">08:00</option>
            <option value="10:00">10:00</option>
            <option value="12:00">12:00</option>
            <option value="14:00">14:00</option>
            <option value="16:00">16:00</option>
            <option value="18:00">18:00</option>
            <option value="20:00">20:00</option>
            <option value="22:00">22:00</option>
            <option value="23:00">23:00</option>
          </select>
        </div>
        
        <!-- Strategy Selector -->
        <div>
           <label class="block text-gray-400 text-xs font-bold mb-1">策略</label>
           <select v-model="config.strategy" class="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-white outline-none">
             <option value="standard">标准定投</option>
             <option value="ema_deviation">EMA20 均线偏离</option>
             <option value="rsi_dynamic">RSI 动态定投</option>
             <option value="ahr999">AHR999 囤币指标 (BTC Only)</option>
             <option value="fear_greed">恐惧贪婪指数</option>
             <option value="value_averaging">固定市值法 (Value Averaging)</option>
           </select>
        </div>

        <div>
           <label class="block text-gray-400 text-xs font-bold mb-1">时区</label>
           <select v-model="config.timezone" class="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-white outline-none">
             <option value="UTC">UTC</option>
             <option value="Asia/Shanghai">Asia/Shanghai (北京)</option>
             <option value="America/New_York">America/New_York</option>
             <option value="Europe/London">Europe/London</option>
             <option value="Asia/Tokyo">Asia/Tokyo</option>
           </select>
        </div>

        <div>
          <label class="block text-gray-400 text-xs font-bold mb-1">
              {{ config.strategy === 'value_averaging' ? '每日目标市值增量 ($)' : '每日基础投入 ($)' }}
          </label>
          <input v-model.number="config.amount" type="number" class="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-white outline-none" />
        </div>

        <!-- Strategy Params (Conditional) -->
        <div v-if="config.strategy !== 'standard' && config.strategy !== 'value_averaging'">
           <label class="block text-gray-400 text-xs font-bold mb-1 flex justify-between">
              <span>强度系数 (Strength)</span>
              <span class="text-gray-500 font-normal">
                  {{ 
                      config.strategy === 'ema_deviation' ? '推荐: 2.0 - 5.0' :
                      config.strategy === 'rsi_dynamic' ? '推荐: 1.0 - 3.0' :
                      config.strategy === 'ahr999' ? '推荐: 0.5 - 2.0' :
                      config.strategy === 'fear_greed' ? '推荐: 1.0 - 3.0' : ''
                  }}
              </span>
           </label>
           <input v-model.number="config.strategy_params.multiplier" type="number" step="0.1" class="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-white outline-none" />
        </div>
        
        <button @click="runSimulation" :disabled="loading" class="bg-gradient-to-r from-green-600 to-teal-600 hover:opacity-90 text-white px-6 py-2 rounded-lg font-bold transition flex items-center justify-center disabled:opacity-50 col-span-1 md:col-span-2">
          <span v-if="loading" class="mr-2 animate-spin">⟳</span>
          计算收益
        </button>
      </div>
    </div>

    <!-- Market Indicators Card -->
    <div class="bg-gray-800 rounded-xl border border-gray-700 p-4">
       <h3 class="text-sm font-bold mb-3 flex items-center">
         <ChartBarIcon class="w-5 h-5 mr-1.5 text-blue-400" />
         市场概览
       </h3>
       
       <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <!-- 当前币价 -->
          <div class="text-center">
             <div class="text-gray-400 text-xs uppercase mb-1">当前币价</div>
             <div class="text-2xl font-bold text-blue-400">${{ result ? (result.current_price || 0).toFixed(2) : '--' }}</div>
          </div>
          
          <!-- RSI -->
          <div class="text-center">
             <div class="text-gray-400 text-xs uppercase mb-1">RSI (14) 日线</div>
             <div class="text-2xl font-bold text-purple-400">{{ marketData.rsi || '--' }}</div>
          </div>
          
          <!-- 恐惧贪婪指数 -->
          <div class="text-center">
             <div class="text-gray-400 text-xs uppercase mb-1">恐惧贪婪指数</div>
             <div class="text-2xl font-bold" :class="marketData.sentiment >= 50 ? 'text-green-400' : 'text-red-400'">
               {{ marketData.sentiment || '--' }}
             </div>
             <div class="text-xs text-gray-500 mt-0.5">{{ marketData.sentimentLabel || '' }}</div>
          </div>
       </div>
    </div>

    <!-- Results - 统一的资产概览 (Always visible) -->
    <div class="bg-gray-800 rounded-xl border border-gray-700 p-4">
       <h3 class="text-sm font-bold mb-3 pb-2 border-b border-gray-700 flex items-center">
         <WalletIcon class="w-5 h-5 mr-1.5 text-yellow-400" />
         资产概览
       </h3>
       
       <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <!-- 移除了当前币价，现在只有6个指标 -->
          
          <!-- 1. 平均成本 -->
          <div class="text-center">
             <div class="text-gray-400 text-xs uppercase mb-1">平均成本</div>
             <div class="text-xl font-bold text-yellow-400">${{ result ? (result.average_cost || 0).toFixed(2) : '--' }}</div>
          </div>
          
          <!-- 2. ROI -->
          <div class="text-center">
             <div class="text-gray-400 text-xs uppercase mb-1">收益率</div>
             <div class="text-xl font-bold" :class="result && (result.roi || 0) >= 0 ? 'text-green-400' : 'text-red-400'">
               {{ result ? (result.roi || 0).toFixed(2) : '--' }}%
             </div>
          </div>
          
          <!-- 3. 总投入 -->
          <div class="text-center">
             <div class="text-gray-400 text-xs uppercase mb-1">总投入</div>
             <div class="text-xl font-bold text-white">${{ result ? (result.total_invested || 0).toFixed(2) : '--' }}</div>
          </div>
          
          <!-- 4. 当前价值 -->
          <div class="text-center">
             <div class="text-gray-400 text-xs uppercase mb-1">当前价值</div>
             <div class="text-xl font-bold text-white">${{ result ? (result.final_value || 0).toFixed(2) : '--' }}</div>
          </div>
          
          <!-- 5. 持仓数量 -->
          <div class="text-center">
             <div class="text-gray-400 text-xs uppercase mb-1">持仓数量</div>
             <div class="text-xl font-bold text-white">{{ result ? (result.total_coins || 0).toFixed(6) : '--' }}</div>
          </div>
          
          <!-- 6. 定投天数 -->
          <div class="text-center">
             <div class="text-gray-400 text-xs uppercase mb-1">定投天数</div>
             <div class="text-xl font-bold text-gray-300">{{ result ? (result.total_days || 0) : '--' }}</div>
          </div>
       </div>
    </div>

    <!-- Charts Area - 3 Charts Layout (Always visible) -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <!-- 1. ROI Trend Chart -->
        <div class="bg-gray-800 rounded-xl border border-gray-700 p-3">
            <h3 class="text-xs font-bold mb-2 text-gray-400">收益率趋势</h3>
            <div class="h-72">
                <canvas ref="roiChartCanvas"></canvas>
            </div>
        </div>
        
        <!-- 2. Price vs Avg Cost Chart -->
        <div class="bg-gray-800 rounded-xl border border-gray-700 p-3">
            <h3 class="text-xs font-bold mb-2 text-gray-400">价格 vs 成本走势</h3>
            <div class="h-72">
                <canvas ref="priceChartCanvas"></canvas>
            </div>
        </div>
        
        <!-- 3. Daily Investment Amount Chart -->
        <div class="bg-gray-800 rounded-xl border border-gray-700 p-3">
            <h3 class="text-xs font-bold mb-2 text-gray-400">每日定投金额</h3>
            <div class="h-72">
                <canvas ref="investmentChartCanvas"></canvas>
            </div>
        </div>
    </div>

  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch, nextTick } from 'vue'
import axios from 'axios'
import { Chart, registerables } from 'chart.js'
import { BanknotesIcon, ChartBarIcon, WalletIcon } from '@heroicons/vue/24/outline'

// Register Chart.js components
Chart.register(...registerables)

const config = reactive({
    symbol: 'BTC/USDT',
    amount: 100,
    start_date: '2025-04-25',
    investment_time: '23:00',
    timezone: 'Asia/Shanghai', // Default, will be auto-detected
    strategy: 'standard', // standard, ema_deviation
    strategy_params: {
        multiplier: 3
    }
})

// Auto-set recommended multiplier when strategy changes
watch(() => config.strategy, (newVal) => {
    if (newVal === 'ema_deviation') {
        config.strategy_params.multiplier = 3.0
    } else if (['rsi_dynamic', 'fear_greed', 'ahr999'].includes(newVal)) {
        config.strategy_params.multiplier = 1.0
    }
})

// Auto-detect timezone
onMounted(() => {
    try {
        const userTz = Intl.DateTimeFormat().resolvedOptions().timeZone
        if (userTz) {
            config.timezone = userTz
        }
    } catch (e) {
        console.warn('Timezone detection failed:', e)
    }
    fetchMarketIndicators()
})


const loading = ref(false)
const result = ref(null)
const marketData = reactive({
    rsi: null,
    sentiment: null,
    sentimentLabel: ''
})
const roiChartCanvas = ref(null)
const priceChartCanvas = ref(null)
const investmentChartCanvas = ref(null)
let roiChart = null
let priceChart = null
let investmentChart = null

const renderCharts = () => {
    if (!result.value || !result.value.history) return
    
    const history = result.value.history
    const labels = history.map(h => h.date)
    
    nextTick(() => {
        // 1. ROI Trend Chart with dynamic colors
        if (roiChartCanvas.value) {
            if (roiChart) roiChart.destroy()
            
            const ctx = roiChartCanvas.value.getContext('2d')
            const roiData = history.map(h => h.roi)
            
            roiChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'ROI (%)',
                        data: roiData,
                        borderColor: (context) => {
                            const value = context.parsed?.y
                            return value >= 0 ? 'rgb(16, 185, 129)' : 'rgb(239, 68, 68)'
                        },
                        backgroundColor: (context) => {
                            const value = context.parsed?.y
                            return value >= 0 ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)'
                        },
                        segment: {
                            borderColor: (ctx) => {
                                const curr = ctx.p1.parsed.y
                                return curr >= 0 ? 'rgb(16, 185, 129)' : 'rgb(239, 68, 68)'
                            },
                            backgroundColor: (ctx) => {
                                const curr = ctx.p1.parsed.y
                                return curr >= 0 ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)'
                            }
                        },
                        fill: true,
                        tension: 0.4,
                        pointRadius: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: (context) => `ROI: ${context.parsed.y.toFixed(2)}%`
                            }
                        }
                    },
                    scales: {
                        x: { 
                            display: true,
                            ticks: { maxTicksLimit: 6, color: '#6b7280', font: { size: 10 } },
                            grid: { color: '#374151', display: false }
                        },
                        y: { 
                            display: true,
                            ticks: { color: '#6b7280', font: { size: 10 } },
                            grid: { color: '#374151' }
                        }
                    }
                }
            })
        }
        
        // 2. Price vs Avg Cost Chart
        if (priceChartCanvas.value) {
            if (priceChart) priceChart.destroy()
            
            const ctx = priceChartCanvas.value.getContext('2d')
            priceChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'BTC Price',
                            data: history.map(h => h.price),
                            borderColor: 'rgb(59, 130, 246)',
                            backgroundColor: 'rgba(59, 130, 246, 0.1)',
                            tension: 0.4,
                            pointRadius: 0,
                            yAxisID: 'y'
                        },
                        {
                            label: 'Average Cost',
                            data: history.map(h => h.avg_cost),
                            borderColor: 'rgb(251, 191, 36)',
                            backgroundColor: 'rgba(251, 191, 36, 0.1)',
                            tension: 0.4,
                            pointRadius: 0,
                            yAxisID: 'y'
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: { mode: 'index', intersect: false },
                    plugins: {
                        legend: {
                            display: true,
                            labels: { color: '#9ca3af', boxWidth: 20 }
                        }
                    },
                    scales: {
                        x: { 
                            ticks: { maxTicksLimit: 6, color: '#6b7280', font: { size: 10 } },
                            grid: { color: '#374151', display: false }
                        },
                        y: { 
                            type: 'linear',
                            display: true,
                            position: 'left',
                            ticks: { color: '#6b7280', font: { size: 10 } },
                            grid: { color: '#374151' }
                        }
                    }
                }
            })
        }
        
        // 3. Daily Investment Amount Chart (Bar)
        if (investmentChartCanvas.value) {
            if (investmentChart) investmentChart.destroy()
            
            const ctx = investmentChartCanvas.value.getContext('2d')
            investmentChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: '投入金额',
                        data: history.map(h => h.invested - (history[history.indexOf(h) - 1]?.invested || 0)),
                        backgroundColor: 'rgba(167, 139, 250, 0.6)',
                        borderColor: 'rgb(167, 139, 250)',
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: (context) => `投入: $${context.parsed.y.toFixed(2)}`
                            }
                        }
                    },
                    scales: {
                        x: { 
                            ticks: { maxTicksLimit: 6, color: '#6b7280', font: { size: 10 } },
                            grid: { color: '#374151', display: false }
                        },
                        y: { 
                            ticks: { color: '#6b7280', font: { size: 10 } },
                            grid: { color: '#374151' }
                        }
                    }
                }
            })
        }
    })
}

const fetchMarketIndicators = async () => {
    try {
        // Get RSI from realtime data
        const realtimeRes = await axios.get('/api/realtime', {
            params: { symbol: config.symbol, timeframe: '1d', limit: 100 }
        })
        if (realtimeRes.data && realtimeRes.data.indicators) {
            marketData.rsi = realtimeRes.data.indicators.rsi?.toFixed(2) || '--'
        }
        
        // Get Fear & Greed
        const sentimentRes = await axios.get('/api/market/sentiment')
        if (sentimentRes.data && sentimentRes.data.value) {
            marketData.sentiment = sentimentRes.data.value
            marketData.sentimentLabel = sentimentRes.data.value_classification || ''
        }
    } catch (e) {
        console.warn('Failed to fetch market indicators:', e)
    }
}

const runSimulation = async () => {
    loading.value = true
    try {
        const response = await axios.post('/api/tools/dca_simulate', config)
        result.value = response.data
        
        // 添加当前币价
        if (typeof response.data.current_price !== 'undefined') {
             result.value.current_price = response.data.current_price
        } else if (response.data.history && response.data.history.length > 0) {
            // Fallback
            result.value.current_price = response.data.history[response.data.history.length - 1].price
        }

        if (response.data.history) {
            result.value.total_days = response.data.history.length
        }
        
        // Fetch market indicators
        await fetchMarketIndicators()
        
        console.log('DCA Response:', response.data)
        
        // Render charts after data is ready
        renderCharts()
        
    } catch (e) {
        console.error('DCA Error:', e)
        alert("Simulation failed: " + e.message)
    } finally {
        loading.value = false
    }
}


</script>
