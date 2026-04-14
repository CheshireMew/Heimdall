<template>
  <div class="h-full flex flex-col p-6 overflow-y-auto">
    <div class="flex-1 min-h-[500px] bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden flex flex-col md:flex-row shadow-lg transition-colors">
      <aside class="w-full md:w-80 border-b md:border-b-0 md:border-r border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 transition-colors">
        <div class="p-4 border-b border-gray-200 dark:border-gray-700">
          <div class="flex items-center justify-between">
            <div class="text-lg font-semibold text-gray-900 dark:text-white">AI Copilot</div>
            <div class="text-sm font-medium text-gray-500 dark:text-gray-400">Autopilot</div>
          </div>
        </div>

        <div class="space-y-4 p-4">
          <div class="grid grid-cols-2 gap-3">
            <label class="space-y-1">
              <span class="text-xs text-gray-500 dark:text-gray-400">初始保证金 ({{ displayCurrency }})</span>
              <input
                v-model.number="displayAccountSize"
                class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-semibold text-gray-900 outline-none transition focus:border-blue-500 dark:border-gray-700 dark:bg-gray-800 dark:text-white"
                type="number"
                min="0"
              />
            </label>
            <label class="space-y-1">
              <span class="text-xs text-gray-500 dark:text-gray-400">风格</span>
              <select
                v-model="tradeStyle"
                class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-semibold text-gray-900 outline-none transition focus:border-blue-500 dark:border-gray-700 dark:bg-gray-800 dark:text-white"
              >
                <option>Scalping</option>
                <option>Intraday</option>
                <option>Swing</option>
              </select>
            </label>
          </div>

          <label class="block space-y-1">
            <span class="text-xs text-gray-500 dark:text-gray-400">判断方式</span>
            <select
              v-model="decisionMode"
              class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-semibold text-gray-900 outline-none transition focus:border-blue-500 dark:border-gray-700 dark:bg-gray-800 dark:text-white"
            >
              <option value="rules">内置规则</option>
              <option value="ai">AI 判断</option>
            </select>
          </label>

          <label class="block space-y-1">
            <span class="text-xs text-gray-500 dark:text-gray-400">策略</span>
            <select
              v-model="tradeStrategy"
              class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-semibold text-gray-900 outline-none transition focus:border-blue-500 dark:border-gray-700 dark:bg-gray-800 dark:text-white"
            >
              <option>最大收益</option>
              <option>稳健突破</option>
              <option>回撤反转</option>
            </select>
          </label>

          <button
            class="w-full rounded-lg bg-gray-900 px-4 py-3 text-sm font-semibold text-white transition hover:bg-gray-700 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-white dark:text-gray-900 dark:hover:bg-gray-200"
            :disabled="tradeSetupLoading || !canAskTradeSetup"
            @click="askTradeSetup"
          >
            {{ tradeSetupLoading ? '分析中...' : canAskTradeSetup ? '询问多 / 空' : '当前标的不支持' }}
          </button>

          <div v-if="tradeSetupResult" class="rounded-lg border border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-800">
            <template v-if="tradeSetupResult.setup">
              <div class="flex items-center justify-between">
                <span :class="['text-sm font-semibold', tradeSetupResult.setup.side === 'long' ? 'text-emerald-600' : 'text-rose-600']">
                  {{ tradeSetupResult.setup.side === 'long' ? '做多' : '做空' }}
                </span>
                <span class="text-xs text-gray-500 dark:text-gray-400">
                  {{ tradeSetupResult.setup.source === 'ai' ? 'AI' : '规则' }} {{ tradeSetupResult.setup.confidence }}%
                </span>
              </div>
              <div class="mt-3 grid grid-cols-2 gap-2 text-sm">
                <div class="text-gray-500 dark:text-gray-400">开仓</div>
                <div class="text-right font-semibold text-gray-900 dark:text-white">{{ formatTradePrice(tradeSetupResult.setup.entry) }}</div>
                <div class="text-gray-500 dark:text-gray-400">目标</div>
                <div class="text-right font-semibold text-emerald-600">{{ formatTradePrice(tradeSetupResult.setup.target) }}</div>
                <div class="text-gray-500 dark:text-gray-400">止损</div>
                <div class="text-right font-semibold text-rose-600">{{ formatTradePrice(tradeSetupResult.setup.stop) }}</div>
                <div class="text-gray-500 dark:text-gray-400">盈亏比</div>
                <div class="text-right font-semibold text-gray-900 dark:text-white">{{ tradeSetupResult.setup.risk_reward.toFixed(2) }}</div>
              </div>
            </template>
            <div v-else class="text-sm text-gray-600 dark:text-gray-300">{{ tradeSetupResult.reason }}</div>
          </div>

          <div v-if="tradeSetupError" class="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700 dark:border-rose-900/60 dark:bg-rose-950/30 dark:text-rose-200">
            {{ tradeSetupError }}
          </div>
        </div>
      </aside>

      <div class="flex min-w-0 flex-1 flex-col">
      <div class="p-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center bg-gray-50/50 dark:bg-gray-800/50 transition-colors">
         <div class="flex items-center space-x-4">
            <SymbolSearchBox
              v-model="currentSymbol"
              class="w-72"
              placeholder="Search symbol"
              @select="handleSymbolSelect"
            />
            <div class="flex space-x-1 bg-gray-200 dark:bg-gray-900 rounded-lg p-1 transition-colors">
                <button v-for="tf in visibleTimeframes" :key="tf"
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
            :trade-setup="activeTradeSetup"
            @load-more="loadMore"
         />
      </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineOptions({ name: 'Dashboard' })

import { ref, onMounted, computed, watch } from 'vue'
import TradingViewChart from '@/components/TradingViewChart.vue'
import SymbolSearchBox from '@/components/SymbolSearchBox.vue'
import { useTheme } from '@/composables/useTheme'
import { useMoney } from '@/composables/useMoney'
import { marketApi, useKlineSeries } from '@/modules/market'

const { theme } = useTheme()
const { displayCurrency, formatMoney, formatDisplayNumber, fromDisplayAmount } = useMoney()

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
const currentAssetClass = ref('crypto')
const visibleTimeframes = computed(() => currentAssetClass.value === 'index' ? ['1d'] : timeframes)
const currentSymbol = ref('BTC/USDT')
const currentTimeframe = ref('1h')
const accountSize = ref(1000)
const tradeStyle = ref('Scalping')
const tradeStrategy = ref('最大收益')
const decisionMode = ref('rules')
const tradeSetupLoading = ref(false)
const tradeSetupResult = ref(null)
const tradeSetupError = ref('')
const activeTradeSetup = computed(() => tradeSetupResult.value?.setup || null)
const canAskTradeSetup = computed(() => currentAssetClass.value === 'crypto')
const displayAccountSize = computed({
    get: () => Number(formatDisplayNumber(accountSize.value, 'USDT', 2) || 0),
    set: (value) => {
        accountSize.value = fromDisplayAmount(value, 'USDT') ?? accountSize.value
    }
})
const {
    chartData,
    volumeData,
    loadingMore,
    fetchLatest,
    loadMore,
} = useKlineSeries(currentSymbol, currentTimeframe)

const handleSymbolSelect = (item) => {
    currentAssetClass.value = item.asset_class
    if (item.asset_class === 'index') currentTimeframe.value = '1d'
}

const formatTradePrice = (value) => {
    if (!Number.isFinite(value)) return '-'
    if (value >= 1000) return formatMoney(value, 'USDT', { maximumFractionDigits: 1 })
    if (value >= 1) return formatMoney(value, 'USDT', { maximumFractionDigits: 3 })
    return formatMoney(value, 'USDT', { maximumSignificantDigits: 4 })
}

const askTradeSetup = async () => {
    if (!canAskTradeSetup.value) return
    tradeSetupLoading.value = true
    tradeSetupError.value = ''
    try {
        const response = await marketApi.getTradeSetup({
            symbol: currentSymbol.value,
            timeframe: currentTimeframe.value,
            limit: 120,
            account_size: accountSize.value,
            style: tradeStyle.value,
            strategy: tradeStrategy.value,
            mode: decisionMode.value,
        })
        tradeSetupResult.value = response.data
    } catch (error) {
        console.error('Trade setup failed', error)
        tradeSetupResult.value = null
        tradeSetupError.value = '暂时无法生成多空方案'
    } finally {
        tradeSetupLoading.value = false
    }
}

watch([currentSymbol, currentTimeframe], () => {
    tradeSetupResult.value = null
    tradeSetupError.value = ''
})

onMounted(() => {
    fetchLatest()
})
</script>
