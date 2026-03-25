<template>
  <section class="space-y-5">
    <section class="space-y-3">
      <div>
        <label class="label">{{ $t('backtest.symbols') }}</label>
        <input v-model="page.symbolsText" class="input" type="text" />
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="label">{{ $t('compare.timeframe') }}</label>
          <select v-model="page.config.timeframe" class="input">
            <option v-for="tf in page.timeframes" :key="tf" :value="tf">{{ $t(`compare.tf.${tf}`) }}</option>
          </select>
        </div>
        <div>
          <label class="label">{{ $t('backtest.days') }}</label>
          <input v-model.number="page.config.days" class="input" type="number" min="7" />
        </div>
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="label">{{ $t('backtest.initialCash') }}</label>
          <input v-model.number="page.config.initial_cash" class="input" type="number" min="1" step="1000" />
        </div>
        <div>
          <label class="label">{{ $t('backtest.feeRate') }}</label>
          <input v-model.number="page.config.fee_rate" class="input" type="number" min="0" max="100" step="0.01" />
        </div>
      </div>
    </section>

    <section class="space-y-3">
      <div class="section-title">{{ $t('backtest.portfolioSection') }}</div>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="label">{{ $t('backtest.maxOpenTrades') }}</label>
          <input v-model.number="page.config.portfolio.max_open_trades" class="input" type="number" min="1" max="50" />
        </div>
        <div>
          <label class="label">{{ $t('backtest.positionSize') }}</label>
          <input v-model.number="page.config.portfolio.position_size_pct" class="input" type="number" min="0.1" max="100" step="0.1" />
        </div>
      </div>
      <div>
        <label class="label">{{ $t('backtest.stakeMode') }}</label>
        <select v-model="page.config.portfolio.stake_mode" class="input">
          <option value="fixed">{{ $t('backtest.stakeModeFixed') }}</option>
          <option value="unlimited">{{ $t('backtest.stakeModeUnlimited') }}</option>
        </select>
      </div>
    </section>

    <section class="space-y-3">
      <div class="section-title">{{ $t('backtest.researchSection') }}</div>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="label">{{ $t('backtest.slippage') }}</label>
          <input v-model.number="page.config.research.slippage_bps" class="input" type="number" min="0" step="1" />
        </div>
        <div>
          <label class="label">{{ $t('backtest.fundingRate') }}</label>
          <input v-model.number="page.config.research.funding_rate_daily" class="input" type="number" step="0.01" />
        </div>
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="label">{{ $t('backtest.inSampleRatio') }}</label>
          <input v-model.number="page.config.research.in_sample_ratio" class="input" type="number" min="50" max="100" step="1" />
        </div>
        <div>
          <label class="label">{{ $t('backtest.optimizeTrials') }}</label>
          <input v-model.number="page.config.research.optimize_trials" class="input" type="number" min="0" step="1" />
        </div>
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="label">{{ $t('backtest.optimizeMetric') }}</label>
          <select v-model="page.config.research.optimize_metric" class="input">
            <option v-for="metric in page.optimizeMetrics" :key="metric" :value="metric">{{ metric }}</option>
          </select>
        </div>
        <div>
          <label class="label">{{ $t('backtest.rollingWindows') }}</label>
          <input v-model.number="page.config.research.rolling_windows" class="input" type="number" min="0" step="1" />
        </div>
      </div>
    </section>

    <div class="rounded-lg border border-blue-200 bg-blue-50 px-3 py-2 text-xs text-blue-700 dark:border-blue-800 dark:bg-blue-950/40 dark:text-blue-300">
      Freqtrade research engine
    </div>
    <button :disabled="page.loading || !page.strategies.length" class="btn-primary w-full" @click="page.startBacktest">
      {{ page.loading ? $t('backtest.running') : $t('backtest.run') }}
    </button>
  </section>
</template>

<script setup lang="ts">
import type { BacktestPageState } from '@/modules/backtest/useBacktestPage'

const props = defineProps<{ page: BacktestPageState }>()
const page = props.page
</script>

<style scoped>
.label { @apply block text-gray-500 dark:text-gray-400 text-xs font-bold mb-1; }
.input { @apply w-full bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-gray-900 dark:text-white outline-none focus:border-blue-500 transition-colors; }
.btn-primary { @apply bg-blue-600 hover:bg-blue-500 text-white py-2 rounded-lg font-bold transition disabled:opacity-50; }
.section-title { @apply text-sm font-bold text-gray-900 dark:text-white; }
</style>
