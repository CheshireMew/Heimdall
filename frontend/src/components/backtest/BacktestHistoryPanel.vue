<template>
  <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 overflow-hidden flex flex-col min-h-[320px] transition-colors">
    <div class="flex items-center justify-between gap-3 mb-4">
      <h2 class="text-xl font-bold text-gray-900 dark:text-white">{{ $t('backtest.recent') }}</h2>
      <div class="text-xs text-gray-500 dark:text-gray-400">{{ $t('backtest.selectForCompareHint') }}</div>
    </div>
    <div class="overflow-y-auto flex-1 space-y-2">
      <div
        v-for="run in page.history"
        :key="run.id"
        class="flex justify-between items-start p-3 bg-gray-50 dark:bg-gray-900 rounded cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 transition border border-gray-200 dark:border-gray-800"
        @click="page.loadResult(run.id)"
      >
        <div class="flex gap-3">
          <label class="pt-1" @click.stop>
            <input :checked="page.compareRunIds.includes(run.id)" type="checkbox" @change="page.toggleCompareRun(run.id)" />
          </label>
          <div>
            <div class="font-bold text-blue-600 dark:text-blue-400">{{ page.portfolioLabel(run) }}</div>
            <div class="text-xs text-gray-500 mt-1">
              {{ run.metadata?.strategy_name || '-' }} · v{{ run.metadata?.strategy_version || '-' }} · {{ run.timeframe }}
            </div>
            <div class="text-xs text-gray-400 mt-1">{{ formatDateTime(run.created_at) }}</div>
          </div>
        </div>
        <div class="text-right">
          <div class="text-sm font-bold" :class="page.profitColorClass(run.report?.profit_pct)">{{ formatPercent(run.report?.profit_pct) }}</div>
          <div class="text-xs text-gray-500">
            {{ formatNumber(run.report?.total_trades ?? run.metrics.total_signals) }} {{ $t('backtest.totalTrades') }}
          </div>
          <div class="text-xs text-gray-500">{{ formatPercent(run.report?.max_drawdown_pct) }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { formatDateTime, formatNumber, formatPercent } from '@/modules/backtest/format'
import type { BacktestPageState } from '@/modules/backtest/useBacktestPage'

const props = defineProps<{ page: BacktestPageState }>()
const page = props.page
</script>
