<template>
  <select
    :value="selectedValue"
    class="w-full rounded-lg border border-gray-300 bg-gray-50 px-3 py-2 text-gray-900 outline-none transition focus:border-blue-500 dark:border-gray-600 dark:bg-gray-900 dark:text-white"
    @change="handleChange"
  >
    <option v-for="option in options" :key="option.value" :value="option.value">
      {{ option.label }}
    </option>
  </select>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useUserPreferences } from '@/composables/useUserPreferences'

const props = defineProps<{
  modelValue?: string
}>()
const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const { timezone, timezoneOptions, setTimezone } = useUserPreferences()

const selectedValue = computed(() => props.modelValue ?? timezone.value)
const options = computed(() => {
  if (timezoneOptions.value.some((option) => option.value === selectedValue.value)) {
    return timezoneOptions.value
  }
  return [{ value: selectedValue.value, label: selectedValue.value }, ...timezoneOptions.value]
})

const handleChange = (event: Event) => {
  const value = (event.target as HTMLSelectElement).value
  emit('update:modelValue', value)
  if (props.modelValue === undefined) {
    setTimezone(value)
  }
}
</script>
