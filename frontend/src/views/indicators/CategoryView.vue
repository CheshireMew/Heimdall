<template>
  <div class="app-page">
    <div class="app-page-inner">
    <!-- Header -->
    <div class="flex-shrink-0 border-b border-stone-200 pb-6 dark:border-slate-800">
      <p class="app-eyebrow">{{ categoryI18nKey }}</p>
      <h2 class="app-title mt-2 flex items-center">
        {{ $t('category.' + categoryI18nKey + '.title') }}
      </h2>
      <p class="app-subtitle mt-3">{{ $t('category.' + categoryI18nKey + '.desc') }}</p>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center items-center h-64">
      <span class="animate-spin text-3xl text-[#0f6b4f] dark:text-emerald-300">&#10227;</span>
    </div>

    <!-- Indicator Grid -->
    <div v-else-if="indicators.length > 0" class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div v-for="ind in indicators" :key="ind.indicator_id"
           class="app-panel overflow-hidden transition-colors">
        <!-- Card Header -->
        <div class="p-5 pb-3">
          <div class="flex justify-between items-start">
            <div>
              <div class="text-xs text-stone-500 dark:text-slate-400 font-bold uppercase tracking-wider">
                {{ $t('indicator.' + ind.indicator_id, ind.name) }}
              </div>
              <div class="text-3xl font-semibold text-stone-950 dark:text-white mt-1">
                {{ ind.current_value !== null ? formatValue(ind.current_value, ind.unit) : 'N/A' }}
              </div>
            </div>
            <div class="text-right">
              <span v-if="ind.last_updated" class="text-xs text-stone-400 dark:text-slate-500">
                {{ formatDate(ind.last_updated) }}
              </span>
            </div>
          </div>
        </div>
        <!-- Chart -->
        <div class="px-3 pb-3">
          <IndicatorChart v-if="ind.history && ind.history.length > 0" :indicator="ind" height="h-56" />
          <div v-else class="text-sm text-stone-400 py-8 text-center">{{ $t('common.noHistory') }}</div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="flex flex-col items-center justify-center py-20">
      <p class="text-stone-500 dark:text-slate-400 text-lg">{{ $t('common.noData') }}</p>
      <p class="text-stone-400 dark:text-slate-500 text-sm mt-1">{{ $t('common.waitingData') }}</p>
    </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import IndicatorChart from '@/components/IndicatorChart.vue'
import { formatDate } from '@/modules/format'
import { useIndicatorCategory } from '@/modules/market'

const route = useRoute()

const CATEGORY_I18N_KEY = {
  Macro: 'macro',
  Onchain: 'onchain',
  Sentiment: 'sentiment',
  Tech: 'tech'
}

const categoryKey = computed(() => route.meta.category || 'Macro')
const categoryI18nKey = computed(() => CATEGORY_I18N_KEY[categoryKey.value] || 'macro')
const { indicators, loading, load } = useIndicatorCategory(categoryKey, 90)

const formatValue = (val, unit) => {
  if (typeof val !== 'number') return String(val)
  let formatted = val > 1000 ? val.toLocaleString(undefined, { maximumFractionDigits: 0 }) : val.toFixed(2)
  return unit ? `${formatted} ${unit}` : formatted
}

onMounted(() => {
  load()
})
</script>
