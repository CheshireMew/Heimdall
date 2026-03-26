<template>
  <div v-if="page.selectedRun" class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 flex-1 flex flex-col min-h-[500px] transition-colors space-y-6">
    <BacktestResultOverview :page="page" />
    <BacktestResearchSection v-if="!page.isPaperRun" :page="page" />
    <BacktestCompareSection v-if="!page.isPaperRun" :page="page" />
    <BacktestTradeReview :page="page" />
  </div>
</template>

<script setup lang="ts">
import BacktestCompareSection from '@/components/backtest/BacktestCompareSection.vue'
import BacktestResearchSection from '@/components/backtest/BacktestResearchSection.vue'
import BacktestResultOverview from '@/components/backtest/BacktestResultOverview.vue'
import BacktestTradeReview from '@/components/backtest/BacktestTradeReview.vue'
import type { BacktestPageState } from '@/modules/backtest/useBacktestPage'

const props = defineProps<{ page: BacktestPageState }>()
const page = props.page
</script>
