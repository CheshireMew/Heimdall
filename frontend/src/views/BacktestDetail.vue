<template>
  <div class="h-full flex flex-col p-6 space-y-6">
    <section class="rounded-[28px] border border-gray-200 dark:border-slate-700 bg-[linear-gradient(135deg,_rgba(240,249,255,0.94),_rgba(255,255,255,0.98))] dark:bg-[radial-gradient(circle_at_top_left,_rgba(14,165,233,0.18),_transparent_36%),linear-gradient(135deg,_rgba(15,23,42,0.96),_rgba(30,41,59,0.92))] px-6 py-6 shadow-[0_20px_60px_rgba(15,23,42,0.16)]">
      <div class="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div>
          <button class="inline-flex items-center rounded-full border border-gray-300/80 bg-white/80 px-3 py-1 text-xs font-semibold text-gray-600 transition hover:border-blue-400 hover:text-blue-600 dark:border-white/10 dark:bg-white/5 dark:text-slate-200 dark:hover:border-sky-400 dark:hover:text-sky-200" @click="page.goBackToCenter">
            {{ $t('backtest.backToCenter') }}
          </button>
          <div class="mt-4 text-xs font-semibold uppercase tracking-[0.22em] text-sky-600/80 dark:text-sky-200/80">{{ $t('backtest.detailEyebrow') }}</div>
          <h1 class="mt-3 text-3xl font-semibold tracking-tight text-gray-900 dark:text-white">{{ $t('backtest.detailTitle') }}</h1>
          <p class="mt-2 max-w-3xl text-sm leading-6 text-gray-600 dark:text-slate-200/86">{{ $t('backtest.detailSubtitle') }}</p>
        </div>
        <div v-if="page.selectedRun" class="grid grid-cols-2 gap-3 rounded-2xl border border-gray-200/80 bg-white/80 p-4 text-sm text-gray-700 dark:border-white/10 dark:bg-white/5 dark:text-slate-100/90">
          <div>
            <div class="text-xs uppercase tracking-wide text-gray-400 dark:text-slate-400">{{ $t('backtest.runMode') }}</div>
            <div class="mt-1 font-semibold">{{ page.isPaperRun ? $t('backtest.paperRunShort') : $t('backtest.runShort') }}</div>
          </div>
          <div>
            <div class="text-xs uppercase tracking-wide text-gray-400 dark:text-slate-400">{{ $t('backtest.runStatus') }}</div>
            <div class="mt-1 font-semibold">{{ page.runStatusLabel(page.selectedRun) }}</div>
          </div>
          <div>
            <div class="text-xs uppercase tracking-wide text-gray-400 dark:text-slate-400">{{ $t('backtest.symbols') }}</div>
            <div class="mt-1 font-semibold">{{ page.portfolioLabel(page.selectedRun) }}</div>
          </div>
          <div>
            <div class="text-xs uppercase tracking-wide text-gray-400 dark:text-slate-400">{{ $t('backtest.version') }}</div>
            <div class="mt-1 font-semibold">v{{ page.selectedRun?.metadata?.strategy_version || '-' }}</div>
          </div>
        </div>
      </div>
    </section>

    <div v-if="page.selectedRun" class="grid grid-cols-1 2xl:grid-cols-[360px_minmax(0,1fr)] gap-6">
      <BacktestHistoryPanel :page="page" />
      <BacktestResultPanel :page="page" />
    </div>

    <section v-else class="rounded-3xl border border-dashed border-gray-300 dark:border-gray-700 bg-white/70 dark:bg-gray-800/70 px-8 py-14 text-center">
      <h2 class="text-xl font-semibold text-gray-900 dark:text-white">{{ $t('backtest.detailEmptyTitle') }}</h2>
      <p class="mt-3 text-sm text-gray-500 dark:text-gray-400">{{ $t('backtest.detailEmptySubtitle') }}</p>
      <button class="mt-6 inline-flex items-center rounded-full bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-500" @click="page.goBackToCenter">
        {{ $t('backtest.backToCenter') }}
      </button>
    </section>
  </div>
</template>

<script setup lang="ts">
import BacktestHistoryPanel from '@/components/backtest/BacktestHistoryPanel.vue'
import BacktestResultPanel from '@/components/backtest/BacktestResultPanel.vue'
import { useBacktestDetailPage } from '@/modules/backtest/useBacktestDetailPage'
import type { BacktestPageState } from '@/modules/backtest/useBacktestPage'

const page = useBacktestDetailPage() as unknown as BacktestPageState
</script>
