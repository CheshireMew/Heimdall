<template>
  <div class="h-full flex flex-col p-6 overflow-y-auto">
    <div class="flex-1 min-h-[500px] bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden flex flex-col md:flex-row shadow-lg transition-colors">
      <aside class="w-full md:w-80 border-b md:border-b-0 md:border-r border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 transition-colors">
        <div class="p-4 border-b border-gray-200 dark:border-gray-700">
          <div class="text-lg font-semibold text-gray-900 dark:text-white">智能开单</div>
        </div>

        <div class="space-y-4 p-4">
          <div class="grid grid-cols-2 gap-3">
            <label class="space-y-1">
              <span class="text-xs text-gray-500 dark:text-gray-400">初始保证金 ({{ page.displayCurrency }})</span>
              <input
                v-model.number="page.displayAccountSize"
                class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-semibold text-gray-900 outline-none transition focus:border-blue-500 dark:border-gray-700 dark:bg-gray-800 dark:text-white"
                type="number"
                min="0"
              />
            </label>
            <label class="space-y-1">
              <span class="text-xs text-gray-500 dark:text-gray-400">风格</span>
            <select
              v-model="page.tradeStyle"
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
              v-model="page.decisionMode"
              class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-semibold text-gray-900 outline-none transition focus:border-blue-500 dark:border-gray-700 dark:bg-gray-800 dark:text-white"
            >
              <option value="rules">内置规则</option>
              <option value="ai">AI 判断</option>
            </select>
          </label>

          <label class="block space-y-1">
            <span class="text-xs text-gray-500 dark:text-gray-400">策略</span>
            <select
              v-model="page.tradeStrategy"
              class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-semibold text-gray-900 outline-none transition focus:border-blue-500 dark:border-gray-700 dark:bg-gray-800 dark:text-white"
            >
              <option>最大收益</option>
              <option>稳健突破</option>
              <option>回撤反转</option>
            </select>
          </label>

          <button
            class="w-full rounded-lg bg-gray-900 px-4 py-3 text-sm font-semibold text-white transition hover:bg-gray-700 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-white dark:text-gray-900 dark:hover:bg-gray-200"
            :disabled="page.tradeSetupLoading || !page.canAskTradeSetup"
            @click="page.askTradeSetup"
          >
            {{ page.tradeSetupLoading ? '分析中...' : page.canAskTradeSetup ? '询问多 / 空' : '当前标的不支持' }}
          </button>

          <div v-if="page.tradeSetupResult" class="rounded-lg border border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-800">
            <template v-if="page.tradeSetupResult.setup">
              <div class="flex items-center justify-between">
                <span :class="['text-sm font-semibold', page.tradeSetupResult.setup.side === 'long' ? 'text-emerald-600' : 'text-rose-600']">
                  {{ page.tradeSetupResult.setup.side === 'long' ? '做多' : '做空' }}
                </span>
                <span class="text-xs text-gray-500 dark:text-gray-400">
                  {{ page.tradeSetupResult.setup.source === 'ai' ? 'AI' : '规则' }} {{ page.tradeSetupResult.setup.confidence }}%
                </span>
              </div>
              <div class="mt-3 grid grid-cols-2 gap-2 text-sm">
                <div class="text-gray-500 dark:text-gray-400">开仓</div>
                <div class="text-right font-semibold text-gray-900 dark:text-white">{{ page.formatTradePrice(page.tradeSetupResult.setup.entry) }}</div>
                <div class="text-gray-500 dark:text-gray-400">目标</div>
                <div class="text-right font-semibold text-emerald-600">{{ page.formatTradePrice(page.tradeSetupResult.setup.target) }}</div>
                <div class="text-gray-500 dark:text-gray-400">止损</div>
                <div class="text-right font-semibold text-rose-600">{{ page.formatTradePrice(page.tradeSetupResult.setup.stop) }}</div>
                <div class="text-gray-500 dark:text-gray-400">盈亏比</div>
                <div class="text-right font-semibold text-gray-900 dark:text-white">{{ page.tradeSetupResult.setup.risk_reward.toFixed(2) }}</div>
              </div>
            </template>
            <div v-else class="text-sm text-gray-600 dark:text-gray-300">{{ page.tradeSetupResult.reason }}</div>
          </div>

          <div v-if="page.tradeSetupError" class="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700 dark:border-rose-900/60 dark:bg-rose-950/30 dark:text-rose-200">
            {{ page.tradeSetupError }}
          </div>
        </div>
      </aside>

      <div class="flex min-w-0 flex-1 flex-col">
      <div class="p-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center bg-gray-50/50 dark:bg-gray-800/50 transition-colors">
         <div class="flex items-center space-x-4">
            <SymbolSearchBox
              v-model="page.currentSymbol"
              class="w-72"
              placeholder="Search symbol"
              @select="page.handleSymbolSelect"
            />
            <div class="flex space-x-1 bg-gray-200 dark:bg-gray-900 rounded-lg p-1 transition-colors">
                <button v-for="tf in page.visibleTimeframes" :key="tf"
                    @click="page.currentTimeframe = tf"
                    :class="['px-3 py-1 text-xs rounded-md transition-all', page.currentTimeframe === tf ? 'bg-white dark:bg-blue-600 shadow text-blue-600 dark:text-white' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-800']">
                    {{ tf }}
                </button>
            </div>
         </div>
      </div>

      <div class="flex-1 relative">
         <div v-if="page.loadingMore" class="absolute top-4 left-1/2 transform -translate-x-1/2 z-20 bg-blue-600 text-white px-3 py-1 rounded-full text-xs shadow-lg flex items-center">
            <span class="animate-spin mr-2">&#10227;</span> {{ $t('dashboard.loadingHistory') }}
         </div>
         <TradingViewChart
            :data="page.chartData"
            :volume-data="page.volumeData"
            :colors="page.chartColors"
            :trade-setup="page.activeTradeSetup"
            @load-more="page.loadMore"
         />
      </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineOptions({ name: 'Dashboard' })

import TradingViewChart from '@/components/TradingViewChart.vue'
import SymbolSearchBox from '@/components/SymbolSearchBox.vue'
import { useDashboardPage } from '@/modules/market'

const page = useDashboardPage()

</script>
