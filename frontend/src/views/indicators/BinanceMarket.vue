<template>
  <div class="h-full overflow-y-auto bg-[radial-gradient(circle_at_top,rgba(8,145,178,0.08),transparent_38%),linear-gradient(180deg,#f8fafc_0%,#eef2ff_100%)] transition-colors dark:bg-none dark:bg-slate-950">
    <div class="space-y-6 p-6 lg:p-8">
      <section class="grid gap-6 lg:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)] 2xl:grid-cols-[1.6fr_1fr] 2xl:gap-8">
        <div class="space-y-6">
          <section class="space-y-4">
            <div class="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
              <div>
                <h3 class="text-xl font-semibold text-slate-900 dark:text-white">{{ t('binanceMarket.rankTitle') }}</h3>
                <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">{{ t('binanceMarket.rankSubtitle') }}</p>
              </div>

              <div class="flex flex-wrap items-center gap-3 text-sm">
                <button
                  type="button"
                  @click="autoRefresh = !autoRefresh"
                  class="flex items-center gap-2 rounded-xl bg-slate-50 px-3 py-1.5 ring-1 ring-slate-200 transition hover:bg-slate-100 dark:bg-slate-900 dark:ring-slate-700 dark:hover:bg-slate-800"
                >
                  <span class="text-slate-500 dark:text-slate-400">{{ t('binanceMarket.autoRefresh') }}</span>
                  <span :class="autoRefresh ? 'font-semibold text-cyan-600 dark:text-cyan-400' : 'text-slate-400 dark:text-slate-500'">{{ autoRefresh ? t('binanceMarket.autoRefreshOn') : t('binanceMarket.autoRefreshOff') }}</span>
                </button>

                <button
                  @click="fetchData"
                  :disabled="loading"
                  class="rounded-xl bg-slate-900 px-4 py-1.5 font-medium text-white transition hover:bg-slate-800 disabled:opacity-50 dark:bg-cyan-600 dark:hover:bg-cyan-500"
                >
                  {{ loading ? t('binanceMarket.refreshing') : t('binanceMarket.refresh') }}
                </button>
              </div>
            </div>

            <div class="grid gap-6 xl:grid-cols-2">
              <article class="overflow-hidden rounded-[30px] border border-slate-200/70 bg-white/90 shadow-sm dark:border-slate-700 dark:bg-slate-800/90 xl:col-span-2">
                <div class="flex items-center justify-between border-b border-slate-200 px-5 py-4 dark:border-slate-700">
                  <div>
                    <h4 class="text-lg font-semibold text-slate-900 dark:text-white">{{ t('binanceMarket.tables.rankContract') }}</h4>
                    <p class="text-sm text-slate-500 dark:text-slate-400">{{ t('binanceMarket.tables.contractSortHint') }}</p>
                  </div>
                  <div class="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600 dark:bg-slate-900 dark:text-slate-300">
                    {{ contractSort.field === 'price_change_pct' ? t('binanceMarket.tables.sortBy24h') : contractSort.field === 'funding_rate_pct' ? t('binanceMarket.tables.sortByFunding') : t('binanceMarket.tables.sortByVolume') }}
                  </div>
                </div>

                <div class="overflow-x-auto">
                  <table class="min-w-full text-left text-sm">
                    <thead class="bg-slate-50 text-slate-500 dark:bg-slate-900/70 dark:text-slate-400">
                      <tr>
                        <th class="px-5 py-3 font-semibold">{{ t('binanceMarket.columns.asset') }}</th>
                        <th class="px-5 py-3 font-semibold">
                          <button
                            type="button"
                            @click="toggleContractSort('price_change_pct')"
                            class="inline-flex items-center gap-2 transition"
                            :class="contractSort.field === 'price_change_pct' ? 'text-slate-900 dark:text-white' : 'hover:text-slate-700 dark:hover:text-slate-200'"
                          >
                            <span>{{ t('binanceMarket.columns.change24hShort') }}</span>
                            <span class="text-xs">{{ sortDirectionIcon(contractSort.field === 'price_change_pct', contractSort.direction) }}</span>
                          </button>
                        </th>
                        <th class="px-5 py-3 font-semibold">{{ t('binanceMarket.columns.price') }}</th>
                        <th class="px-5 py-3 font-semibold">
                          <button
                            type="button"
                            @click="toggleContractSort('funding_rate_pct')"
                            class="inline-flex items-center gap-2 transition"
                            :class="contractSort.field === 'funding_rate_pct' ? 'text-slate-900 dark:text-white' : 'hover:text-slate-700 dark:hover:text-slate-200'"
                          >
                            <span>{{ t('binanceMarket.columns.funding') }}</span>
                            <span class="text-xs">{{ sortDirectionIcon(contractSort.field === 'funding_rate_pct', contractSort.direction) }}</span>
                          </button>
                        </th>
                        <th class="px-5 py-3 font-semibold">
                          <button
                            type="button"
                            @click="toggleContractSort('quote_volume')"
                            class="inline-flex items-center gap-2 transition"
                            :class="contractSort.field === 'quote_volume' ? 'text-slate-900 dark:text-white' : 'hover:text-slate-700 dark:hover:text-slate-200'"
                          >
                            <span>{{ t('binanceMarket.columns.quoteVolume') }}</span>
                            <span class="text-xs">{{ sortDirectionIcon(contractSort.field === 'quote_volume', contractSort.direction) }}</span>
                          </button>
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr
                        v-for="item in contractRows"
                        :key="`${item.market}-${item.symbol}`"
                        class="cursor-pointer border-t border-slate-100 transition hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-700/50"
                        @click="openChart(item)"
                      >
                        <td class="px-5 py-4 font-medium text-slate-900 dark:text-white">
                          <button
                            type="button"
                            class="rounded-full px-2 py-1 transition hover:bg-cyan-50 hover:text-cyan-700 dark:hover:bg-cyan-500/10 dark:hover:text-cyan-300"
                            @click.stop="openChart(item)"
                          >
                            {{ displaySymbol(item.symbol) }}
                          </button>
                        </td>
                        <td class="px-5 py-4" :class="valueTone(item.price_change_pct)">{{ formatSigned(item.price_change_pct) }}</td>
                        <td class="px-5 py-4 text-slate-600 dark:text-slate-300">{{ formatPrice(item.mark_price ?? item.last_price) }}</td>
                        <td class="px-5 py-4" :class="valueTone(item.funding_rate_pct)">{{ formatSigned(item.funding_rate_pct, 4) }}</td>
                        <td class="px-5 py-4 text-slate-600 dark:text-slate-300">{{ formatCompact(item.quote_volume) }}</td>
                      </tr>
                      <tr v-if="!contractRows.length">
                        <td colspan="5" class="px-5 py-8 text-center text-sm text-slate-400 dark:text-slate-500">{{ t('binanceMarket.tables.noContractRows') }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </article>

              <article class="overflow-hidden rounded-[30px] border border-slate-200/70 bg-white/90 shadow-sm dark:border-slate-700 dark:bg-slate-800/90 xl:col-span-2">
                <div class="flex items-center justify-between border-b border-slate-200 px-5 py-4 dark:border-slate-700">
                  <div>
                    <h4 class="text-lg font-semibold text-slate-900 dark:text-white">{{ t('binanceMarket.tables.rankSpot') }}</h4>
                    <p class="text-sm text-slate-500 dark:text-slate-400">{{ t('binanceMarket.tables.spotSortHint') }}</p>
                  </div>
                  <div class="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600 dark:bg-slate-900 dark:text-slate-300">
                    {{ spotSort.field === 'price_change_pct' ? (spotSort.direction === 'desc' ? t('binanceMarket.tables.sortByGainers') : t('binanceMarket.tables.sortByLosers')) : t('binanceMarket.tables.sortByVolume') }}
                  </div>
                </div>
                <div class="overflow-x-auto">
                  <table class="min-w-full text-left text-sm">
                    <thead class="bg-slate-50 text-slate-500 dark:bg-slate-900/70 dark:text-slate-400">
                      <tr>
                        <th class="px-5 py-3 font-semibold">{{ t('binanceMarket.columns.asset') }}</th>
                        <th class="px-5 py-3 font-semibold">
                          <button
                            type="button"
                            @click="toggleSpotSort('price_change_pct')"
                            class="inline-flex items-center gap-2 transition"
                            :class="spotSort.field === 'price_change_pct' ? 'text-slate-900 dark:text-white' : 'hover:text-slate-700 dark:hover:text-slate-200'"
                          >
                            <span>{{ t('binanceMarket.columns.change24hShort') }}</span>
                            <span class="text-xs">{{ sortDirectionIcon(spotSort.field === 'price_change_pct', spotSort.direction) }}</span>
                          </button>
                        </th>
                        <th class="px-5 py-3 font-semibold">{{ t('binanceMarket.columns.price') }}</th>
                        <th class="px-5 py-3 font-semibold">
                          <button
                            type="button"
                            @click="toggleSpotSort('quote_volume')"
                            class="inline-flex items-center gap-2 transition"
                            :class="spotSort.field === 'quote_volume' ? 'text-slate-900 dark:text-white' : 'hover:text-slate-700 dark:hover:text-slate-200'"
                          >
                            <span>{{ t('binanceMarket.columns.quoteVolume') }}</span>
                            <span class="text-xs">{{ sortDirectionIcon(spotSort.field === 'quote_volume', spotSort.direction) }}</span>
                          </button>
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="item in spotRows" :key="item.symbol" class="border-t border-slate-100 transition hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-700/50">
                        <td class="px-5 py-4 font-medium text-slate-900 dark:text-white">
                          <button
                            type="button"
                            class="rounded-full px-2 py-1 transition hover:bg-cyan-50 hover:text-cyan-700 dark:hover:bg-cyan-500/10 dark:hover:text-cyan-300"
                            @click="openChart({ ...item, market: 'spot' })"
                          >
                            {{ displaySymbol(item.symbol) }}
                          </button>
                        </td>
                        <td class="px-5 py-4" :class="valueTone(item.price_change_pct)">{{ formatSigned(item.price_change_pct) }}</td>
                        <td class="px-5 py-4 text-slate-600 dark:text-slate-300">{{ formatPrice(item.last_price) }}</td>
                        <td class="px-5 py-4 text-slate-600 dark:text-slate-300">{{ formatCompact(item.quote_volume) }}</td>
                      </tr>
                      <tr v-if="!spotRows.length">
                        <td colspan="4" class="px-5 py-8 text-center text-sm text-slate-400 dark:text-slate-500">{{ t('binanceMarket.tables.noSpotRows') }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </article>

            </div>
          </section>
        </div>

        <div class="space-y-6">
          <section class="space-y-4">
            <section class="grid grid-cols-2 gap-3 lg:grid-cols-4">
              <article
                v-for="card in summaryCards"
                :key="card.label"
                class="rounded-[20px] border border-slate-200/70 bg-white/85 p-3 shadow-sm backdrop-blur dark:border-slate-700 dark:bg-slate-800/85"
              >
                <div class="flex items-center justify-between">
                  <p class="text-[10px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">{{ card.label }}</p>
                  <p class="text-[10px] text-slate-400 dark:text-slate-500">{{ card.hint }}</p>
                </div>
                <p class="mt-1 text-2xl font-bold text-slate-900 dark:text-white">{{ card.value }}</p>
              </article>
            </section>

            <section v-if="error" class="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-600 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-300">
              {{ error }}
            </section>

            <div class="flex flex-col gap-3 rounded-[30px] border border-slate-200/70 bg-white/90 p-4 shadow-sm dark:border-slate-700 dark:bg-slate-800/90">
              <div class="flex flex-col gap-4 px-2 xl:flex-row xl:items-center xl:justify-between">
                <div class="flex flex-wrap items-baseline gap-3">
                  <h2 class="text-xl font-bold text-slate-900 dark:text-white">{{ t('binanceMarket.tables.monitor') }}</h2>
                  <span class="rounded bg-slate-900 px-2 py-0.5 text-xs font-semibold text-white dark:bg-cyan-500 dark:text-slate-950">{{ monitor.quote_asset }}</span>
                  <span class="text-xs text-slate-500 dark:text-slate-400">{{ t('binanceMarket.updatedAt', { time: formatTime(monitor.updated_at) }) }}</span>
                </div>

                <label class="flex w-fit items-center gap-2 rounded-xl bg-slate-50 px-3 py-1.5 text-sm ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-700">
                  <span class="text-slate-500 dark:text-slate-400">{{ t('binanceMarket.minRisePct') }}</span>
                  <input v-model.number="minRisePct" type="number" min="1" max="30" step="0.5" class="w-14 bg-transparent text-center font-semibold text-slate-900 outline-none dark:text-white" />
                </label>
              </div>
              <div class="flex flex-wrap items-center gap-3">
                <div class="flex flex-wrap gap-2 rounded-full border border-slate-200 bg-slate-50 p-1 dark:border-slate-700 dark:bg-slate-900">
                  <button
                    v-for="item in [
                      { key: 'focus', label: t('binanceMarket.filters.focus') },
                      { key: 'momentum', label: t('binanceMarket.filters.momentum') },
                      { key: 'natural', label: t('binanceMarket.filters.natural') },
                      { key: 'all', label: t('binanceMarket.filters.all') },
                    ]"
                    :key="item.key"
                    @click="mode = item.key"
                    class="rounded-full px-4 py-2 text-sm transition"
                    :class="mode === item.key ? 'bg-slate-900 text-white dark:bg-cyan-600' : 'text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white'"
                  >
                    {{ item.label }}
                  </button>
                </div>

                <div class="flex flex-wrap gap-2 rounded-full border border-slate-200 bg-slate-50 p-1 dark:border-slate-700 dark:bg-slate-900">
                  <button
                    v-for="item in [
                      { key: 'all', label: t('binanceMarket.market.all') },
                      { key: 'spot', label: t('binanceMarket.market.spot') },
                      { key: 'usdm', label: t('binanceMarket.market.usdm') },
                    ]"
                    :key="item.key"
                    @click="marketFilter = item.key"
                    class="rounded-full px-4 py-2 text-sm transition"
                    :class="marketFilter === item.key ? 'bg-cyan-500 text-slate-950' : 'text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white'"
                  >
                    {{ item.label }}
                  </button>
                </div>
              </div>
            </div>

            <div>
              <article class="overflow-hidden rounded-[30px] border border-slate-200/70 bg-white/90 shadow-sm dark:border-slate-700 dark:bg-slate-800/90">
                <div class="flex items-center justify-between border-b border-slate-200 px-5 py-4 dark:border-slate-700">
                  <div>
                    <h4 class="text-lg font-semibold text-slate-900 dark:text-white">{{ t('binanceMarket.tables.monitorList') }}</h4>
                    <p class="text-sm text-slate-500 dark:text-slate-400">{{ t('binanceMarket.resultCount', { count: filteredItems.length }) }}</p>
                  </div>
                </div>

                <div class="overflow-x-auto">
                  <table class="min-w-full text-left text-sm">
                    <thead class="bg-slate-50 text-slate-500 dark:bg-slate-900/70 dark:text-slate-400">
                      <tr>
                        <th class="px-5 py-3 font-semibold">{{ t('binanceMarket.columns.asset') }}</th>
                        <th class="px-4 py-3 font-semibold">{{ t('binanceMarket.columns.today') }}</th>
                        <th class="px-4 py-3 font-semibold">15m</th>
                        <th class="px-4 py-3 font-semibold">1h</th>
                        <th class="px-4 py-3 font-semibold">{{ t('binanceMarket.columns.naturalScore') }}</th>
                        <th class="px-4 py-3 font-semibold">{{ t('binanceMarket.columns.momentumScore') }}</th>
                        <th class="px-5 py-3 font-semibold">{{ t('binanceMarket.columns.status') }}</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr
                        v-for="item in filteredItems"
                        :key="`${item.market}-${item.symbol}`"
                        class="cursor-pointer border-t border-slate-100 transition hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-700/50"
                        :class="chartDialog.open && detailKey === toItemKey(item) ? 'bg-cyan-50/80 dark:bg-cyan-500/10' : ''"
                        @click="openMonitorDetail(item)"
                      >
                        <td class="px-5 py-4">
                          <div class="flex items-center gap-3">
                            <span class="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-600 dark:bg-slate-900 dark:text-slate-300">{{ formatMarketLabel(item) }}</span>
                            <div>
                              <button
                                type="button"
                                class="font-semibold text-slate-900 transition hover:text-cyan-700 dark:text-white dark:hover:text-cyan-300"
                                @click.stop="openMonitorDetail(item)"
                              >
                                {{ displaySymbol(item.symbol) }}
                              </button>
                              <div class="text-xs text-slate-500 dark:text-slate-400">{{ formatPrice(item.mark_price ?? item.last_price) }}</div>
                            </div>
                          </div>
                        </td>
                        <td class="px-4 py-4 font-medium" :class="valueTone(item.price_change_pct)">{{ formatSigned(item.price_change_pct) }}</td>
                        <td class="px-4 py-4" :class="valueTone(item.change_15m_pct)">{{ formatSigned(item.change_15m_pct) }}</td>
                        <td class="px-4 py-4" :class="valueTone(item.change_1h_pct)">{{ formatSigned(item.change_1h_pct) }}</td>
                        <td class="px-4 py-4 text-slate-700 dark:text-slate-300">{{ formatScore(item.natural_score) }}</td>
                        <td class="px-4 py-4 text-slate-700 dark:text-slate-300">{{ formatScore(item.momentum_score) }}</td>
                        <td class="px-5 py-4">
                          <span class="inline-flex rounded-full px-3 py-1 text-xs font-semibold ring-1" :class="verdictTone(item.verdict)">
                            {{ formatVerdict(item.verdict) }}
                          </span>
                        </td>
                      </tr>
                      <tr v-if="!filteredItems.length">
                        <td colspan="7" class="px-5 py-10 text-center text-sm text-slate-500 dark:text-slate-400">
                          {{ t('binanceMarket.tables.noMonitorRows') }}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </article>

            </div>
          </section>
        </div>
      </section>
    </div>

    <BinanceSymbolChartDialog
      :open="chartDialog.open"
      :market-label="chartMarketLabel"
      :title="chartTitle"
      :symbol="chartSymbol"
      :timeframe="chartTimeframe"
      :timeframes="chartTimeframes"
      :chart-colors="chartColors"
      :chart-data="chartData"
      :volume-data="volumeData"
      :loading-more="chartLoadingMore"
      :monitor-item="detailItem"
      :format-score="formatScore"
      :format-signed="formatSigned"
      :format-compact="formatCompact"
      :value-tone="valueTone"
      :verdict-tone="verdictTone"
      :format-verdict="formatVerdict"
      :format-follow-status="formatFollowStatus"
      :format-reason="formatReason"
      @close="closeChart"
      @load-more="loadMoreChartHistory"
      @update:timeframe="chartTimeframe = $event"
    />
  </div>
</template>

<script setup lang="ts">
defineOptions({ name: 'BinanceMarket' })

import BinanceSymbolChartDialog from '@/components/market/BinanceSymbolChartDialog.vue'
import { useBinanceMarketPage } from '@/modules/market'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const {
  loading,
  error,
  minRisePct,
  mode,
  marketFilter,
  autoRefresh,
  monitor,
  spotRows,
  spotSort,
  contractRows,
  contractSort,
  filteredItems,
  detailKey,
  detailItem,
  chartDialog,
  chartSymbol,
  chartTitle,
  chartMarketLabel,
  chartTimeframe,
  chartTimeframes,
  chartColors,
  chartData,
  volumeData,
  chartLoadingMore,
  openChart,
  closeChart,
  openMonitorDetail,
  loadMoreChartHistory,
  summaryCards,
  fetchData,
  toggleSpotSort,
  toggleContractSort,
  formatSigned,
  formatScore,
  formatTime,
  formatPrice,
  formatCompact,
  displaySymbol,
  formatMarketLabel,
  formatVerdict,
  formatFollowStatus,
  formatReason,
  sortDirectionIcon,
  valueTone,
  verdictTone,
  toItemKey,
} = useBinanceMarketPage()
</script>
