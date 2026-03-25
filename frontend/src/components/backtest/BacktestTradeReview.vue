<template>
  <section class="space-y-6">
    <div class="rounded-xl border border-gray-200 dark:border-gray-700 p-4">
      <div class="text-sm font-bold text-gray-900 dark:text-white mb-3">{{ $t('backtest.tradeList') }}</div>
      <div v-if="page.selectedRun.trades?.length" class="overflow-x-auto">
        <table class="min-w-full text-sm">
          <thead>
            <tr class="text-left text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-gray-700">
              <th class="py-2 pr-4">{{ $t('backtest.openedAt') }}</th>
              <th class="py-2 pr-4">{{ $t('backtest.closedAt') }}</th>
              <th class="py-2 pr-4">{{ $t('backtest.symbol') }}</th>
              <th class="py-2 pr-4">{{ $t('backtest.entryPrice') }}</th>
              <th class="py-2 pr-4">{{ $t('backtest.exitPrice') }}</th>
              <th class="py-2 pr-4">{{ $t('backtest.profit') }}</th>
              <th class="py-2 pr-4">{{ $t('backtest.duration') }}</th>
              <th class="py-2">{{ $t('backtest.reason') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="trade in page.selectedRun.trades" :key="trade.id" class="border-b border-gray-100 dark:border-gray-800 text-gray-700 dark:text-gray-200">
              <td class="py-2 pr-4 whitespace-nowrap">{{ formatDateTime(trade.opened_at) }}</td>
              <td class="py-2 pr-4 whitespace-nowrap">{{ formatDateTime(trade.closed_at) }}</td>
              <td class="py-2 pr-4 whitespace-nowrap">{{ trade.pair }}</td>
              <td class="py-2 pr-4 whitespace-nowrap">{{ formatPrice(trade.entry_price) }}</td>
              <td class="py-2 pr-4 whitespace-nowrap">{{ formatPrice(trade.exit_price) }}</td>
              <td class="py-2 pr-4 whitespace-nowrap font-semibold" :class="page.profitColorClass(trade.profit_pct)">
                {{ formatPercent(trade.profit_pct) }} / {{ formatMoney(trade.profit_abs) }}
              </td>
              <td class="py-2 pr-4 whitespace-nowrap">{{ formatDuration(trade.duration_minutes) }}</td>
              <td class="py-2 whitespace-nowrap">{{ trade.exit_reason || '-' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else class="text-sm text-gray-500 dark:text-gray-400">{{ $t('backtest.noTrades') }}</div>
    </div>

    <div class="rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
      <div class="px-4 py-3 text-sm font-bold text-gray-900 dark:text-white border-b border-gray-200 dark:border-gray-700">
        {{ $t('backtest.report') }} / K线复盘
      </div>
      <div class="h-[420px] relative">
        <TradingViewChart :data="page.chartData.candles" :volume-data="page.chartData.volume" :colors="page.chartColors" />
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import TradingViewChart from '@/components/TradingViewChart.vue'
import { formatDateTime, formatDuration, formatMoney, formatPercent, formatPrice } from '@/modules/backtest/format'
import type { BacktestPageState } from '@/modules/backtest/useBacktestPage'

const props = defineProps<{ page: BacktestPageState }>()
const page = props.page
</script>
