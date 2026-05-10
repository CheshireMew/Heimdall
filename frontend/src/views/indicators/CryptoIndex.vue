<template>
  <div class="app-page">
    <div class="app-page-inner-wide">
      <section class="app-hero-panel">
        <div class="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div class="max-w-3xl">
            <p class="app-eyebrow">
              {{ $t('cryptoIndex.eyebrow') }}
            </p>
            <h2 class="app-title mt-2">
              {{ $t('cryptoIndex.title') }}
            </h2>
            <p class="app-subtitle mt-3">
              {{ $t('cryptoIndex.subtitle') }}
            </p>
          </div>

          <div class="flex flex-wrap items-end gap-4">
            <div>
              <label class="mb-1 block text-xs font-bold uppercase tracking-wide text-stone-500 dark:text-slate-400">
                {{ $t('cryptoIndex.topN') }}
              </label>
              <div class="flex border border-stone-200 bg-white p-1 dark:border-slate-700 dark:bg-slate-900">
                <button
                  v-for="size in basketSizes"
                  :key="size"
                  @click="setTopN(size)"
                  :class="[
                    'px-4 py-2 text-sm font-semibold transition',
                    topN === size
                      ? 'bg-[#0f6b4f] text-white shadow-sm dark:bg-emerald-500 dark:text-slate-950'
                      : 'text-stone-500 hover:bg-stone-100 hover:text-stone-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white'
                  ]"
                >
                  Top {{ size }}
                </button>
              </div>
            </div>

            <div class="w-32">
              <label class="mb-1 block text-xs font-bold uppercase tracking-wide text-stone-500 dark:text-slate-400">
                {{ $t('cryptoIndex.historyDays') }}
              </label>
              <select
                v-model.number="days"
                class="app-control w-full"
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
              class="app-button-primary"
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
        class="border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-200"
      >
        Using {{ data?.resolved_constituents_count || constituents.length }}/{{ topN }} assets because some upstream history requests were rate-limited.
      </section>

      <section class="app-panel p-5">
        <div class="mb-4 flex items-center justify-between">
          <div>
            <h3 class="app-section-title">{{ $t('cryptoIndex.chartTitle') }}</h3>
            <p class="app-muted text-sm">
              {{ summary?.methodology || $t('cryptoIndex.methodologyFallback') }}
            </p>
          </div>
          <p class="app-muted text-xs uppercase tracking-wide">
            {{ $t('cryptoIndex.base') }} {{ data?.base_value || 1000 }}
          </p>
        </div>

        <div class="app-chart-frame h-[420px]">
          <TradingViewChart
            :data="chartData"
            chart-type="area"
            :colors="chartColors"
          />
        </div>
      </section>

      <section class="app-panel">
        <div class="app-panel-header">
          <h3 class="app-section-title">{{ $t('cryptoIndex.tableTitle') }}</h3>
          <p class="app-muted text-sm">{{ $t('cryptoIndex.tableSubtitle') }}</p>
        </div>

        <div v-if="error" class="px-5 py-8 text-sm text-rose-500">{{ error }}</div>
        <div v-else class="overflow-x-auto">
          <table class="min-w-full text-left text-sm">
            <thead class="app-table-head">
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
                class="app-table-row"
              >
                <td class="px-5 py-4 font-medium">{{ coin.rank }}</td>
                <td class="px-5 py-4">
                  <div class="flex items-center gap-3">
                    <img v-if="coin.image" :src="coin.image" :alt="coin.name" class="h-8 w-8 rounded-full" />
                    <div>
                      <p class="font-semibold text-stone-950 dark:text-white">{{ coin.name }}</p>
                      <p class="text-xs uppercase tracking-wide text-stone-500 dark:text-slate-400">{{ coin.symbol }}</p>
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
