<template>
  <div class="h-full overflow-y-auto bg-slate-50 dark:bg-slate-900 transition-colors">
    <div class="mx-auto max-w-7xl p-6 space-y-6">
      <section class="rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800/90">
        <div class="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div class="max-w-3xl">
            <p class="text-xs font-semibold uppercase tracking-[0.3em] text-cyan-600 dark:text-cyan-400">
              {{ $t('cryptoIndex.eyebrow') }}
            </p>
            <h2 class="mt-2 text-3xl font-semibold text-slate-900 dark:text-white">
              {{ $t('cryptoIndex.title') }}
            </h2>
            <p class="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
              {{ $t('cryptoIndex.subtitle') }}
            </p>
          </div>

          <div class="flex flex-wrap items-end gap-4">
            <div>
              <label class="mb-1 block text-xs font-bold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                {{ $t('cryptoIndex.topN') }}
              </label>
              <div class="flex rounded-2xl bg-slate-100 p-1 dark:bg-slate-900">
                <button
                  v-for="size in basketSizes"
                  :key="size"
                  @click="setTopN(size)"
                  :class="[
                    'rounded-xl px-4 py-2 text-sm font-semibold transition',
                    topN === size
                      ? 'bg-cyan-600 text-white shadow-sm'
                      : 'text-slate-500 hover:bg-white hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white'
                  ]"
                >
                  Top {{ size }}
                </button>
              </div>
            </div>

            <div class="w-32">
              <label class="mb-1 block text-xs font-bold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                {{ $t('cryptoIndex.historyDays') }}
              </label>
              <select
                v-model.number="days"
                class="w-full rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-cyan-500 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100"
              >
                <option :value="30">30D</option>
                <option :value="90">90D</option>
                <option :value="180">180D</option>
                <option :value="365">365D</option>
              </select>
            </div>

            <button
              @click="fetchData"
              :disabled="loading"
              class="rounded-2xl bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-cyan-600 dark:hover:bg-cyan-500"
            >
              <span v-if="loading">{{ $t('cryptoIndex.loading') }}</span>
              <span v-else>{{ $t('cryptoIndex.refresh') }}</span>
            </button>
          </div>
        </div>
      </section>

      <IndicatorSummaryCards :cards="summaryCards" />

      <section
        v-if="data?.is_partial"
        class="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-200"
      >
        Using {{ data?.resolved_constituents_count || constituents.length }}/{{ topN }} assets because some upstream history requests were rate-limited.
      </section>

      <section class="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-800">
        <div class="mb-4 flex items-center justify-between">
          <div>
            <h3 class="text-lg font-semibold text-slate-900 dark:text-white">{{ $t('cryptoIndex.chartTitle') }}</h3>
            <p class="text-sm text-slate-500 dark:text-slate-400">
              {{ summary?.methodology || $t('cryptoIndex.methodologyFallback') }}
            </p>
          </div>
          <p class="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
            {{ $t('cryptoIndex.base') }} {{ data?.base_value || 1000 }}
          </p>
        </div>

        <div class="h-[420px] rounded-2xl border border-slate-200 bg-slate-50 p-2 dark:border-slate-700 dark:bg-slate-900">
          <TradingViewChart
            :data="chartData"
            chart-type="area"
            :colors="chartColors"
          />
        </div>
      </section>

      <section class="rounded-3xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
        <div class="border-b border-slate-200 px-5 py-4 dark:border-slate-700">
          <h3 class="text-lg font-semibold text-slate-900 dark:text-white">{{ $t('cryptoIndex.tableTitle') }}</h3>
          <p class="text-sm text-slate-500 dark:text-slate-400">{{ $t('cryptoIndex.tableSubtitle') }}</p>
        </div>

        <div v-if="error" class="px-5 py-8 text-sm text-rose-500">{{ error }}</div>
        <div v-else class="overflow-x-auto">
          <table class="min-w-full text-left text-sm">
            <thead class="bg-slate-50 text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
              <tr>
                <th class="px-5 py-3 font-semibold">#</th>
                <th class="px-5 py-3 font-semibold">{{ $t('cryptoIndex.asset') }}</th>
                <th class="px-5 py-3 font-semibold">{{ $t('cryptoIndex.price') }}</th>
                <th class="px-5 py-3 font-semibold">{{ $t('cryptoIndex.marketCap') }}</th>
                <th class="px-5 py-3 font-semibold">{{ $t('cryptoIndex.weight') }}</th>
                <th class="px-5 py-3 font-semibold">24H</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="coin in constituents"
                :key="coin.id"
                class="border-t border-slate-100 text-slate-700 dark:border-slate-700 dark:text-slate-200"
              >
                <td class="px-5 py-4 font-medium">{{ coin.rank }}</td>
                <td class="px-5 py-4">
                  <div class="flex items-center gap-3">
                    <img v-if="coin.image" :src="coin.image" :alt="coin.name" class="h-8 w-8 rounded-full" />
                    <div>
                      <p class="font-semibold text-slate-900 dark:text-white">{{ coin.name }}</p>
                      <p class="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">{{ coin.symbol }}</p>
                    </div>
                  </div>
                </td>
                <td class="px-5 py-4">{{ formatCurrency(coin.price) }}</td>
                <td class="px-5 py-4">{{ formatCompactCurrency(coin.market_cap) }}</td>
                <td class="px-5 py-4">{{ formatPercent(weightOf(coin)) }}</td>
                <td class="px-5 py-4" :class="changeClass(coin.market_cap_change_24h_pct)">
                  {{ formatSignedPercent(coin.market_cap_change_24h_pct) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
defineOptions({ name: 'CryptoIndex' })

import TradingViewChart from '@/components/TradingViewChart.vue'
import IndicatorSummaryCards from '@/components/market/IndicatorSummaryCards.vue'
import { useCryptoIndexPage } from '@/modules/market'

const {
  basketSizes,
  topN,
  days,
  loading,
  error,
  data,
  chartColors,
  summary,
  constituents,
  chartData,
  summaryCards,
  setTopN,
  fetchData,
  weightOf,
  formatCurrency,
  formatCompactCurrency,
  formatPercent,
  formatSignedPercent,
  changeClass,
} = useCryptoIndexPage()
</script>
