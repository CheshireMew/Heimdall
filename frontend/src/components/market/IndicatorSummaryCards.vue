<template>
  <section class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
    <article
      v-for="card in cards"
      :key="card.label"
      class="app-card"
    >
      <p class="text-xs font-bold uppercase tracking-wide text-stone-500 dark:text-slate-400">{{ card.label }}</p>
      <p class="mt-3 text-2xl font-semibold text-stone-950 dark:text-white">{{ card.primary ?? card.value ?? '--' }}</p>
      <p v-if="card.secondary || card.hint" class="mt-2 text-xs text-stone-500 dark:text-slate-400" :class="card.tone">
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
