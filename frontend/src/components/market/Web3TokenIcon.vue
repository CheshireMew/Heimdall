<template>
  <span
    :class="[
      sizeClass,
      'inline-flex shrink-0 items-center justify-center overflow-hidden rounded-full bg-slate-100 text-[10px] font-semibold uppercase text-slate-500 ring-1 ring-slate-200 dark:bg-slate-700 dark:text-slate-300 dark:ring-slate-600',
    ]"
  >
    <img
      v-if="src && !failed"
      :src="src"
      alt=""
      class="h-full w-full object-cover"
      referrerpolicy="no-referrer"
      @error="failed = true"
    />
    <span v-else>{{ initials }}</span>
  </span>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'

const props = withDefaults(defineProps<{
  src?: string | null
  symbol?: string | null
  size?: 'sm' | 'lg'
}>(), {
  src: null,
  symbol: null,
  size: 'sm',
})

const failed = ref(false)

watch(() => props.src, () => {
  failed.value = false
})

const sizeClass = computed(() => (props.size === 'lg' ? 'h-12 w-12 text-sm' : 'h-7 w-7'))
const initials = computed(() => String(props.symbol || '?').trim().slice(0, 2) || '?')
</script>
