<template>
  <div
    v-if="open"
    class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/55 p-4 backdrop-blur-sm"
    @click.self="$emit('close')"
  >
    <section class="flex h-[min(88vh,820px)] w-full max-w-7xl flex-col overflow-hidden rounded-[32px] border border-slate-200/80 bg-white shadow-2xl dark:border-slate-700 dark:bg-slate-800">
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

      <div class="grid min-h-0 flex-1 bg-slate-950" :class="monitorItem ? 'lg:grid-cols-[minmax(0,1fr)_360px]' : ''">
        <div class="relative min-h-[420px] p-4">
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

        <aside v-if="monitorItem" class="overflow-y-auto border-t border-slate-800 bg-white p-5 dark:bg-slate-800 lg:border-l lg:border-t-0">
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="text-sm text-slate-500 dark:text-slate-400">{{ monitorItem.follow_status }}</p>
              <h4 class="mt-1 text-lg font-semibold text-slate-900 dark:text-white">监控判断</h4>
            </div>
            <span class="inline-flex rounded-full px-3 py-1 text-xs font-semibold ring-1" :class="renderVerdictTone(monitorItem.verdict)">
              {{ monitorItem.verdict }}
            </span>
          </div>

          <div class="mt-5 grid grid-cols-2 gap-3">
            <div class="rounded-2xl bg-slate-50 px-4 py-3 dark:bg-slate-900/70">
              <div class="text-xs uppercase tracking-[0.18em] text-slate-400">当天</div>
              <div class="mt-2 text-lg font-semibold" :class="renderValueTone(monitorItem.price_change_pct)">{{ renderSigned(monitorItem.price_change_pct) }}</div>
            </div>
            <div class="rounded-2xl bg-slate-50 px-4 py-3 dark:bg-slate-900/70">
              <div class="text-xs uppercase tracking-[0.18em] text-slate-400">成交额</div>
              <div class="mt-2 text-lg font-semibold text-slate-900 dark:text-white">{{ renderCompact(monitorItem.quote_volume) }}</div>
            </div>
            <div class="rounded-2xl bg-slate-50 px-4 py-3 dark:bg-slate-900/70">
              <div class="text-xs uppercase tracking-[0.18em] text-slate-400">自然度</div>
              <div class="mt-2 text-lg font-semibold text-slate-900 dark:text-white">{{ renderScore(monitorItem.natural_score) }}</div>
            </div>
            <div class="rounded-2xl bg-slate-50 px-4 py-3 dark:bg-slate-900/70">
              <div class="text-xs uppercase tracking-[0.18em] text-slate-400">动能</div>
              <div class="mt-2 text-lg font-semibold text-slate-900 dark:text-white">{{ renderScore(monitorItem.momentum_score) }}</div>
            </div>
          </div>

          <div class="mt-5 space-y-3 rounded-[26px] bg-slate-950 p-4 text-white ring-1 ring-slate-800 dark:bg-slate-900">
            <div class="flex items-center justify-between gap-4 text-sm">
              <span class="text-slate-400">15m / 1h</span>
              <span>{{ renderSigned(monitorItem.change_15m_pct) }} / {{ renderSigned(monitorItem.change_1h_pct) }}</span>
            </div>
            <div class="flex items-center justify-between gap-4 text-sm">
              <span class="text-slate-400">距高点</span>
              <span :class="renderValueTone(monitorItem.pullback_from_high_pct, false)">{{ renderSigned(monitorItem.pullback_from_high_pct) }}</span>
            </div>
            <div class="flex items-center justify-between gap-4 text-sm">
              <span class="text-slate-400">EMA20 偏离</span>
              <span>{{ renderSigned(monitorItem.ema20_gap_15m_pct) }} / {{ renderSigned(monitorItem.ema20_gap_1h_pct) }}</span>
            </div>
            <div class="flex items-center justify-between gap-4 text-sm">
              <span class="text-slate-400">RSI</span>
              <span>{{ renderSigned(monitorItem.rsi_15m, 1, '', false) }} / {{ renderSigned(monitorItem.rsi_1h, 1, '', false) }}</span>
            </div>
            <div class="flex items-center justify-between gap-4 text-sm" v-if="monitorItem.funding_rate_pct !== null && monitorItem.funding_rate_pct !== undefined">
              <span class="text-slate-400">Funding</span>
              <span :class="renderValueTone(monitorItem.funding_rate_pct)">{{ renderSigned(monitorItem.funding_rate_pct, 3) }}</span>
            </div>
          </div>

          <div class="mt-5">
            <h5 class="text-sm font-semibold text-slate-900 dark:text-white">判断依据</h5>
            <div class="mt-3 flex flex-wrap gap-2">
              <span
                v-for="reason in monitorItem.reasons || []"
                :key="reason"
                class="rounded-full bg-cyan-50 px-3 py-1.5 text-sm text-cyan-700 dark:bg-cyan-500/10 dark:text-cyan-300"
              >
                {{ reason }}
              </span>
            </div>
          </div>
        </aside>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import TradingViewChart from '@/components/TradingViewChart.vue'
import type { BinanceBreakoutMonitorItem, CandlestickData, VolumeData } from '@/modules/market/contracts'

const props = defineProps<{
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
  monitorItem?: BinanceBreakoutMonitorItem | null
  formatScore?: (value: number | null | undefined) => string
  formatSigned?: (value: number | null | undefined, digits?: number, suffix?: string, withSign?: boolean) => string
  formatCompact?: (value: number | null | undefined) => string
  valueTone?: (value: number | null | undefined, positiveIsGood?: boolean) => string
  verdictTone?: (verdict: string | null | undefined) => string
}>()

defineEmits<{
  close: []
  loadMore: []
  'update:timeframe': [timeframe: string]
}>()

const renderScore = (value: number | null | undefined) => props.formatScore?.(value) ?? '--'
const renderSigned = (value: number | null | undefined, digits = 2, suffix = '%', withSign = true) => (
  props.formatSigned?.(value, digits, suffix, withSign) ?? '--'
)
const renderCompact = (value: number | null | undefined) => props.formatCompact?.(value) ?? '--'
const renderValueTone = (value: number | null | undefined, positiveIsGood = true) => (
  props.valueTone?.(value, positiveIsGood) ?? 'text-slate-500 dark:text-slate-400'
)
const renderVerdictTone = (value: string | null | undefined) => (
  props.verdictTone?.(value) ?? 'bg-slate-500/10 text-slate-600 ring-slate-500/20 dark:text-slate-300'
)
</script>
