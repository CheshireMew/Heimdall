<template>
  <div class="h-full flex flex-col p-6 space-y-6">
    <section class="rounded-[28px] border border-slate-700/60 bg-[radial-gradient(circle_at_top_left,_rgba(59,130,246,0.18),_transparent_42%),linear-gradient(135deg,_rgba(15,23,42,0.92),_rgba(30,41,59,0.9))] px-6 py-7 text-white shadow-[0_24px_80px_rgba(15,23,42,0.28)]">
      <div class="text-xs font-semibold uppercase tracking-[0.22em] text-sky-200/80">{{ $t('backtest.centerEyebrow') }}</div>
      <div class="mt-3 flex flex-col gap-3 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <h1 class="text-3xl font-semibold tracking-tight">{{ $t('backtest.centerTitle') }}</h1>
          <p class="mt-2 max-w-3xl text-sm leading-6 text-slate-200/88">{{ $t('backtest.centerSubtitle') }}</p>
        </div>
        <div class="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-100/90 backdrop-blur">
          {{ $t('backtest.centerHint') }}
        </div>
      </div>
    </section>

    <div class="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_380px] gap-6 items-start">
      <BacktestControlPanel :panel="page.controlPanel" />
      <BacktestHistoryPanel :panel="page.historyPanel" />
    </div>
  </div>
</template>

<script setup lang="ts">
import BacktestControlPanel from '@/components/backtest/BacktestControlPanel.vue'
import BacktestHistoryPanel from '@/components/backtest/BacktestHistoryPanel.vue'
import { useBacktestPage } from '@/modules/backtest/useBacktestPage'

const page = useBacktestPage()
</script>
