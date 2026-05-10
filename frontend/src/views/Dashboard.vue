<template>
  <div class="app-page">
    <div class="app-page-inner-wide flex min-h-full flex-col">
    <div class="app-panel flex min-h-[500px] flex-1 flex-col overflow-hidden transition-colors md:flex-row">
      <aside class="w-full border-b border-stone-200 bg-white transition-colors dark:border-gray-700 dark:bg-gray-900 md:w-80 md:border-b-0 md:border-r">
        <div class="border-b border-stone-200 p-4 dark:border-gray-700">
          <div class="app-section-title">智能开单</div>
        </div>

        <div class="space-y-4 p-4">
          <div class="grid grid-cols-2 gap-3">
            <label class="space-y-1">
              <span class="text-xs text-stone-500 dark:text-gray-400">初始保证金 ({{ page.displayCurrency }})</span>
              <input
                v-model.number="page.displayAccountSize"
                class="app-control w-full"
                type="number"
                min="0"
              />
            </label>
            <label class="space-y-1">
              <span class="text-xs text-stone-500 dark:text-gray-400">风格</span>
            <select
              v-model="page.tradeStyle"
              class="app-control w-full"
            >
                <option>Scalping</option>
                <option>Intraday</option>
                <option>Swing</option>
              </select>
            </label>
          </div>

          <label class="block space-y-1">
            <span class="text-xs text-stone-500 dark:text-gray-400">判断方式</span>
            <select
              v-model="page.decisionMode"
              class="app-control w-full"
            >
              <option value="rules">内置规则</option>
              <option value="ai">AI 判断</option>
            </select>
          </label>

          <label class="block space-y-1">
            <span class="text-xs text-stone-500 dark:text-gray-400">策略</span>
            <select
              v-model="page.tradeStrategy"
              class="app-control w-full"
            >
              <option>最大收益</option>
              <option>稳健突破</option>
              <option>回撤反转</option>
            </select>
          </label>

          <button
            class="app-button-primary w-full px-4 py-3"
            :disabled="page.tradeSetupLoading || !page.canAskTradeSetup"
            @click="page.askTradeSetup"
          >
            {{ page.tradeSetupLoading ? '分析中...' : page.canAskTradeSetup ? '询问多 / 空' : '当前标的不支持' }}
          </button>

          <div v-if="page.tradeSetupResult" class="border border-stone-200 bg-[#fbfaf7] p-4 dark:border-gray-700 dark:bg-gray-800">
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
      <div class="flex items-center justify-between border-b border-stone-200 bg-[#fbfaf7] p-4 transition-colors dark:border-gray-700 dark:bg-gray-800/50">
         <div class="flex items-center space-x-4">
            <SymbolSearchBox
              v-model="page.currentSymbol"
              class="w-72"
              @select="page.handleSymbolSelect"
            />
            <div class="flex space-x-1 border border-stone-200 bg-white p-1 transition-colors dark:border-gray-700 dark:bg-gray-900">
                <button v-for="tf in page.visibleTimeframes" :key="tf"
                    @click="page.currentTimeframe = tf"
                    :class="['px-3 py-1 text-xs transition-all', page.currentTimeframe === tf ? 'bg-[#edf3ee] text-[#0f6b4f] dark:bg-emerald-500 dark:text-slate-950' : 'text-stone-500 hover:bg-stone-100 hover:text-stone-700 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-200']">
                    {{ tf }}
                </button>
            </div>
         </div>
      </div>

      <div class="flex-1 relative">
         <div v-if="page.loadingMore" class="absolute left-1/2 top-4 z-20 flex -translate-x-1/2 transform items-center bg-[#0f6b4f] px-3 py-1 text-xs text-white shadow-lg">
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
  </div>
</template>

<script setup>
defineOptions({ name: 'Dashboard' })

import TradingViewChart from '@/components/TradingViewChart.vue'
import SymbolSearchBox from '@/components/SymbolSearchBox.vue'
import { useDashboardPage } from '@/modules/market'

const page = useDashboardPage()

</script>
