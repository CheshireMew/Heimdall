<template>
  <label :class="containerClass">
    <span v-if="label" :class="labelClass">{{ label }}</span>
    <input
      :value="modelValue || ''"
      :min="min"
      :max="max"
      :disabled="disabled"
      type="date"
      :class="inputClass"
      @input="handleInput"
    />
  </label>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  modelValue?: string | null
  label?: string
  min?: string
  max?: string
  disabled?: boolean
  containerClass?: string
  labelClass?: string
  inputClass?: string
}>(), {
  modelValue: '',
  label: '',
  min: '',
  max: '',
  disabled: false,
  containerClass: 'block',
  labelClass: 'mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400',
  inputClass: 'w-full rounded-xl border border-slate-300 bg-slate-50 px-4 py-3 text-slate-900 outline-none transition focus:border-sky-500 dark:border-slate-600 dark:bg-slate-900 dark:text-white',
})

const emit = defineEmits<{
  (event: 'update:modelValue', value: string): void
}>()

const handleInput = (event: Event) => {
  const target = event.target as HTMLInputElement | null
  emit('update:modelValue', target?.value || '')
}
</script>
