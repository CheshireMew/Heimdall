<template>
  <select
    :value="displayCurrency"
    class="w-full rounded-lg border border-gray-300 bg-gray-50 px-3 py-2 text-gray-900 outline-none transition focus:border-blue-500 dark:border-gray-600 dark:bg-gray-900 dark:text-white"
    @change="handleChange"
  >
    <option v-for="option in currencyOptions" :key="option.value" :value="option.value">
      {{ option.label }}
    </option>
  </select>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useMoney } from '@/composables/useMoney'

const { displayCurrency, currencyOptions, setDisplayCurrency, loadCurrencyRates } = useMoney()

const handleChange = (event: Event) => {
  setDisplayCurrency((event.target as HTMLSelectElement).value)
}

onMounted(() => {
  loadCurrencyRates()
})
</script>
