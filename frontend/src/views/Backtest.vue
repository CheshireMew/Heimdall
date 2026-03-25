<template>
  <div class="h-full flex flex-col p-6 space-y-6">
    <div class="grid grid-cols-1 2xl:grid-cols-[420px_minmax(0,1fr)] gap-6">
      <BacktestControlPanel :page="page" />
      <BacktestHistoryPanel :page="page" />
    </div>

    <BacktestResultPanel :page="page" />
  </div>
</template>

<script setup lang="ts">
import BacktestControlPanel from '@/components/backtest/BacktestControlPanel.vue'
import BacktestHistoryPanel from '@/components/backtest/BacktestHistoryPanel.vue'
import BacktestResultPanel from '@/components/backtest/BacktestResultPanel.vue'
import { useBacktestPage } from '@/modules/backtest/useBacktestPage'

const page = useBacktestPage()
</script>
