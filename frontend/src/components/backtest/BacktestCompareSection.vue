<template>
  <section class="grid grid-cols-1 xl:grid-cols-2 gap-6">
    <div class="rounded-xl border border-gray-200 dark:border-gray-700 p-4 space-y-4">
      <div class="flex items-center justify-between gap-3">
        <div class="text-sm font-bold text-gray-900 dark:text-white">{{ $t('backtest.runCompare') }}</div>
        <div class="text-xs text-gray-500 dark:text-gray-400">{{ $t('backtest.selectForCompareHint') }}</div>
      </div>
      <template v-if="page.selectedCompareRuns.length">
        <div class="h-[260px]">
          <BacktestMetricCompareChart :categories="page.recentRunCompare.performance.categories" :series="page.recentRunCompare.performance.series" :dark="page.isDark" />
        </div>
        <div class="h-[260px]">
          <BacktestMetricCompareChart :categories="page.recentRunCompare.quality.categories" :series="page.recentRunCompare.quality.series" :dark="page.isDark" />
        </div>
        <div class="overflow-x-auto">
          <table class="min-w-full text-sm">
            <thead>
              <tr class="text-left text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-gray-700">
                <th class="py-2 pr-4">{{ $t('backtest.runLabel') }}</th>
                <th class="py-2 pr-4">{{ $t('backtest.totalReturn') }}</th>
                <th class="py-2 pr-4">{{ $t('backtest.maxDrawdown') }}</th>
                <th class="py-2 pr-4">{{ $t('backtest.sharpe') }}</th>
                <th class="py-2 pr-4">{{ $t('backtest.winRate') }}</th>
                <th class="py-2">{{ $t('backtest.totalTrades') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="run in page.selectedCompareRuns" :key="run.id" class="border-b border-gray-100 dark:border-gray-800 text-gray-700 dark:text-gray-200">
                <td class="py-2 pr-4">{{ page.compareRunLabel(run) }}</td>
                <td class="py-2 pr-4" :class="page.profitColorClass(run.report?.profit_pct)">{{ formatPercent(run.report?.profit_pct) }}</td>
                <td class="py-2 pr-4 text-red-600 dark:text-red-400">{{ formatPercent(run.report?.max_drawdown_pct) }}</td>
                <td class="py-2 pr-4">{{ formatMetric(run.report?.sharpe) }}</td>
                <td class="py-2 pr-4">{{ formatPercent(run.report?.win_rate) }}</td>
                <td class="py-2">{{ formatNumber(run.report?.total_trades) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
      <div v-else class="text-sm text-gray-500 dark:text-gray-400">{{ $t('backtest.noCompareSelection') }}</div>
    </div>

    <div class="rounded-xl border border-gray-200 dark:border-gray-700 p-4 space-y-4">
      <div class="flex items-center justify-between gap-3">
        <div class="text-sm font-bold text-gray-900 dark:text-white">{{ $t('backtest.versionCompare') }}</div>
        <div class="text-xs text-gray-500 dark:text-gray-400">{{ $t('backtest.versionCompareHint') }}</div>
      </div>
      <div v-if="page.versionCompareOptions.length" class="grid grid-cols-1 md:grid-cols-2 gap-2">
        <label
          v-for="item in page.versionCompareOptions"
          :key="item.version"
          class="flex items-center justify-between gap-3 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/40 px-3 py-2"
        >
          <div class="flex items-center gap-2">
            <input :checked="page.versionCompareSelections.includes(item.version)" type="checkbox" @change="page.toggleVersionCompare(item.version)" />
            <span class="font-semibold text-gray-900 dark:text-white">v{{ item.version }}</span>
          </div>
          <div class="text-right">
            <div class="text-xs text-gray-500 dark:text-gray-400">{{ item.name }}</div>
            <div class="text-xs" :class="page.profitColorClass(item.run.report?.profit_pct)">{{ formatPercent(item.run.report?.profit_pct) }}</div>
          </div>
        </label>
      </div>
      <template v-if="page.selectedVersionCompareRuns.length">
        <div class="h-[260px]">
          <BacktestMetricCompareChart :categories="page.versionRunCompare.performance.categories" :series="page.versionRunCompare.performance.series" :dark="page.isDark" />
        </div>
        <div class="h-[260px]">
          <BacktestMetricCompareChart :categories="page.versionRunCompare.quality.categories" :series="page.versionRunCompare.quality.series" :dark="page.isDark" />
        </div>
        <div class="overflow-x-auto">
          <table class="min-w-full text-sm">
            <thead>
              <tr class="text-left text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-gray-700">
                <th class="py-2 pr-4">{{ $t('backtest.version') }}</th>
                <th class="py-2 pr-4">{{ $t('backtest.latestVersionRun') }}</th>
                <th class="py-2 pr-4">{{ $t('backtest.totalReturn') }}</th>
                <th class="py-2 pr-4">{{ $t('backtest.maxDrawdown') }}</th>
                <th class="py-2 pr-4">{{ $t('backtest.sharpe') }}</th>
                <th class="py-2">{{ $t('backtest.totalTrades') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="run in page.selectedVersionCompareRuns" :key="run.id" class="border-b border-gray-100 dark:border-gray-800 text-gray-700 dark:text-gray-200">
                <td class="py-2 pr-4">v{{ run.metadata?.strategy_version || '-' }}</td>
                <td class="py-2 pr-4">{{ formatDateTime(run.created_at) }}</td>
                <td class="py-2 pr-4" :class="page.profitColorClass(run.report?.profit_pct)">{{ formatPercent(run.report?.profit_pct) }}</td>
                <td class="py-2 pr-4 text-red-600 dark:text-red-400">{{ formatPercent(run.report?.max_drawdown_pct) }}</td>
                <td class="py-2 pr-4">{{ formatMetric(run.report?.sharpe) }}</td>
                <td class="py-2">{{ formatNumber(run.report?.total_trades) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
      <div v-else class="text-sm text-gray-500 dark:text-gray-400">{{ $t('backtest.noVersionCompareData') }}</div>
    </div>
  </section>
</template>

<script setup lang="ts">
import BacktestMetricCompareChart from '@/components/BacktestMetricCompareChart.vue'
import { formatDateTime, formatMetric, formatNumber, formatPercent } from '@/modules/backtest/format'
import type { BacktestPageState } from '@/modules/backtest/useBacktestPage'

const props = defineProps<{ page: BacktestPageState }>()
const page = props.page
</script>
