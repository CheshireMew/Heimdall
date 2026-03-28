<template>
  <div class="h-full flex flex-col p-6 space-y-6">
    <section class="rounded-[28px] border border-emerald-800/40 bg-[radial-gradient(circle_at_top_right,_rgba(16,185,129,0.18),_transparent_36%),linear-gradient(135deg,_rgba(6,78,59,0.96),_rgba(15,23,42,0.92))] px-6 py-7 text-white shadow-[0_26px_80px_rgba(6,78,59,0.22)]">
      <div class="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <button class="inline-flex items-center rounded-full border border-white/15 bg-white/5 px-3 py-1 text-xs font-semibold text-emerald-50/90 transition hover:border-emerald-300/60 hover:text-white" @click="page.seedPanel.goBackToCenter">
            {{ $t('backtest.backToCenter') }}
          </button>
          <div class="mt-4 text-xs font-semibold uppercase tracking-[0.22em] text-emerald-200/75">{{ $t('backtest.editorEyebrow') }}</div>
          <h1 class="mt-3 text-3xl font-semibold tracking-tight">{{ $t('backtest.editorTitle') }}</h1>
          <p class="mt-2 max-w-3xl text-sm leading-6 text-emerald-50/82">{{ $t('backtest.editorSubtitle') }}</p>
        </div>
        <div class="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-emerald-50/90 backdrop-blur">
          {{ $t('backtest.editorHint') }}
        </div>
      </div>
    </section>

    <div class="grid grid-cols-1 2xl:grid-cols-[340px_minmax(0,1fr)] gap-6">
      <aside class="rounded-3xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-6 space-y-5">
        <div>
          <div class="text-xs font-semibold uppercase tracking-[0.2em] text-gray-400 dark:text-gray-500">{{ $t('backtest.editorSeed') }}</div>
          <h2 class="mt-2 text-xl font-semibold text-gray-900 dark:text-white">{{ $t('backtest.editorSeedTitle') }}</h2>
          <p class="mt-2 text-sm leading-6 text-gray-500 dark:text-gray-400">{{ $t('backtest.editorSeedSubtitle') }}</p>
        </div>

        <div class="space-y-3">
          <div>
            <label class="label">{{ $t('backtest.strategy') }}</label>
            <select v-model="page.seedPanel.config.strategy_key" class="input" @change="page.seedPanel.syncStrategyVersion">
              <option v-for="item in page.seedPanel.strategies" :key="item.key" :value="item.key">{{ item.name }}</option>
            </select>
          </div>
          <div>
            <label class="label">{{ $t('backtest.version') }}</label>
            <select v-model="page.seedPanel.config.strategy_version" class="input">
              <option v-for="item in page.seedPanel.selectedStrategyVersions" :key="item?.version ?? String(item)" :value="item?.version">
                v{{ item?.version ?? '-' }} · {{ item?.name ?? '-' }}
              </option>
            </select>
          </div>
        </div>

        <div v-if="page.seedPanel.selectedStrategy" class="rounded-2xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/40 px-4 py-4 text-sm text-gray-600 dark:text-gray-300">
          <div class="font-semibold text-gray-900 dark:text-white">{{ page.seedPanel.selectedStrategy.name }}</div>
          <div class="mt-2">{{ page.seedPanel.selectedStrategy.description || '-' }}</div>
          <div class="mt-3 text-xs text-gray-500 dark:text-gray-400">
            {{ $t('backtest.selectedVersion') }}: v{{ page.seedPanel.config.strategy_version }} · {{ page.seedPanel.selectedVersion?.name || '-' }}
          </div>
        </div>

        <div class="space-y-3">
          <button class="btn-primary w-full" :disabled="!page.seedPanel.selectedVersion" @click="page.seedPanel.openCopySeed">{{ $t('backtest.fillFromCurrent') }}</button>
          <button class="btn-secondary w-full" @click="page.seedPanel.openBlankSeed">{{ $t('backtest.startBlankBuilder') }}</button>
        </div>
      </aside>

      <BacktestVersionEditor :panel="page.editorPanel" />
    </div>
  </div>
</template>

<script setup lang="ts">
import BacktestVersionEditor from '@/components/backtest/BacktestVersionEditor.vue'
import { useBacktestEditorPage } from '@/modules/backtest/useBacktestEditorPage'

const page = useBacktestEditorPage()
</script>

<style scoped>
.label { @apply block text-gray-500 dark:text-gray-400 text-xs font-bold mb-1; }
.input { @apply w-full bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-gray-900 dark:text-white outline-none focus:border-blue-500 transition-colors; }
.btn-primary { @apply bg-emerald-600 hover:bg-emerald-500 text-white py-2.5 rounded-xl font-bold transition disabled:opacity-50; }
.btn-secondary { @apply bg-gray-100 hover:bg-gray-200 dark:bg-gray-900 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-200 py-2.5 rounded-xl font-bold transition border border-gray-200 dark:border-gray-700; }
</style>
