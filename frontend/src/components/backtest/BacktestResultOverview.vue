<template>
  <section class="space-y-6">
    <div class="flex flex-col xl:flex-row xl:items-end xl:justify-between gap-3">
      <div>
        <h3 class="text-xl font-bold text-gray-900 dark:text-white">{{ $t('backtest.result') }}: #{{ page.selectedRun.id }}</h3>
        <div class="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {{ page.portfolioLabel(page.selectedRun) }} · {{ page.selectedRun.metadata?.strategy_name || '-' }} · v{{ page.selectedRun.metadata?.strategy_version || '-' }}
        </div>
      </div>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-2">
        <div class="stat-badge">{{ $t('backtest.buy') }}: {{ page.selectedRun.metrics.buy_signals }}</div>
        <div class="stat-badge">{{ $t('backtest.sell') }}: {{ page.selectedRun.metrics.sell_signals }}</div>
        <div class="stat-badge">{{ $t('backtest.optimizeTrials') }}: {{ page.selectedRun.report?.research?.optimization?.trial_count ?? 0 }}</div>
        <div class="stat-badge">{{ $t('backtest.rollingWindows') }}: {{ page.selectedRun.report?.research?.rolling_windows?.length ?? 0 }}</div>
      </div>
    </div>

    <div class="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-8 gap-3">
      <div class="summary-card">
        <div class="summary-label">{{ $t('backtest.totalReturn') }}</div>
        <div class="summary-value" :class="page.profitColorClass(page.selectedRun.report?.profit_pct)">{{ formatPercent(page.selectedRun.report?.profit_pct) }}</div>
      </div>
      <div class="summary-card">
        <div class="summary-label">{{ $t('backtest.finalBalance') }}</div>
        <div class="summary-value">{{ formatMoney(page.selectedRun.report?.final_balance) }}</div>
      </div>
      <div class="summary-card">
        <div class="summary-label">{{ $t('backtest.maxDrawdown') }}</div>
        <div class="summary-value text-red-600 dark:text-red-400">{{ formatPercent(page.selectedRun.report?.max_drawdown_pct) }}</div>
      </div>
      <div class="summary-card">
        <div class="summary-label">{{ $t('backtest.sharpe') }}</div>
        <div class="summary-value">{{ formatMetric(page.selectedRun.report?.sharpe) }}</div>
      </div>
      <div class="summary-card">
        <div class="summary-label">{{ $t('backtest.winRate') }}</div>
        <div class="summary-value">{{ formatPercent(page.selectedRun.report?.win_rate) }}</div>
      </div>
      <div class="summary-card">
        <div class="summary-label">{{ $t('backtest.profitFactor') }}</div>
        <div class="summary-value">{{ formatMetric(page.selectedRun.report?.profit_factor) }}</div>
      </div>
      <div class="summary-card">
        <div class="summary-label">{{ $t('backtest.avgTrade') }}</div>
        <div class="summary-value">{{ formatPercent(page.selectedRun.report?.avg_trade_pct) }}</div>
      </div>
      <div class="summary-card">
        <div class="summary-label">{{ $t('backtest.totalTrades') }}</div>
        <div class="summary-value">{{ formatNumber(page.selectedRun.report?.total_trades) }}</div>
      </div>
    </div>

    <div class="grid grid-cols-1 xl:grid-cols-[340px_minmax(0,1fr)] gap-6">
      <div class="rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/40 p-4 space-y-3">
        <h4 class="text-sm font-bold text-gray-900 dark:text-white">{{ $t('backtest.config') }}</h4>
        <div class="config-row"><span>{{ $t('backtest.symbols') }}</span><strong>{{ page.joinSymbols(page.selectedRun.metadata?.symbols) }}</strong></div>
        <div class="config-row"><span>{{ $t('compare.timeframe') }}</span><strong>{{ page.selectedRun.timeframe }}</strong></div>
        <div class="config-row"><span>{{ $t('backtest.initialCash') }}</span><strong>{{ formatMoney(page.selectedRun.metadata?.initial_cash) }}</strong></div>
        <div class="config-row"><span>{{ $t('backtest.feeRate') }}</span><strong>{{ formatPercent(page.selectedRun.metadata?.fee_rate) }}</strong></div>
        <div class="config-row"><span>{{ $t('backtest.maxOpenTrades') }}</span><strong>{{ page.selectedRun.report?.portfolio?.max_open_trades ?? '-' }}</strong></div>
        <div class="config-row"><span>{{ $t('backtest.positionSize') }}</span><strong>{{ formatPercent(page.selectedRun.report?.portfolio?.position_size_pct) }}</strong></div>
        <div class="config-row"><span>{{ $t('backtest.stakeMode') }}</span><strong>{{ page.selectedRun.report?.portfolio?.stake_mode || '-' }}</strong></div>
        <div class="config-row"><span>{{ $t('backtest.slippage') }}</span><strong>{{ formatMetric(page.selectedRun.report?.research?.slippage_bps) }} bps</strong></div>
        <div class="config-row"><span>{{ $t('backtest.fundingRate') }}</span><strong>{{ formatPercent(page.selectedRun.report?.research?.funding_rate_daily) }}</strong></div>
        <div class="config-row"><span>{{ $t('backtest.inSampleRatio') }}</span><strong>{{ formatPercent(page.selectedRun.report?.research?.in_sample_ratio) }}</strong></div>
      </div>

      <div class="rounded-xl border border-gray-200 dark:border-gray-700 p-4">
        <div class="text-sm font-bold text-gray-900 dark:text-white mb-3">{{ $t('backtest.equityCurve') }}</div>
        <div class="h-[320px]">
          <BacktestEquityChart :points="page.selectedRun.equity_curve || []" />
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import BacktestEquityChart from '@/components/BacktestEquityChart.vue'
import { formatMetric, formatMoney, formatNumber, formatPercent } from '@/modules/backtest/format'
import type { BacktestPageState } from '@/modules/backtest/useBacktestPage'

const props = defineProps<{ page: BacktestPageState }>()
const page = props.page
</script>

<style scoped>
.stat-badge { @apply px-3 py-2 rounded text-sm font-bold border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/40 text-gray-700 dark:text-gray-200; }
.summary-card { @apply rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/40 px-4 py-3; }
.summary-label { @apply text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400; }
.summary-value { @apply mt-2 text-lg font-bold text-gray-900 dark:text-white; }
.config-row { @apply flex items-center justify-between gap-3 text-sm text-gray-600 dark:text-gray-300; }
</style>
