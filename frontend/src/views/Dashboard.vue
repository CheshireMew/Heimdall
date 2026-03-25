<template>
  <div class="h-full flex flex-col p-6 overflow-y-auto">
    <!-- Main Chart Area -->
    <div class="flex-1 min-h-[500px] bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden flex flex-col shadow-lg transition-colors">
      <div class="p-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center bg-gray-50/50 dark:bg-gray-800/50 transition-colors">
         <div class="flex items-center space-x-4">
            <h3 class="font-bold text-lg text-gray-900 dark:text-gray-100 flex items-center">
              <span class="w-2 h-2 rounded-full bg-green-500 mr-2 animate-pulse"></span>
              BTC/USDT
            </h3>
            <div class="flex space-x-1 bg-gray-200 dark:bg-gray-900 rounded-lg p-1 transition-colors">
                <button v-for="tf in timeframes" :key="tf"
                    @click="currentTimeframe = tf"
                    :class="['px-3 py-1 text-xs rounded-md transition-all', currentTimeframe === tf ? 'bg-white dark:bg-blue-600 shadow text-blue-600 dark:text-white' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-800']">
                    {{ tf }}
                </button>
            </div>
         </div>
      </div>

      <div class="flex-1 relative">
         <div v-if="loadingMore" class="absolute top-4 left-1/2 transform -translate-x-1/2 z-20 bg-blue-600 text-white px-3 py-1 rounded-full text-xs shadow-lg flex items-center">
            <span class="animate-spin mr-2">&#10227;</span> {{ $t('dashboard.loadingHistory') }}
         </div>
         <TradingViewChart
            :data="chartData"
            :volume-data="volumeData"
            :colors="chartColors"
            @load-more="loadMore"
         />
      </div>
    </div>
  </div>
</template>

<script setup>
defineOptions({ name: 'Dashboard' })

import { ref, onMounted, computed } from 'vue'
import TradingViewChart from '@/components/TradingViewChart.vue'
import { useTheme } from '@/composables/useTheme'
import { useKlineSeries } from '@/modules/market'

const { theme } = useTheme()

const chartColors = computed(() => {
    const isDark = theme.value === 'dark'
    return {
        bg: isDark ? '#1f2937' : '#ffffff',
        grid: isDark ? '#374151' : '#e5e7eb',
        text: isDark ? '#9ca3af' : '#4b5563',
        upColor: '#10b981',
        downColor: '#ef4444'
    }
})

const timeframes = ['5m', '15m', '1h', '4h', '1d', '1w', '1M']
const currentSymbol = ref('BTC/USDT')
const currentTimeframe = ref('1h')
const {
    chartData,
    volumeData,
    loadingMore,
    fetchLatest,
    loadMore,
} = useKlineSeries(currentSymbol, currentTimeframe)

onMounted(() => {
    fetchLatest()
})
</script>
