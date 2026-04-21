<template>
  <div
    v-if="open && token"
    class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/55 p-4 backdrop-blur-sm"
    @click.self="$emit('close')"
  >
    <section class="flex h-[min(90vh,860px)] w-full max-w-7xl flex-col overflow-hidden rounded-[32px] border border-slate-200/80 bg-white shadow-2xl">
      <header class="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 px-6 py-5">
        <div class="flex items-center gap-4">
          <img v-if="token.icon_url" :src="token.icon_url" alt="" class="h-12 w-12 rounded-full" />
          <span v-else class="h-12 w-12 rounded-full bg-slate-100" />
          <div>
            <div class="flex items-center gap-3">
              <h3 class="text-2xl font-semibold text-slate-900">{{ token.symbol || '--' }}</h3>
              <span class="rounded-full bg-cyan-50 px-3 py-1 text-xs font-semibold text-cyan-700">Score {{ formatScore(token.heat_score) }}</span>
            </div>
            <p class="mt-2 max-w-[680px] truncate text-sm text-slate-500">{{ token.contract_address }}</p>
          </div>
        </div>

        <div class="flex items-center gap-3">
          <div class="flex flex-wrap gap-2 rounded-full border border-slate-200 bg-slate-50 p-1">
            <button
              v-for="item in intervals"
              :key="item"
              type="button"
              class="rounded-full px-4 py-2 text-sm transition"
              :class="interval === item ? 'bg-slate-900 text-white' : 'text-slate-600 hover:bg-white'"
              @click="$emit('update:interval', item)"
            >
              {{ item }}
            </button>
          </div>
          <button
            type="button"
            class="rounded-full border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-50"
            @click="$emit('close')"
          >
            关闭
          </button>
        </div>
      </header>

      <div v-if="detailError" class="border-b border-rose-100 bg-rose-50 px-6 py-3 text-sm text-rose-600">{{ detailError }}</div>

      <div class="grid min-h-0 flex-1 gap-0 lg:grid-cols-[360px_minmax(0,1fr)]">
        <aside class="overflow-y-auto border-r border-slate-200 p-5">
          <div v-if="detailLoading" class="rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-500">加载中...</div>

          <div class="grid grid-cols-2 gap-3">
            <div class="rounded-2xl bg-slate-50 px-4 py-3">
              <div class="text-xs text-slate-400">价格</div>
              <div class="mt-2 font-semibold text-slate-900">{{ formatPrice(dynamic?.price ?? token.metrics?.price) }}</div>
            </div>
            <div class="rounded-2xl bg-slate-50 px-4 py-3">
              <div class="text-xs text-slate-400">24H</div>
              <div class="mt-2 font-semibold" :class="valueTone(dynamic?.percent_change_24h ?? token.metrics?.percent_change_24h)">
                {{ formatSigned(dynamic?.percent_change_24h ?? token.metrics?.percent_change_24h) }}
              </div>
            </div>
            <div class="rounded-2xl bg-slate-50 px-4 py-3">
              <div class="text-xs text-slate-400">市值</div>
              <div class="mt-2 font-semibold text-slate-900">{{ formatCompact(dynamic?.market_cap ?? token.metrics?.market_cap) }}</div>
            </div>
            <div class="rounded-2xl bg-slate-50 px-4 py-3">
              <div class="text-xs text-slate-400">流动性</div>
              <div class="mt-2 font-semibold text-slate-900">{{ formatCompact(dynamic?.liquidity ?? token.metrics?.liquidity) }}</div>
            </div>
            <div class="rounded-2xl bg-slate-50 px-4 py-3">
              <div class="text-xs text-slate-400">1H 成交</div>
              <div class="mt-2 font-semibold text-slate-900">{{ formatCompact(dynamic?.volume_1h ?? token.metrics?.volume_1h) }}</div>
            </div>
            <div class="rounded-2xl bg-slate-50 px-4 py-3">
              <div class="text-xs text-slate-400">24H 成交</div>
              <div class="mt-2 font-semibold text-slate-900">{{ formatCompact(dynamic?.volume_24h ?? token.metrics?.volume_24h) }}</div>
            </div>
            <div class="rounded-2xl bg-slate-50 px-4 py-3">
              <div class="text-xs text-slate-400">持有人</div>
              <div class="mt-2 font-semibold text-slate-900">{{ formatCompact(dynamic?.holders ?? token.metrics?.holders) }}</div>
            </div>
            <div class="rounded-2xl bg-slate-50 px-4 py-3">
              <div class="text-xs text-slate-400">交易次数</div>
              <div class="mt-2 font-semibold text-slate-900">{{ formatCompact(dynamic?.count_24h ?? token.metrics?.count_24h) }}</div>
            </div>
          </div>

          <div class="mt-5 rounded-[26px] bg-slate-950 p-4 text-sm text-white">
            <div class="flex items-center justify-between">
              <span class="text-slate-400">Top Search</span>
              <span>{{ token.components?.top_search?.toFixed?.(1) ?? '--' }}</span>
            </div>
            <div class="mt-3 flex items-center justify-between">
              <span class="text-slate-400">Trending</span>
              <span>{{ token.components?.trending?.toFixed?.(1) ?? '--' }}</span>
            </div>
            <div class="mt-3 flex items-center justify-between">
              <span class="text-slate-400">Social</span>
              <span>{{ token.components?.social_hype?.toFixed?.(1) ?? '--' }}</span>
            </div>
            <div class="mt-3 flex items-center justify-between">
              <span class="text-slate-400">Volume / Tx</span>
              <span>{{ token.components?.volume_growth?.toFixed?.(1) ?? '--' }} / {{ token.components?.transaction_growth?.toFixed?.(1) ?? '--' }}</span>
            </div>
            <div class="mt-3 flex items-center justify-between">
              <span class="text-slate-400">Smart Money</span>
              <span>{{ formatCompact(token.metrics?.smart_money_inflow) }}</span>
            </div>
          </div>

          <div class="mt-5 rounded-2xl border border-slate-200 p-4 text-sm">
            <div class="flex items-center justify-between">
              <span class="text-slate-500">合约风险</span>
              <span class="font-semibold text-slate-900">{{ audit?.risk_level_enum || audit?.risk_level || '--' }}</span>
            </div>
            <div class="mt-3 flex items-center justify-between">
              <span class="text-slate-500">买 / 卖税</span>
              <span class="font-semibold text-slate-900">{{ formatSigned(audit?.buy_tax, 2) }} / {{ formatSigned(audit?.sell_tax, 2) }}</span>
            </div>
            <div class="mt-3 flex items-center justify-between">
              <span class="text-slate-500">合约验证</span>
              <span class="font-semibold text-slate-900">{{ audit?.is_verified === true ? '已验证' : audit?.is_verified === false ? '未验证' : '--' }}</span>
            </div>
          </div>
        </aside>

        <main class="min-h-0 bg-slate-950 p-4">
          <TradingViewChart
            :data="chartData"
            :volume-data="volumeData"
            :colors="chartColors"
          />
        </main>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import TradingViewChart from '@/components/TradingViewChart.vue'
import type { CandlestickData, VolumeData } from '@/modules/market/contracts'
import type {
  BinanceWeb3HeatRankItemResponse,
  BinanceWeb3TokenAuditResponse,
  BinanceWeb3TokenDynamicResponse,
} from '../../types/market'

defineProps<{
  open: boolean
  token: BinanceWeb3HeatRankItemResponse | null
  interval: string
  intervals: string[]
  detailLoading: boolean
  detailError: string
  dynamic: BinanceWeb3TokenDynamicResponse | null
  audit: BinanceWeb3TokenAuditResponse | null
  chartData: CandlestickData[]
  volumeData: VolumeData[]
  chartColors: Record<string, string>
  formatScore: (value: number | null | undefined) => string
  formatPrice: (value: number | null | undefined) => string
  formatSigned: (value: number | null | undefined, digits?: number, suffix?: string, withSign?: boolean) => string
  formatCompact: (value: number | null | undefined) => string
  valueTone: (value: number | null | undefined, positiveIsGood?: boolean) => string
}>()

defineEmits<{
  close: []
  'update:interval': [interval: string]
}>()
</script>
