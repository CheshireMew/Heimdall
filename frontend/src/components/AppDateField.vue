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
  inputClass: 'app-control w-full px-4 py-3',
})

const emit = defineEmits<{
  (event: 'update:modelValue', value: string): void
}>()

const handleInput = (event: Event) => {
  const target = event.target as HTMLInputElement | null
  emit('update:modelValue', target?.value || '')
}
</script>
