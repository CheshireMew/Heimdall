<template>
  <div
    v-if="open && token"
    class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/55 p-4 backdrop-blur-sm"
    @click.self="$emit('close')"
  >
    <section class="flex h-[min(90vh,860px)] w-full max-w-7xl flex-col overflow-hidden rounded-[32px] border border-slate-200/80 bg-white shadow-2xl dark:border-slate-700 dark:bg-slate-800">
      <header class="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 px-6 py-5 dark:border-slate-700">
        <div class="flex items-center gap-4">
          <Web3TokenIcon :src="token.icon_url" :symbol="token.symbol" size="lg" />
          <div>
            <div class="flex items-center gap-3">
              <h3 class="text-2xl font-semibold text-slate-900 dark:text-white">{{ token.symbol || '--' }}</h3>
              <span class="rounded-full bg-cyan-50 px-3 py-1 text-xs font-semibold text-cyan-700 dark:bg-cyan-500/10 dark:text-cyan-300">{{ t('web3Rank.dialog.score') }} {{ formatScore(token.heat_score) }}</span>
            </div>
            <p class="mt-2 max-w-[680px] truncate text-sm text-slate-500 dark:text-slate-400">{{ token.contract_address }}</p>
          </div>
        </div>

        <div class="flex items-center gap-3">
          <div class="flex flex-wrap gap-2 rounded-full border border-slate-200 bg-slate-50 p-1 dark:border-slate-700 dark:bg-slate-900">
            <button
              v-for="item in intervals"
              :key="item"
              type="button"
              class="rounded-full px-4 py-2 text-sm transition"
              :class="interval === item ? 'bg-slate-900 text-white dark:bg-cyan-600' : 'text-slate-600 hover:bg-white dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white'"
              @click="$emit('update:interval', item)"
            >
              {{ item }}
            </button>
          </div>
          <button
            type="button"
            class="rounded-full border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-900 dark:hover:text-white"
            @click="$emit('close')"
          >
            {{ t('web3Rank.dialog.close') }}
          </button>
        </div>
      </header>

      <div v-if="detailError" class="border-b border-rose-100 bg-rose-50 px-6 py-3 text-sm text-rose-600 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-300">{{ detailError }}</div>

      <div class="grid min-h-0 flex-1 gap-0 lg:grid-cols-[360px_minmax(0,1fr)]">
        <aside class="overflow-y-auto border-r border-slate-200 p-5 dark:border-slate-700">
          <div v-if="detailLoading" class="rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-500 dark:bg-slate-900 dark:text-slate-400">{{ t('web3Rank.dialog.loading') }}</div>

          <div class="grid grid-cols-2 gap-3">
            <div class="rounded-2xl bg-slate-50 px-4 py-3 dark:bg-slate-900/70">
              <div class="text-xs text-slate-400 dark:text-slate-500">{{ t('web3Rank.dialog.price') }}</div>
              <div class="mt-2 font-semibold text-slate-900 dark:text-white">{{ formatPrice(dynamic?.price ?? token.metrics?.price) }}</div>
            </div>
            <div class="rounded-2xl bg-slate-50 px-4 py-3 dark:bg-slate-900/70">
              <div class="text-xs text-slate-400 dark:text-slate-500">24H</div>
              <div class="mt-2 font-semibold" :class="valueTone(dynamic?.percent_change_24h ?? token.metrics?.percent_change_24h)">
                {{ formatSigned(dynamic?.percent_change_24h ?? token.metrics?.percent_change_24h) }}
              </div>
            </div>
            <div class="rounded-2xl bg-slate-50 px-4 py-3 dark:bg-slate-900/70">
              <div class="text-xs text-slate-400 dark:text-slate-500">{{ t('web3Rank.dialog.marketCap') }}</div>
              <div class="mt-2 font-semibold text-slate-900 dark:text-white">{{ formatCompact(dynamic?.market_cap ?? token.metrics?.market_cap) }}</div>
            </div>
            <div class="rounded-2xl bg-slate-50 px-4 py-3 dark:bg-slate-900/70">
              <div class="text-xs text-slate-400 dark:text-slate-500">{{ t('web3Rank.dialog.liquidity') }}</div>
              <div class="mt-2 font-semibold text-slate-900 dark:text-white">{{ formatCompact(dynamic?.liquidity ?? token.metrics?.liquidity) }}</div>
            </div>
            <div class="rounded-2xl bg-slate-50 px-4 py-3 dark:bg-slate-900/70">
              <div class="text-xs text-slate-400 dark:text-slate-500">{{ t('web3Rank.dialog.volume1h') }}</div>
              <div class="mt-2 font-semibold text-slate-900 dark:text-white">{{ formatCompact(dynamic?.volume_1h ?? token.metrics?.volume_1h) }}</div>
            </div>
            <div class="rounded-2xl bg-slate-50 px-4 py-3 dark:bg-slate-900/70">
              <div class="text-xs text-slate-400 dark:text-slate-500">{{ t('web3Rank.dialog.volume24h') }}</div>
              <div class="mt-2 font-semibold text-slate-900 dark:text-white">{{ formatCompact(dynamic?.volume_24h ?? token.metrics?.volume_24h) }}</div>
            </div>
            <div class="rounded-2xl bg-slate-50 px-4 py-3 dark:bg-slate-900/70">
              <div class="text-xs text-slate-400 dark:text-slate-500">{{ t('web3Rank.dialog.holders') }}</div>
              <div class="mt-2 font-semibold text-slate-900 dark:text-white">{{ formatCompact(dynamic?.holders ?? token.metrics?.holders) }}</div>
            </div>
            <div class="rounded-2xl bg-slate-50 px-4 py-3 dark:bg-slate-900/70">
              <div class="text-xs text-slate-400 dark:text-slate-500">{{ t('web3Rank.dialog.trades') }}</div>
              <div class="mt-2 font-semibold text-slate-900 dark:text-white">{{ formatCompact(dynamic?.count_24h ?? token.metrics?.count_24h) }}</div>
            </div>
          </div>

          <div class="mt-5 rounded-[26px] bg-slate-950 p-4 text-sm text-white ring-1 ring-slate-800 dark:bg-slate-900">
            <div class="flex items-center justify-between">
              <span class="text-slate-400">{{ t('web3Rank.dialog.topSearch') }}</span>
              <span>{{ token.components?.top_search?.toFixed?.(1) ?? '--' }}</span>
            </div>
            <div class="mt-3 flex items-center justify-between">
              <span class="text-slate-400">{{ t('web3Rank.dialog.trending') }}</span>
              <span>{{ token.components?.trending?.toFixed?.(1) ?? '--' }}</span>
            </div>
            <div class="mt-3 flex items-center justify-between">
              <span class="text-slate-400">{{ t('web3Rank.dialog.social') }}</span>
              <span>{{ token.components?.social_hype?.toFixed?.(1) ?? '--' }}</span>
            </div>
            <div class="mt-3 flex items-center justify-between">
              <span class="text-slate-400">{{ t('web3Rank.dialog.volumeTx') }}</span>
              <span>{{ token.components?.volume_growth?.toFixed?.(1) ?? '--' }} / {{ token.components?.transaction_growth?.toFixed?.(1) ?? '--' }}</span>
            </div>
            <div class="mt-3 flex items-center justify-between">
              <span class="text-slate-400">{{ t('web3Rank.dialog.smartMoney') }}</span>
              <span>{{ formatCompact(token.metrics?.smart_money_inflow) }}</span>
            </div>
            <div class="mt-3 flex items-center justify-between">
              <span class="text-slate-400">{{ t('web3Rank.dialog.meme') }}</span>
              <span>{{ token.ranks?.meme ? `#${token.ranks.meme}` : '--' }}</span>
            </div>
          </div>

          <div class="mt-5 rounded-2xl border border-slate-200 p-4 text-sm dark:border-slate-700">
            <div class="flex items-center justify-between">
              <span class="text-slate-500 dark:text-slate-400">{{ t('web3Rank.dialog.sentiment') }}</span>
              <span class="font-semibold text-slate-900 dark:text-white">{{ token.sentiment || '--' }}</span>
            </div>
            <p v-if="token.summary" class="mt-3 text-xs leading-5 text-slate-500 dark:text-slate-400">{{ token.summary }}</p>
            <div class="mt-3 grid grid-cols-2 gap-2 text-xs">
              <div class="rounded-xl bg-slate-50 px-3 py-2 dark:bg-slate-900/70">
                <div class="text-slate-400">{{ t('web3Rank.dialog.topSearch') }}</div>
                <div class="mt-1 font-semibold text-slate-900 dark:text-white">{{ token.ranks?.top_search ? `#${token.ranks.top_search}` : '--' }}</div>
              </div>
              <div class="rounded-xl bg-slate-50 px-3 py-2 dark:bg-slate-900/70">
                <div class="text-slate-400">{{ t('web3Rank.dialog.trending') }}</div>
                <div class="mt-1 font-semibold text-slate-900 dark:text-white">{{ token.ranks?.trending ? `#${token.ranks.trending}` : '--' }}</div>
              </div>
              <div class="rounded-xl bg-slate-50 px-3 py-2 dark:bg-slate-900/70">
                <div class="text-slate-400">{{ t('web3Rank.dialog.socialHype') }}</div>
                <div class="mt-1 font-semibold text-slate-900 dark:text-white">{{ formatCompact(token.metrics?.social_hype) }}</div>
              </div>
              <div class="rounded-xl bg-slate-50 px-3 py-2 dark:bg-slate-900/70">
                <div class="text-slate-400">{{ t('web3Rank.dialog.memeScore') }}</div>
                <div class="mt-1 font-semibold text-slate-900 dark:text-white">{{ formatCompact(token.metrics?.meme_score) }}</div>
              </div>
            </div>
          </div>

          <div class="mt-5 rounded-2xl border border-slate-200 p-4 text-sm dark:border-slate-700">
            <div class="flex items-center justify-between">
              <span class="text-slate-500 dark:text-slate-400">{{ t('web3Rank.dialog.contractRisk') }}</span>
              <span class="font-semibold text-slate-900 dark:text-white">{{ audit?.risk_level_enum || audit?.risk_level || '--' }}</span>
            </div>
            <div class="mt-3 flex items-center justify-between">
              <span class="text-slate-500 dark:text-slate-400">{{ t('web3Rank.dialog.buySellTax') }}</span>
              <span class="font-semibold text-slate-900 dark:text-white">{{ formatSigned(audit?.buy_tax, 2) }} / {{ formatSigned(audit?.sell_tax, 2) }}</span>
            </div>
            <div class="mt-3 flex items-center justify-between">
              <span class="text-slate-500 dark:text-slate-400">{{ t('web3Rank.dialog.contractVerification') }}</span>
              <span class="font-semibold text-slate-900 dark:text-white">{{ audit?.is_verified === true ? t('web3Rank.dialog.verified') : audit?.is_verified === false ? t('web3Rank.dialog.unverified') : '--' }}</span>
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
import Web3TokenIcon from '@/components/market/Web3TokenIcon.vue'
import { useI18n } from 'vue-i18n'
import type {
  BinanceWeb3HeatRankItem,
  BinanceWeb3TokenAudit,
  BinanceWeb3TokenDynamic,
  CandlestickData,
  VolumeData,
} from '@/modules/market/contracts'

const { t } = useI18n()

defineProps<{
  open: boolean
  token: BinanceWeb3HeatRankItem | null
  interval: string
  intervals: string[]
  detailLoading: boolean
  detailError: string
  dynamic: BinanceWeb3TokenDynamic | null
  audit: BinanceWeb3TokenAudit | null
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
