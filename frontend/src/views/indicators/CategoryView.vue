<template>
  <div class="h-full flex flex-col p-6 space-y-6 overflow-y-auto">
    <!-- Header -->
    <div class="flex-shrink-0">
      <h2 class="text-2xl font-bold text-gray-800 dark:text-gray-100 flex items-center">
        <span class="mr-3 text-2xl">{{ categoryIcon }}</span>
        {{ $t('category.' + categoryI18nKey + '.title') }}
      </h2>
      <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">{{ $t('category.' + categoryI18nKey + '.desc') }}</p>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center items-center h-64">
      <span class="animate-spin text-3xl text-blue-500">&#10227;</span>
    </div>

    <!-- Indicator Grid -->
    <div v-else-if="indicators.length > 0" class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div v-for="ind in indicators" :key="ind.indicator_id"
           class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm transition-colors overflow-hidden">
        <!-- Card Header -->
        <div class="p-5 pb-3">
          <div class="flex justify-between items-start">
            <div>
              <div class="text-xs text-gray-500 dark:text-gray-400 font-bold uppercase tracking-wider">
                {{ $t('indicator.' + ind.indicator_id, ind.name) }}
              </div>
              <div class="text-3xl font-bold font-mono text-gray-900 dark:text-white mt-1">
                {{ ind.current_value !== null ? formatValue(ind.current_value, ind.unit) : 'N/A' }}
              </div>
            </div>
            <div class="text-right">
              <span v-if="ind.last_updated" class="text-xs text-gray-400 dark:text-gray-500">
                {{ formatDate(ind.last_updated) }}
              </span>
            </div>
          </div>
        </div>
        <!-- Chart -->
        <div class="px-3 pb-3">
          <IndicatorChart v-if="ind.history && ind.history.length > 0" :indicator="ind" height="h-56" />
          <div v-else class="text-sm text-gray-400 py-8 text-center">{{ $t('common.noHistory') }}</div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="flex flex-col items-center justify-center py-20">
      <div class="text-5xl mb-4 opacity-30">{{ categoryIcon }}</div>
      <p class="text-gray-500 dark:text-gray-400 text-lg">{{ $t('common.noData') }}</p>
      <p class="text-gray-400 dark:text-gray-500 text-sm mt-1">{{ $t('common.waitingData') }}</p>
    </div>
  </div>
</template>

<script setup>
import { onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import IndicatorChart from '@/components/IndicatorChart.vue'
import { useDateTime } from '@/composables/useDateTime'
import { useIndicatorCategory } from '@/modules/market'

const route = useRoute()

const CATEGORY_ICONS = {
  Macro: '🏛️',
  Onchain: '⛓️',
  Sentiment: '💡',
  Tech: '📐'
}

const CATEGORY_I18N_KEY = {
  Macro: 'macro',
  Onchain: 'onchain',
  Sentiment: 'sentiment',
  Tech: 'tech'
}

const categoryKey = computed(() => route.meta.category || 'Macro')
const categoryIcon = computed(() => CATEGORY_ICONS[categoryKey.value] || '🏛️')
const categoryI18nKey = computed(() => CATEGORY_I18N_KEY[categoryKey.value] || 'macro')
const { indicators, loading, load } = useIndicatorCategory(categoryKey, 90)
const dateTime = useDateTime()

const formatValue = (val, unit) => {
  if (typeof val !== 'number') return String(val)
  let formatted = val > 1000 ? val.toLocaleString(undefined, { maximumFractionDigits: 0 }) : val.toFixed(2)
  return unit ? `${formatted} ${unit}` : formatted
}

const formatDate = (isoStr) => {
  if (!isoStr) return ''
  return dateTime.formatDate(isoStr)
}

onMounted(() => {
  load()
})
</script>
