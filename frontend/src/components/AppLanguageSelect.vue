<template>
  <select
    :value="locale"
    class="w-full rounded-lg border border-gray-300 bg-gray-50 px-3 py-2 text-gray-900 outline-none transition focus:border-blue-500 dark:border-gray-600 dark:bg-gray-900 dark:text-white"
    @change="handleChange"
  >
    <option v-for="option in LOCALE_OPTIONS" :key="option.value" :value="option.value">
      {{ option.label }}
    </option>
  </select>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { LOCALE_OPTIONS, setAppLocale } from '@/i18n/config'

const { locale } = useI18n()

const handleChange = (event: Event) => {
  setAppLocale(locale, (event.target as HTMLSelectElement).value)
}
</script>
