<template>
  <div v-if="panel.selectedRun" class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 flex-1 flex flex-col min-h-[500px] transition-colors space-y-6">
    <BacktestResultOverview :panel="panel" />
    <BacktestResearchSection v-if="!panel.isPaperRun" :panel="panel" />
    <BacktestCompareSection v-if="!panel.isPaperRun" :panel="panel" />
    <BacktestTradeReview :panel="panel" />
  </div>
</template>

<script setup lang="ts">
import BacktestCompareSection from '@/components/backtest/BacktestCompareSection.vue'
import BacktestResearchSection from '@/components/backtest/BacktestResearchSection.vue'
import BacktestResultOverview from '@/components/backtest/BacktestResultOverview.vue'
import BacktestTradeReview from '@/components/backtest/BacktestTradeReview.vue'
import type { BacktestResultPanelView } from '@/modules/backtest/viewTypes'

const props = defineProps<{ panel: BacktestResultPanelView }>()
const panel = props.panel
</script>
