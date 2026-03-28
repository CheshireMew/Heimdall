<template>
  <aside class="space-y-6">
    <section class="panel p-5">
      <div class="flex items-start justify-between gap-3">
        <div>
          <h2 class="text-lg font-semibold text-slate-900 dark:text-white">{{ $t('factorResearch.recentRuns') }}</h2>
          <p class="text-sm text-slate-500 dark:text-slate-400">{{ $t('factorResearch.recentRunsHint') }}</p>
        </div>
        <div class="text-xs text-slate-400">{{ panel.runsLoading ? $t('factorResearch.loadingRuns') : panel.runs.length }}</div>
      </div>
      <div class="mt-4 space-y-3">
        <button v-for="run in panel.runs" :key="run.id" class="block w-full rounded-2xl border px-4 py-3 text-left transition" :class="run.id === panel.selectedRunId ? 'border-cyan-500 bg-cyan-50 dark:border-cyan-400 dark:bg-cyan-500/10' : 'border-slate-200 bg-white hover:border-slate-300 dark:border-slate-700 dark:bg-slate-800/70 dark:hover:border-slate-600'" @click="panel.loadRun(run.id)">
          <div class="flex items-start justify-between gap-3">
            <div>
              <div class="text-sm font-semibold text-slate-900 dark:text-white">{{ run.summary.symbol }} · {{ run.summary.timeframe }}</div>
              <div class="mt-1 text-xs text-slate-500 dark:text-slate-400">{{ panel.formatDate(run.created_at) }}</div>
            </div>
            <div class="text-xs text-slate-400">#{{ run.id }}</div>
          </div>
          <div class="mt-3 grid grid-cols-3 gap-2 text-xs">
            <div class="mini-stat">
              <div class="mini-stat-label">{{ $t('factorResearch.blendCount') }}</div>
              <div class="mini-stat-value">{{ run.summary.blend_factor_count }}</div>
            </div>
            <div class="mini-stat">
              <div class="mini-stat-label">{{ $t('factorResearch.lookbackDays') }}</div>
              <div class="mini-stat-value">{{ run.summary.days }}</div>
            </div>
            <div class="mini-stat">
              <div class="mini-stat-label">{{ $t('factorResearch.horizonBars') }}</div>
              <div class="mini-stat-value">{{ run.summary.horizon_bars }}</div>
            </div>
          </div>
        </button>
        <div v-if="!panel.runsLoading && !panel.runs.length" class="rounded-2xl border border-dashed border-slate-200 px-4 py-6 text-center text-sm text-slate-500 dark:border-slate-700 dark:text-slate-400">
          {{ $t('factorResearch.noRuns') }}
        </div>
      </div>
    </section>

    <section class="panel p-5">
      <div>
        <h2 class="text-lg font-semibold text-slate-900 dark:text-white">{{ $t('factorResearch.blendTitle') }}</h2>
        <p class="text-sm text-slate-500 dark:text-slate-400">{{ $t('factorResearch.blendSubtitle') }}</p>
      </div>
      <div v-if="panel.blend" class="mt-4 space-y-4">
        <div class="grid grid-cols-2 gap-3">
          <div class="mini-stat">
            <div class="mini-stat-label">{{ $t('factorResearch.entryThreshold') }}</div>
            <div class="mini-stat-value">{{ panel.formatNumber(panel.blend.entry_threshold, 3) }}</div>
          </div>
          <div class="mini-stat">
            <div class="mini-stat-label">{{ $t('factorResearch.exitThreshold') }}</div>
            <div class="mini-stat-value">{{ panel.formatNumber(panel.blend.exit_threshold, 3) }}</div>
          </div>
        </div>
        <div class="space-y-2">
          <div v-for="item in panel.blend.selected_factors" :key="item.factor_id" class="rounded-2xl border border-slate-200 bg-slate-50 px-3 py-3 dark:border-slate-700 dark:bg-slate-900/60">
            <div class="flex items-start justify-between gap-3">
              <div>
                <div class="text-sm font-semibold text-slate-900 dark:text-white">{{ item.name }}</div>
                <div class="mt-1 text-xs text-slate-500 dark:text-slate-400">{{ item.category }}</div>
              </div>
              <div class="text-sm font-semibold text-slate-900 dark:text-white">{{ panel.formatNumber(item.weight, 3) }}</div>
            </div>
            <div class="mt-3 grid grid-cols-3 gap-2 text-xs">
              <div class="mini-stat">
                <div class="mini-stat-label">{{ $t('factorResearch.score') }}</div>
                <div class="mini-stat-value" :class="panel.scoreClass(item.score)">{{ panel.formatNumber(item.score, 2) }}</div>
              </div>
              <div class="mini-stat">
                <div class="mini-stat-label">{{ $t('factorResearch.stability') }}</div>
                <div class="mini-stat-value">{{ panel.formatPct(item.stability) }}</div>
              </div>
              <div class="mini-stat">
                <div class="mini-stat-label">{{ $t('factorResearch.turnover') }}</div>
                <div class="mini-stat-value">{{ panel.formatPct(item.turnover) }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="mt-4 rounded-2xl border border-dashed border-slate-200 px-4 py-6 text-center text-sm text-slate-500 dark:border-slate-700 dark:text-slate-400">
        {{ $t('factorResearch.noBlend') }}
      </div>
    </section>

    <section class="panel p-5">
      <div>
        <h2 class="text-lg font-semibold text-slate-900 dark:text-white">{{ $t('factorResearch.executionTitle') }}</h2>
        <p class="text-sm text-slate-500 dark:text-slate-400">{{ $t('factorResearch.executionSubtitle') }}</p>
      </div>
      <div class="mt-4 grid gap-4 sm:grid-cols-2">
        <div>
          <label class="label">{{ $t('backtest.initialCash') }}</label>
          <input v-model.number="panel.executionForm.initial_cash" class="input" type="number" min="1000" step="1000" />
        </div>
        <div>
          <label class="label">{{ $t('backtest.feeRate') }}</label>
          <input v-model.number="panel.executionForm.fee_rate" class="input" type="number" min="0" step="0.01" />
        </div>
        <div>
          <label class="label">{{ $t('backtest.positionSize') }}</label>
          <input v-model.number="panel.executionForm.position_size_pct" class="input" type="number" min="1" max="100" step="1" />
        </div>
        <div>
          <label class="label">{{ $t('backtest.stakeMode') }}</label>
          <select v-model="panel.executionForm.stake_mode" class="input">
            <option value="fixed">{{ $t('backtest.stakeModeFixed') }}</option>
            <option value="unlimited">{{ $t('backtest.stakeModeUnlimited') }}</option>
          </select>
        </div>
        <div>
          <label class="label">{{ $t('factorResearch.entryThreshold') }}</label>
          <input v-model.number="panel.executionForm.entry_threshold" class="input" type="number" step="0.01" />
        </div>
        <div>
          <label class="label">{{ $t('factorResearch.exitThreshold') }}</label>
          <input v-model.number="panel.executionForm.exit_threshold" class="input" type="number" step="0.01" />
        </div>
        <div>
          <label class="label">{{ $t('backtest.stoplossLabel') }}</label>
          <input v-model.number="panel.executionForm.stoploss_pct" class="input" type="number" step="0.01" />
        </div>
        <div>
          <label class="label">{{ $t('factorResearch.takeprofit') }}</label>
          <input v-model.number="panel.executionForm.takeprofit_pct" class="input" type="number" min="0" step="0.01" />
        </div>
        <div class="sm:col-span-2">
          <label class="label">{{ $t('factorResearch.maxHoldBars') }}</label>
          <input v-model.number="panel.executionForm.max_hold_bars" class="input" type="number" min="1" step="1" />
        </div>
      </div>
      <p class="mt-4 text-sm leading-6 text-slate-500 dark:text-slate-400">{{ $t('factorResearch.executionHint') }}</p>
      <div class="mt-4 flex flex-col gap-3">
        <button class="primary-btn" :disabled="!panel.selectedRunId || !!panel.executionLoading" @click="panel.startExecution('backtest')">
          {{ panel.executionLoading === 'backtest' ? $t('backtest.running') : $t('factorResearch.runBacktest') }}
        </button>
        <button class="secondary-btn" :disabled="!panel.selectedRunId || !!panel.executionLoading" @click="panel.startExecution('paper')">
          {{ panel.executionLoading === 'paper' ? $t('backtest.running') : $t('factorResearch.startPaper') }}
        </button>
      </div>
    </section>
  </aside>
</template>

<script setup lang="ts">
import type { FactorResearchSidebarView } from '@/modules/factors/viewTypes'

const props = defineProps<{ panel: FactorResearchSidebarView }>()
const panel = props.panel
</script>

<style scoped>
.panel { @apply rounded-3xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800; }
.label { @apply mb-1 block text-xs font-bold uppercase tracking-wide text-slate-500 dark:text-slate-400; }
.input { @apply w-full rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-cyan-500 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100; }
.primary-btn { @apply rounded-2xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-cyan-600 dark:hover:bg-cyan-500; }
.secondary-btn { @apply rounded-2xl border border-slate-300 px-5 py-3 text-sm font-semibold text-slate-700 transition hover:border-slate-400 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-600 dark:text-slate-100 dark:hover:border-slate-500 dark:hover:bg-slate-800; }
.mini-stat { @apply rounded-xl bg-slate-100 px-3 py-2 dark:bg-slate-900; }
.mini-stat-label { @apply text-[11px] uppercase tracking-wide text-slate-400; }
.mini-stat-value { @apply mt-1 font-semibold text-slate-900 dark:text-white; }
</style>
