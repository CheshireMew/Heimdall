<template>
  <section class="panel p-5">
    <div class="grid gap-4 xl:grid-cols-[repeat(5,minmax(0,1fr))_auto]">
      <div>
        <label class="label">{{ $t('factorResearch.symbol') }}</label>
        <select v-model="panel.form.symbol" class="input">
          <option v-for="item in panel.catalog.symbols" :key="item" :value="item">{{ item }}</option>
        </select>
      </div>
      <div>
        <label class="label">{{ $t('factorResearch.timeframe') }}</label>
        <select v-model="panel.form.timeframe" class="input">
          <option v-for="item in panel.catalog.timeframes" :key="item" :value="item">{{ $t(`compare.tf.${item}`) }}</option>
        </select>
      </div>
      <div>
        <label class="label">{{ $t('factorResearch.lookbackDays') }}</label>
        <input v-model.number="panel.form.days" class="input" type="number" min="60" step="10" />
      </div>
      <div>
        <label class="label">{{ $t('factorResearch.horizonBars') }}</label>
        <input v-model.number="panel.form.horizon_bars" class="input" type="number" min="1" step="1" />
      </div>
      <div>
        <label class="label">{{ $t('factorResearch.maxLagBars') }}</label>
        <input v-model.number="panel.form.max_lag_bars" class="input" type="number" min="0" step="1" />
      </div>
      <button class="primary-btn" :disabled="panel.loading || panel.catalogLoading" @click="panel.runAnalysis">
        {{ panel.loading ? $t('factorResearch.analyzing') : $t('factorResearch.run') }}
      </button>
    </div>

    <div class="mt-5 grid gap-5 xl:grid-cols-[minmax(0,0.72fr)_minmax(0,1fr)]">
      <div class="card-shell">
        <div class="section-title">{{ $t('factorResearch.categoryScope') }}</div>
        <div class="section-subtitle">{{ $t('factorResearch.categoryScopeHint') }}</div>
        <div class="mt-4 flex flex-wrap gap-2">
          <button v-for="category in panel.catalog.categories" :key="category" class="chip" :class="panel.categoryChipClass(category)" @click="panel.toggleCategory(category)">
            {{ category }}
          </button>
        </div>
      </div>

      <div class="card-shell">
        <div class="flex items-center justify-between gap-3">
          <div>
            <div class="section-title">{{ $t('factorResearch.factorPool') }}</div>
            <div class="section-subtitle">{{ $t('factorResearch.factorPoolHint') }}</div>
          </div>
          <button class="text-sm font-medium text-cyan-600 dark:text-cyan-300" @click="panel.resetFactorSelection">{{ $t('factorResearch.useAll') }}</button>
        </div>
        <div class="mt-4 flex max-h-40 flex-wrap gap-2 overflow-y-auto pr-1">
          <button v-for="factor in panel.factorPool" :key="factor.factor_id" class="chip" :class="panel.factorChipClass(factor.factor_id)" @click="panel.toggleFactor(factor.factor_id)">
            {{ factor.name }}
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { FactorResearchFiltersView } from '@/modules/factors/viewTypes'

const props = defineProps<{ panel: FactorResearchFiltersView }>()
const panel = props.panel
</script>

<style scoped>
.panel { @apply rounded-3xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800; }
.label { @apply mb-1 block text-xs font-bold uppercase tracking-wide text-slate-500 dark:text-slate-400; }
.input { @apply w-full rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-cyan-500 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100; }
.primary-btn { @apply rounded-2xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-cyan-600 dark:hover:bg-cyan-500; }
.card-shell { @apply rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900/50; }
.section-title { @apply text-sm font-semibold text-slate-900 dark:text-white; }
.section-subtitle { @apply mt-1 text-xs text-slate-500 dark:text-slate-400; }
.chip { @apply rounded-full border px-3 py-1.5 text-sm font-medium transition; }
</style>
