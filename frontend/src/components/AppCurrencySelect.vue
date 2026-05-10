<template>
  <select
    :value="displayCurrency"
    class="app-control w-full px-3 py-2"
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
