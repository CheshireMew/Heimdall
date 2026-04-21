<template>
  <section class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
    <article
      v-for="card in cards"
      :key="card.label"
      class="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-800"
    >
      <p class="text-xs font-bold uppercase tracking-wide text-slate-500 dark:text-slate-400">{{ card.label }}</p>
      <p class="mt-3 text-2xl font-semibold text-slate-900 dark:text-white">{{ card.primary ?? card.value ?? '--' }}</p>
      <p v-if="card.secondary || card.hint" class="mt-2 text-xs text-slate-500 dark:text-slate-400" :class="card.tone">
        {{ card.secondary ?? card.hint }}
      </p>
    </article>
  </section>
</template>

<script setup>
defineOptions({ name: 'IndicatorSummaryCards' })

defineProps({
  cards: {
    type: Array,
    default: () => [],
  },
})
</script>
