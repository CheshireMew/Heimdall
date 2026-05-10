<template>
  <select
    :value="locale"
    class="app-control w-full px-3 py-2"
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
