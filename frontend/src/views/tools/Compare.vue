<template>
  <div class="h-full flex flex-col p-6 space-y-6">
    <!-- Configuration Panel -->
    <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 flex flex-wrap items-end gap-4 transition-colors">
      <div class="flex-1 min-w-[200px]">
        <label class="block text-gray-500 dark:text-gray-400 text-xs font-bold mb-1">{{ $t('compare.symbolA') }}</label>
        <SymbolSearchBox v-model="config.symbolA" output-mode="base" placeholder="Search symbol" @select="handleSymbolSelect" />
      </div>

      <div class="flex items-center justify-center p-2">
         <span class="text-gray-400 dark:text-gray-500 font-bold text-xl">VS</span>
      </div>

      <div class="flex-1 min-w-[200px]">
        <label class="block text-gray-500 dark:text-gray-400 text-xs font-bold mb-1">{{ $t('compare.symbolB') }}</label>
        <SymbolSearchBox v-model="config.symbolB" output-mode="base" placeholder="Search symbol" @select="handleSymbolSelect" />
      </div>

      <div class="w-32">
        <label class="block text-gray-500 dark:text-gray-400 text-xs font-bold mb-1">{{ $t('compare.timeframe') }}</label>
        <select v-model="config.timeframe" class="w-full bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-gray-900 dark:text-white outline-none transition-colors">
          <option value="5m">{{ $t('compare.tf.5m') }}</option>
          <option value="15m">{{ $t('compare.tf.15m') }}</option>
          <option value="1h">{{ $t('compare.tf.1h') }}</option>
          <option value="4h">{{ $t('compare.tf.4h') }}</option>
          <option value="1d">{{ $t('compare.tf.1d') }}</option>
          <option value="1w">{{ $t('compare.tf.1w') }}</option>
          <option value="1M">{{ $t('compare.tf.1M') }}</option>
        </select>
      </div>

      <div class="w-32">
        <label class="block text-gray-500 dark:text-gray-400 text-xs font-bold mb-1">{{ $t('compare.days') }}</label>
        <input v-model.number="config.days" type="number" min="1" max="90" class="w-full bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-gray-900 dark:text-white outline-none transition-colors" />
      </div>

      <button @click="fetchComparisonData" :disabled="loading" class="bg-blue-600 hover:bg-blue-500 text-white px-6 py-2 rounded-lg font-bold transition flex items-center disabled:opacity-50 disabled:cursor-not-allowed">
        <span v-if="loading" class="mr-2 animate-spin">&#10227;</span>
        {{ loading ? $t('compare.analyzing') : $t('compare.compare') }}
      </button>
    </div>

    <!-- Charts Grid -->
    <div class="flex-1 grid grid-cols-2 grid-rows-2 gap-4 min-h-[600px]">

      <!-- Chart A -->
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden flex flex-col relative transition-colors">
        <div class="absolute top-2 left-2 z-10 bg-white/90 dark:bg-gray-900/80 px-2 py-1 rounded text-sm font-bold text-blue-600 dark:text-blue-400 border border-blue-500/30">
          {{ symbolLabel(config.symbolA) }}
        </div>
        <TradingViewChart
          ref="chartARef"
          :data="dataA"
          :colors="{ ...chartColors, upColor: '#3b82f6', downColor: '#1d4ed8' }"
        />
      </div>

      <!-- Chart B -->
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden flex flex-col relative transition-colors">
        <div class="absolute top-2 left-2 z-10 bg-white/90 dark:bg-gray-900/80 px-2 py-1 rounded text-sm font-bold text-purple-600 dark:text-purple-400 border border-purple-500/30">
          {{ symbolLabel(config.symbolB) }}
        </div>
        <TradingViewChart
          ref="chartBRef"
          :data="dataB"
          :colors="{ ...chartColors, upColor: '#a855f7', downColor: '#7e22ce' }"
        />
      </div>

      <!-- Ratio Chart (Full Width) -->
      <div class="col-span-2 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden flex flex-col relative transition-colors">
        <div class="absolute top-2 left-2 z-10 bg-white/90 dark:bg-gray-900/80 px-2 py-1 rounded text-sm font-bold text-green-600 dark:text-green-400 border border-green-500/30">
          {{ $t('compare.ratio') }}: {{ config.symbolA }} / {{ config.symbolB }}
        </div>
        <TradingViewChart
          ref="chartRatioRef"
          :data="dataRatio"
          chart-type="area"
          :colors="chartColors"
        />
      </div>

    </div>
  </div>
</template>

<script setup>
import TradingViewChart from '@/components/TradingViewChart.vue'
import SymbolSearchBox from '@/components/SymbolSearchBox.vue'
import { useComparePage } from '@/modules/tools'

const {
  chartColors,
  config,
  loading,
  dataA,
  dataB,
  dataRatio,
  chartARef,
  chartBRef,
  chartRatioRef,
  fetchComparisonData,
  handleSymbolSelect,
  symbolLabel,
} = useComparePage()
</script>
