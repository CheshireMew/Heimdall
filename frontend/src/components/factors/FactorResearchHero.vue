<template>
  <section class="panel p-6">
    <div class="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
      <div class="max-w-4xl">
        <div class="text-xs font-semibold uppercase tracking-[0.26em] text-cyan-600 dark:text-cyan-300">{{ $t('factorResearch.eyebrow') }}</div>
        <h1 class="mt-3 text-3xl font-semibold tracking-tight text-slate-900 dark:text-white">{{ $t('factorResearch.title') }}</h1>
        <p class="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">{{ $t('factorResearch.subtitle') }}</p>
      </div>
      <div class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200">
        {{ $t('factorResearch.hint') }}
        <div class="mt-2 text-xs text-slate-500 dark:text-slate-400">
          {{ $t('factorResearch.forwardHorizons') }}: {{ panel.catalog.forward_horizons.length ? panel.catalog.forward_horizons.join(' / ') : '--' }}
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { FactorResearchHeroView } from '@/modules/factors/viewTypes'

const props = defineProps<{ panel: FactorResearchHeroView }>()
const panel = props.panel
</script>

<style scoped>
.panel { @apply rounded-3xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800; }
</style>
