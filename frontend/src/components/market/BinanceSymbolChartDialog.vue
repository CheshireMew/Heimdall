<template>
  <div
    v-if="open"
    class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/55 p-4 backdrop-blur-sm"
    @click.self="$emit('close')"
  >
    <section class="flex h-[min(88vh,820px)] w-full max-w-6xl flex-col overflow-hidden rounded-[32px] border border-slate-200/80 bg-white shadow-2xl dark:border-slate-700 dark:bg-slate-800">
      <header class="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 px-6 py-5 dark:border-slate-700">
        <div>
          <div class="flex items-center gap-3">
            <span class="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600 dark:bg-slate-900 dark:text-slate-300">{{ marketLabel }}</span>
            <h3 class="text-2xl font-semibold text-slate-900 dark:text-white">{{ title }}</h3>
          </div>
          <p class="mt-2 text-sm text-slate-500 dark:text-slate-400">{{ symbol || '--' }}</p>
        </div>

        <div class="flex items-center gap-3">
          <div class="flex flex-wrap gap-2 rounded-full border border-slate-200 bg-slate-50 p-1 dark:border-slate-700 dark:bg-slate-900">
            <button
              v-for="item in timeframes"
              :key="item"
              type="button"
              class="rounded-full px-4 py-2 text-sm transition"
              :class="timeframe === item ? 'bg-slate-900 text-white dark:bg-cyan-600' : 'text-slate-600 hover:bg-white dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white'"
              @click="$emit('update:timeframe', item)"
            >
              {{ item }}
            </button>
          </div>

          <button
            type="button"
            class="rounded-full border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-900 dark:hover:text-white"
            @click="$emit('close')"
          >
            关闭
          </button>
        </div>
      </header>

      <div class="relative flex-1 bg-slate-950 p-4">
        <div
          v-if="loadingMore"
          class="absolute left-1/2 top-6 z-10 -translate-x-1/2 rounded-full bg-cyan-500 px-3 py-1 text-xs font-semibold text-slate-950 shadow-lg"
        >
          加载更多历史中...
        </div>
        <TradingViewChart
          :data="chartData"
          :volume-data="volumeData"
          :colors="chartColors"
          @load-more="$emit('loadMore')"
        />
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import TradingViewChart from '@/components/TradingViewChart.vue'
import type { CandlestickData, VolumeData } from '@/modules/market/contracts'

defineProps<{
  open: boolean
  marketLabel: string
  title: string
  symbol: string
  timeframe: string
  timeframes: string[]
  chartColors: Record<string, string>
  chartData: CandlestickData[]
  volumeData: VolumeData[]
  loadingMore: boolean
}>()

defineEmits<{
  close: []
  loadMore: []
  'update:timeframe': [timeframe: string]
}>()
</script>
