<template>
  <div class="h-full overflow-y-auto bg-slate-50 dark:bg-slate-900 transition-colors">
    <div class="mx-auto max-w-7xl p-6 space-y-6">
      <section class="rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800/90">
        <div class="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.3em] text-cyan-600 dark:text-cyan-400">{{ t('web3Rank.eyebrow') }}</p>
            <h2 class="mt-2 text-3xl font-semibold text-slate-900 dark:text-white">{{ t('web3Rank.title') }}</h2>
            <p class="mt-3 text-sm text-slate-600 dark:text-slate-300">{{ t('web3Rank.subtitle') }}</p>
          </div>

          <div class="flex flex-wrap items-end gap-4">
            <div class="w-40">
              <label class="mb-1 block text-xs font-bold uppercase tracking-wide text-slate-500 dark:text-slate-400">{{ t('web3Rank.chain') }}</label>
              <select v-model="chainId" class="w-full rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700 outline-none dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100">
                <option v-for="item in chainOptions" :key="item.value" :value="item.value">{{ item.label }}</option>
              </select>
            </div>
          </div>
        </div>
      </section>

      <section v-if="error" class="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-600 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-300">
        {{ error }}
      </section>

      <article class="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
        <div class="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 px-5 py-4 dark:border-slate-700">
          <div>
            <h3 class="text-lg font-semibold text-slate-900 dark:text-white">{{ t('web3Rank.heatRank.title') }}</h3>
            <p class="text-sm text-slate-500 dark:text-slate-400">{{ t('web3Rank.heatRank.subtitle') }}</p>
          </div>
          <button
            type="button"
            class="rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-800 disabled:opacity-50 dark:bg-cyan-600 dark:hover:bg-cyan-500"
            :disabled="web3Loading"
            @click="fetchWeb3HeatRank"
          >
            {{ web3Loading ? t('web3Rank.refreshing') : t('web3Rank.refresh') }}
          </button>
        </div>
        <div v-if="web3Error" class="border-b border-rose-100 bg-rose-50 px-5 py-3 text-sm text-rose-600 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-300">{{ web3Error }}</div>
        <div class="overflow-x-auto">
          <table class="min-w-full text-left text-sm">
            <thead class="bg-slate-50 text-slate-500 dark:bg-slate-900/70 dark:text-slate-400">
              <tr>
                <th class="px-5 py-3 font-semibold">{{ t('web3Rank.columns.rank') }}</th>
                <th class="px-5 py-3 font-semibold">{{ t('web3Rank.columns.token') }}</th>
                <th class="px-5 py-3 font-semibold">{{ t('web3Rank.columns.heat') }}</th>
                <th class="px-5 py-3 font-semibold">{{ t('web3Rank.columns.signal') }}</th>
                <th class="px-5 py-3 font-semibold">
                  <button
                    type="button"
                    @click="toggleWeb3Sort('percent_change_24h')"
                    class="inline-flex items-center gap-2 transition"
                    :class="web3Sort.field === 'percent_change_24h' ? 'text-slate-900 dark:text-white' : 'hover:text-slate-700 dark:hover:text-slate-200'"
                  >
                    <span>{{ t('web3Rank.columns.change24h') }}</span>
                    <span class="text-xs">{{ sortDirectionIcon(web3Sort.field === 'percent_change_24h', web3Sort.direction) }}</span>
                  </button>
                </th>
                <th class="px-5 py-3 font-semibold">
                  <button
                    type="button"
                    @click="toggleWeb3Sort('market_cap')"
                    class="inline-flex items-center gap-2 transition"
                    :class="web3Sort.field === 'market_cap' ? 'text-slate-900 dark:text-white' : 'hover:text-slate-700 dark:hover:text-slate-200'"
                  >
                    <span>{{ t('web3Rank.columns.marketCap') }}</span>
                    <span class="text-xs">{{ sortDirectionIcon(web3Sort.field === 'market_cap', web3Sort.direction) }}</span>
                  </button>
                </th>
                <th class="px-5 py-3 font-semibold">
                  <button
                    type="button"
                    @click="toggleWeb3Sort('liquidity')"
                    class="inline-flex items-center gap-2 transition"
                    :class="web3Sort.field === 'liquidity' ? 'text-slate-900 dark:text-white' : 'hover:text-slate-700 dark:hover:text-slate-200'"
                  >
                    <span>{{ t('web3Rank.columns.liquidity') }}</span>
                    <span class="text-xs">{{ sortDirectionIcon(web3Sort.field === 'liquidity', web3Sort.direction) }}</span>
                  </button>
                </th>
                <th class="px-5 py-3 font-semibold">{{ t('web3Rank.columns.smartMoney') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="item in web3HeatRank"
                :key="`${item.chain_id}-${item.contract_address}`"
                class="cursor-pointer border-t border-slate-100 transition hover:bg-cyan-50/70 dark:border-slate-700 dark:hover:bg-cyan-500/10"
                @click="openWeb3Token(item)"
              >
                <td class="px-5 py-4 text-slate-500 dark:text-slate-400">{{ item.rank ?? '--' }}</td>
                <td class="px-5 py-4">
                  <div class="flex items-center gap-3">
                    <Web3TokenIcon :src="item.icon_url" :symbol="item.symbol" />
                    <div>
                      <button type="button" class="font-semibold text-slate-900 transition hover:text-cyan-700 dark:text-white dark:hover:text-cyan-300">
                        {{ item.symbol || '--' }}
                      </button>
                      <div class="max-w-[160px] truncate text-xs text-slate-400 dark:text-slate-500">{{ item.contract_address }}</div>
                    </div>
                  </div>
                </td>
                <td class="px-5 py-4 font-semibold text-cyan-700 dark:text-cyan-300">{{ formatScore(item.heat_score) }}</td>
                <td class="px-5 py-4">
                  <div class="flex flex-wrap gap-1.5 text-xs">
                    <span v-if="item.ranks?.top_search" class="rounded-full bg-slate-100 px-2 py-1 text-slate-600 dark:bg-slate-900 dark:text-slate-300">{{ t('web3Rank.signals.search') }} #{{ item.ranks.top_search }}</span>
                    <span v-if="item.ranks?.trending" class="rounded-full bg-slate-100 px-2 py-1 text-slate-600 dark:bg-slate-900 dark:text-slate-300">{{ t('web3Rank.signals.trending') }} #{{ item.ranks.trending }}</span>
                    <span v-if="item.metrics?.social_hype" class="rounded-full bg-violet-500/10 px-2 py-1 text-violet-600 dark:text-violet-300">{{ t('web3Rank.signals.social') }} {{ formatCompact(item.metrics.social_hype) }}</span>
                    <span v-if="item.metrics?.smart_money_inflow" class="rounded-full bg-cyan-500/10 px-2 py-1 text-cyan-600 dark:text-cyan-300">{{ t('web3Rank.signals.smartMoney') }} {{ formatCompact(item.metrics.smart_money_inflow) }}</span>
                    <span v-if="item.ranks?.meme" class="rounded-full bg-amber-500/10 px-2 py-1 text-amber-600 dark:text-amber-300">Meme #{{ item.ranks.meme }}</span>
                  </div>
                </td>
                <td class="px-5 py-4" :class="changeClass(item.metrics?.percent_change_24h)">{{ formatPercent(item.metrics?.percent_change_24h) }}</td>
                <td class="px-5 py-4 text-slate-600 dark:text-slate-300">{{ formatCompact(item.metrics?.market_cap) }}</td>
                <td class="px-5 py-4 text-slate-600 dark:text-slate-300">{{ formatCompact(item.metrics?.liquidity) }}</td>
                <td class="px-5 py-4 text-slate-600 dark:text-slate-300">{{ formatCompact(item.metrics?.smart_money_inflow) }}</td>
              </tr>
              <tr v-if="!web3HeatRank.length">
                <td colspan="8" class="px-5 py-8 text-center text-sm text-slate-400 dark:text-slate-500">{{ t('web3Rank.heatRank.noRows') }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </article>

      <article class="rounded-3xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
        <div class="border-b border-slate-200 px-5 py-4 dark:border-slate-700">
          <h3 class="text-lg font-semibold text-slate-900 dark:text-white">{{ t('web3Rank.addressPnlTitle') }}</h3>
        </div>
        <div class="overflow-x-auto">
          <table class="min-w-full text-left text-sm">
            <thead class="bg-slate-50 text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
              <tr>
                <th class="px-5 py-3 font-semibold">{{ t('web3Rank.columns.address') }}</th>
                <th class="px-5 py-3 font-semibold">{{ t('web3Rank.columns.pnl') }}</th>
                <th class="px-5 py-3 font-semibold">{{ t('web3Rank.columns.winRate') }}</th>
                <th class="px-5 py-3 font-semibold">{{ t('web3Rank.columns.volume') }}</th>
                <th class="px-5 py-3 font-semibold">{{ t('web3Rank.columns.trades') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in addressPnl" :key="item.address" class="border-t border-slate-100 dark:border-slate-700">
                <td class="px-5 py-4 font-medium text-slate-900 dark:text-white">{{ item.address_label || item.address }}</td>
                <td class="px-5 py-4" :class="changeClass(item.realized_pnl)">{{ formatCompact(item.realized_pnl) }}</td>
                <td class="px-5 py-4 text-slate-600 dark:text-slate-300">{{ formatPercent(item.win_rate) }}</td>
                <td class="px-5 py-4 text-slate-600 dark:text-slate-300">{{ formatCompact(item.total_volume) }}</td>
                <td class="px-5 py-4 text-slate-600 dark:text-slate-300">{{ item.total_tx_cnt ?? '--' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </article>
    </div>

    <BinanceWeb3TokenDialog
      :open="web3Dialog.open"
      :token="web3Dialog.token"
      :interval="web3KlineInterval"
      :intervals="web3KlineIntervals"
      :detail-loading="web3DetailLoading"
      :detail-error="web3DetailError"
      :dynamic="web3Dynamic"
      :audit="web3Audit"
      :chart-data="web3ChartData"
      :volume-data="web3VolumeData"
      :chart-colors="web3ChartColors"
      :format-score="formatScore"
      :format-price="formatPrice"
      :format-signed="formatPercent"
      :format-compact="formatCompact"
      :value-tone="changeClass"
      @close="closeWeb3Token"
      @update:interval="web3KlineInterval = $event"
    />
  </div>
</template>

<script setup lang="ts">
defineOptions({ name: 'Web3MarketRank' })

import { useWeb3MarketRankPage } from '@/modules/market'
import BinanceWeb3TokenDialog from '@/components/market/BinanceWeb3TokenDialog.vue'
import Web3TokenIcon from '@/components/market/Web3TokenIcon.vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const {
  error,
  chainId,
  chainOptions,
  addressPnl,
  web3HeatRank,
  web3Loading,
  web3Error,
  web3Dialog,
  web3Dynamic,
  web3Audit,
  web3DetailLoading,
  web3DetailError,
  web3KlineInterval,
  web3KlineIntervals,
  web3ChartData,
  web3VolumeData,
  web3ChartColors,
  web3Sort,
  fetchWeb3HeatRank,
  toggleWeb3Sort,
  openWeb3Token,
  closeWeb3Token,
  formatScore,
  formatPercent,
  formatPrice,
  formatCompact,
  sortDirectionIcon,
  changeClass,
} = useWeb3MarketRankPage()
</script>
