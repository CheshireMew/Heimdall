<template>
  <div class="h-full overflow-y-auto bg-slate-50 dark:bg-slate-900 transition-colors">
    <div class="mx-auto max-w-7xl p-6 space-y-6">
      <section class="rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800/90">
        <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.3em] text-cyan-600 dark:text-cyan-400">Binance</p>
            <h2 class="mt-2 text-3xl font-semibold text-slate-900 dark:text-white">Binance 市场看板</h2>
            <p class="mt-3 text-sm text-slate-600 dark:text-slate-300">现货强弱和永续结构放在一页里看。</p>
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

      <section class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <article
          v-for="card in summaryCards"
          :key="card.label"
          class="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-800"
        >
          <p class="text-xs font-bold uppercase tracking-wide text-slate-500 dark:text-slate-400">{{ card.label }}</p>
          <p class="mt-3 text-2xl font-semibold text-slate-900 dark:text-white">{{ card.primary }}</p>
          <p class="mt-2 text-sm" :class="card.tone">{{ card.secondary }}</p>
        </article>
      </section>

      <section v-if="error" class="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-600 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-300">
        {{ error }}
      </section>

      <section class="grid gap-6 xl:grid-cols-2">
        <article class="rounded-3xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
          <div class="border-b border-slate-200 px-5 py-4 dark:border-slate-700">
            <h3 class="text-lg font-semibold text-slate-900 dark:text-white">现货涨幅榜</h3>
          </div>
          <div class="overflow-x-auto">
            <table class="min-w-full text-left text-sm">
              <thead class="bg-slate-50 text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
                <tr>
                  <th class="px-5 py-3 font-semibold">Symbol</th>
                  <th class="px-5 py-3 font-semibold">24H</th>
                  <th class="px-5 py-3 font-semibold">Price</th>
                  <th class="px-5 py-3 font-semibold">Quote Vol</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in gainers" :key="item.symbol" class="border-t border-slate-100 dark:border-slate-700">
                  <td class="px-5 py-4 font-medium text-slate-900 dark:text-white">{{ item.symbol }}</td>
                  <td class="px-5 py-4" :class="changeClass(item.price_change_pct)">{{ formatSignedPercent(item.price_change_pct) }}</td>
                  <td class="px-5 py-4 text-slate-600 dark:text-slate-300">{{ formatPrice(item.last_price) }}</td>
                  <td class="px-5 py-4 text-slate-600 dark:text-slate-300">{{ formatCompact(item.quote_volume) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </article>

        <article class="rounded-3xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
          <div class="border-b border-slate-200 px-5 py-4 dark:border-slate-700">
            <h3 class="text-lg font-semibold text-slate-900 dark:text-white">现货跌幅榜</h3>
          </div>
          <div class="overflow-x-auto">
            <table class="min-w-full text-left text-sm">
              <thead class="bg-slate-50 text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
                <tr>
                  <th class="px-5 py-3 font-semibold">Symbol</th>
                  <th class="px-5 py-3 font-semibold">24H</th>
                  <th class="px-5 py-3 font-semibold">Price</th>
                  <th class="px-5 py-3 font-semibold">Quote Vol</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in losers" :key="item.symbol" class="border-t border-slate-100 dark:border-slate-700">
                  <td class="px-5 py-4 font-medium text-slate-900 dark:text-white">{{ item.symbol }}</td>
                  <td class="px-5 py-4" :class="changeClass(item.price_change_pct)">{{ formatSignedPercent(item.price_change_pct) }}</td>
                  <td class="px-5 py-4 text-slate-600 dark:text-slate-300">{{ formatPrice(item.last_price) }}</td>
                  <td class="px-5 py-4 text-slate-600 dark:text-slate-300">{{ formatCompact(item.quote_volume) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </article>
      </section>

      <section class="grid gap-6 xl:grid-cols-2">
        <article class="rounded-3xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
          <div class="border-b border-slate-200 px-5 py-4 dark:border-slate-700">
            <h3 class="text-lg font-semibold text-slate-900 dark:text-white">U 本位永续</h3>
          </div>
          <div class="overflow-x-auto">
            <table class="min-w-full text-left text-sm">
              <thead class="bg-slate-50 text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
                <tr>
                  <th class="px-5 py-3 font-semibold">Symbol</th>
                  <th class="px-5 py-3 font-semibold">24H</th>
                  <th class="px-5 py-3 font-semibold">Funding</th>
                  <th class="px-5 py-3 font-semibold">Quote Vol</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in usdmRows" :key="item.symbol" class="border-t border-slate-100 dark:border-slate-700">
                  <td class="px-5 py-4 font-medium text-slate-900 dark:text-white">{{ item.symbol }}</td>
                  <td class="px-5 py-4" :class="changeClass(item.price_change_pct)">{{ formatSignedPercent(item.price_change_pct) }}</td>
                  <td class="px-5 py-4" :class="changeClass(item.funding_rate_pct)">{{ formatSignedPercent(item.funding_rate_pct, 4) }}</td>
                  <td class="px-5 py-4 text-slate-600 dark:text-slate-300">{{ formatCompact(item.quote_volume) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </article>

        <article class="rounded-3xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
          <div class="border-b border-slate-200 px-5 py-4 dark:border-slate-700">
            <h3 class="text-lg font-semibold text-slate-900 dark:text-white">币本位永续</h3>
          </div>
          <div class="overflow-x-auto">
            <table class="min-w-full text-left text-sm">
              <thead class="bg-slate-50 text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
                <tr>
                  <th class="px-5 py-3 font-semibold">Symbol</th>
                  <th class="px-5 py-3 font-semibold">24H</th>
                  <th class="px-5 py-3 font-semibold">Funding</th>
                  <th class="px-5 py-3 font-semibold">Quote Vol</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in coinmRows" :key="item.symbol" class="border-t border-slate-100 dark:border-slate-700">
                  <td class="px-5 py-4 font-medium text-slate-900 dark:text-white">{{ item.symbol }}</td>
                  <td class="px-5 py-4" :class="changeClass(item.price_change_pct)">{{ formatSignedPercent(item.price_change_pct) }}</td>
                  <td class="px-5 py-4" :class="changeClass(item.funding_rate_pct)">{{ formatSignedPercent(item.funding_rate_pct, 4) }}</td>
                  <td class="px-5 py-4 text-slate-600 dark:text-slate-300">{{ formatCompact(item.quote_volume) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </article>
      </section>
    </div>
  </div>
</template>

<script setup>
defineOptions({ name: 'BinanceMarket' })

import { useBinanceMarketPage } from '@/modules/market'

const {
  loading,
  error,
  gainers,
  losers,
  usdmRows,
  coinmRows,
  summaryCards,
  fetchData,
  formatSignedPercent,
  formatCompact,
  formatPrice,
  changeClass,
} = useBinanceMarketPage()
</script>
