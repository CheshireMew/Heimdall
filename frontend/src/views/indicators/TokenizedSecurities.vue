<template>
  <div class="h-full overflow-y-auto bg-slate-50 dark:bg-slate-900 transition-colors">
    <div class="mx-auto max-w-7xl p-6 space-y-6">
      <section class="rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800/90">
        <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.3em] text-cyan-600 dark:text-cyan-400">RWA</p>
            <h2 class="mt-2 text-3xl font-semibold text-slate-900 dark:text-white">代币化美股</h2>
            <p class="mt-3 text-sm text-slate-600 dark:text-slate-300">用 Binance Web3 的 RWA 数据补股票代币列表、状态、基本面和 K 线。</p>
          </div>

          <button
            @click="fetchData"
            :disabled="loading"
            class="rounded-2xl bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-cyan-600 dark:hover:bg-cyan-500"
          >
            {{ loading ? '加载中...' : '刷新' }}
          </button>
        </div>
      </section>

      <IndicatorSummaryCards :cards="summaryCards" />

      <section v-if="error" class="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-600 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-300">
        {{ error }}
      </section>

      <section class="grid gap-6 xl:grid-cols-[1.2fr_1.8fr]">
        <article class="rounded-3xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
          <div class="border-b border-slate-200 px-5 py-4 dark:border-slate-700">
            <h3 class="text-lg font-semibold text-slate-900 dark:text-white">Ticker 列表</h3>
          </div>
          <div class="overflow-x-auto">
            <table class="min-w-full text-left text-sm">
              <thead class="bg-slate-50 text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
                <tr>
                  <th class="px-5 py-3 font-semibold">Ticker</th>
                  <th class="px-5 py-3 font-semibold">Token</th>
                  <th class="px-5 py-3 font-semibold">Chain</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="item in rows"
                  :key="`${item.chain_id}:${item.contract_address}`"
                  class="cursor-pointer border-t border-slate-100 dark:border-slate-700"
                  :class="selectedKey === `${item.chain_id}:${item.contract_address}` ? 'bg-cyan-50 dark:bg-cyan-500/10' : ''"
                  @click="selectedKey = `${item.chain_id}:${item.contract_address}`"
                >
                  <td class="px-5 py-4 font-medium text-slate-900 dark:text-white">{{ item.ticker }}</td>
                  <td class="px-5 py-4 text-slate-600 dark:text-slate-300">{{ item.symbol }}</td>
                  <td class="px-5 py-4 text-slate-600 dark:text-slate-300">{{ item.chain_id }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </article>

        <div class="space-y-6">
          <article class="rounded-3xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
            <div class="border-b border-slate-200 px-5 py-4 dark:border-slate-700">
              <h3 class="text-lg font-semibold text-slate-900 dark:text-white">{{ detailLoading ? '明细加载中...' : '当前标的' }}</h3>
            </div>
            <div class="grid gap-4 p-5 md:grid-cols-2">
              <div>
                <div class="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">Company</div>
                <div class="mt-1 text-base font-semibold text-slate-900 dark:text-white">{{ meta?.company_info?.companyNameZh || meta?.company_info?.companyName || '--' }}</div>
              </div>
              <div>
                <div class="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">CEO</div>
                <div class="mt-1 text-base font-semibold text-slate-900 dark:text-white">{{ meta?.company_info?.ceo || '--' }}</div>
              </div>
              <div>
                <div class="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">P/E</div>
                <div class="mt-1 text-base font-semibold text-slate-900 dark:text-white">{{ dynamic?.stock_info?.priceToEarnings || '--' }}</div>
              </div>
              <div>
                <div class="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">Dividend Yield</div>
                <div class="mt-1 text-base font-semibold text-slate-900 dark:text-white">{{ formatPercent(dynamic?.stock_info?.dividendYield) }}</div>
              </div>
            </div>
          </article>

          <article class="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-800">
            <div class="mb-4 flex items-center justify-between">
              <div>
                <h3 class="text-lg font-semibold text-slate-900 dark:text-white">K 线</h3>
                <p class="text-sm text-slate-500 dark:text-slate-400">{{ selectedItem?.ticker || '--' }}</p>
              </div>
              <div class="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
                {{ assetStatus?.marketStatus || marketStatus?.reasonCode || '--' }}
              </div>
            </div>

            <div class="h-[360px] rounded-2xl border border-slate-200 bg-slate-50 p-2 dark:border-slate-700 dark:bg-slate-900">
              <TradingViewChart :data="chartData" chart-type="candlestick" />
            </div>
          </article>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
defineOptions({ name: 'TokenizedSecurities' })

import TradingViewChart from '@/components/TradingViewChart.vue'
import IndicatorSummaryCards from '@/components/market/IndicatorSummaryCards.vue'
import { useTokenizedSecuritiesPage } from '@/modules/market'

const {
  loading,
  detailLoading,
  error,
  rows,
  selectedKey,
  selectedItem,
  marketStatus,
  meta,
  assetStatus,
  dynamic,
  chartData,
  summaryCards,
  fetchData,
  formatPercent,
} = useTokenizedSecuritiesPage()
</script>
