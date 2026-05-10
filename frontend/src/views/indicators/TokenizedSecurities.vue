<template>
  <div class="app-page">
    <div class="app-page-inner-wide">
      <section class="app-hero-panel">
        <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p class="app-eyebrow">RWA</p>
            <h2 class="app-title mt-2">代币化美股</h2>
            <p class="app-subtitle mt-3">用 Binance Web3 的 RWA 数据补股票代币列表、状态、基本面和 K 线。</p>
          </div>

          <button
            @click="fetchData"
            :disabled="loading"
            class="app-button-primary"
          >
            {{ loading ? '加载中...' : '刷新' }}
          </button>
        </div>
      </section>

      <IndicatorSummaryCards :cards="summaryCards" />

      <section v-if="error" class="border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-600 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-300">
        {{ error }}
      </section>

      <section class="grid gap-6 xl:grid-cols-[1.2fr_1.8fr]">
        <article class="app-panel">
          <div class="app-panel-header">
            <h3 class="app-section-title">Ticker 列表</h3>
          </div>
          <div class="overflow-x-auto">
            <table class="min-w-full text-left text-sm">
              <thead class="app-table-head">
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
                  class="app-table-row cursor-pointer"
                  :class="selectedKey === `${item.chain_id}:${item.contract_address}` ? 'bg-[#edf3ee] dark:bg-emerald-500/10' : ''"
                  @click="selectedKey = `${item.chain_id}:${item.contract_address}`"
                >
                  <td class="px-5 py-4 font-medium text-stone-950 dark:text-white">{{ item.ticker }}</td>
                  <td class="px-5 py-4 text-stone-600 dark:text-slate-300">{{ item.symbol }}</td>
                  <td class="px-5 py-4 text-stone-600 dark:text-slate-300">{{ item.chain_id }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </article>

        <div class="space-y-6">
          <article class="app-panel">
            <div class="app-panel-header">
              <h3 class="app-section-title">{{ detailLoading ? '明细加载中...' : '当前标的' }}</h3>
            </div>
            <div class="grid gap-4 p-5 md:grid-cols-2">
              <div>
                <div class="text-xs uppercase tracking-wide text-stone-500 dark:text-slate-400">Company</div>
                <div class="mt-1 text-base font-semibold text-stone-950 dark:text-white">{{ meta?.company_info?.companyNameZh || meta?.company_info?.companyName || '--' }}</div>
              </div>
              <div>
                <div class="text-xs uppercase tracking-wide text-stone-500 dark:text-slate-400">CEO</div>
                <div class="mt-1 text-base font-semibold text-stone-950 dark:text-white">{{ meta?.company_info?.ceo || '--' }}</div>
              </div>
              <div>
                <div class="text-xs uppercase tracking-wide text-stone-500 dark:text-slate-400">P/E</div>
                <div class="mt-1 text-base font-semibold text-stone-950 dark:text-white">{{ dynamic?.stock_info?.priceToEarnings || '--' }}</div>
              </div>
              <div>
                <div class="text-xs uppercase tracking-wide text-stone-500 dark:text-slate-400">Dividend Yield</div>
                <div class="mt-1 text-base font-semibold text-stone-950 dark:text-white">{{ formatPercent(dynamic?.stock_info?.dividendYield) }}</div>
              </div>
            </div>
          </article>

          <article class="app-panel p-5">
            <div class="mb-4 flex items-center justify-between">
              <div>
                <h3 class="app-section-title">K 线</h3>
                <p class="app-muted text-sm">{{ selectedItem?.ticker || '--' }}</p>
              </div>
              <div class="app-muted text-xs uppercase tracking-wide">
                {{ assetStatus?.marketStatus || marketStatus?.reasonCode || '--' }}
              </div>
            </div>

            <div class="app-chart-frame h-[360px]">
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
