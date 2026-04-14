<template>
  <div class="h-full overflow-y-auto bg-slate-50 dark:bg-slate-900 transition-colors">
    <div class="mx-auto max-w-7xl p-6 space-y-6">
      <section class="rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800/90">
        <div class="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.3em] text-cyan-600 dark:text-cyan-400">Binance Web3</p>
            <h2 class="mt-2 text-3xl font-semibold text-slate-900 dark:text-white">Web3 榜单</h2>
            <p class="mt-3 text-sm text-slate-600 dark:text-slate-300">社交热度、热门币、聪明钱流入、Meme 榜和地址收益榜。</p>
          </div>

          <div class="flex flex-wrap items-end gap-4">
            <div class="w-40">
              <label class="mb-1 block text-xs font-bold uppercase tracking-wide text-slate-500 dark:text-slate-400">Chain</label>
              <select v-model="chainId" class="w-full rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700 outline-none dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100">
                <option v-for="item in chainOptions" :key="item.value" :value="item.value">{{ item.label }}</option>
              </select>
            </div>

            <div>
              <label class="mb-1 block text-xs font-bold uppercase tracking-wide text-slate-500 dark:text-slate-400">Unified</label>
              <div class="flex rounded-2xl bg-slate-100 p-1 dark:bg-slate-900">
                <button
                  v-for="item in unifiedOptions"
                  :key="item.value"
                  @click="rankType = item.value"
                  :class="[
                    'rounded-xl px-4 py-2 text-sm font-semibold transition',
                    rankType === item.value
                      ? 'bg-cyan-600 text-white shadow-sm'
                      : 'text-slate-500 hover:bg-white hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white'
                  ]"
                >
                  {{ item.label }}
                </button>
              </div>
            </div>
          </div>
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
            <h3 class="text-lg font-semibold text-slate-900 dark:text-white">Social Hype</h3>
          </div>
          <div class="overflow-x-auto">
            <table class="min-w-full text-left text-sm">
              <thead class="bg-slate-50 text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
                <tr>
                  <th class="px-5 py-3 font-semibold">Token</th>
                  <th class="px-5 py-3 font-semibold">Sentiment</th>
                  <th class="px-5 py-3 font-semibold">24H</th>
                  <th class="px-5 py-3 font-semibold">Market Cap</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in socialHype.slice(0, 10)" :key="`${item.chain_id}-${item.contract_address}`" class="border-t border-slate-100 dark:border-slate-700">
                  <td class="px-5 py-4 font-medium text-slate-900 dark:text-white">{{ item.symbol }}</td>
                  <td class="px-5 py-4 text-slate-600 dark:text-slate-300">{{ item.sentiment || '--' }}</td>
                  <td class="px-5 py-4" :class="changeClass(item.price_change_pct)">{{ formatPercent(item.price_change_pct) }}</td>
                  <td class="px-5 py-4 text-slate-600 dark:text-slate-300">{{ formatCompact(item.market_cap) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </article>

        <article class="rounded-3xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
          <div class="border-b border-slate-200 px-5 py-4 dark:border-slate-700">
            <h3 class="text-lg font-semibold text-slate-900 dark:text-white">Unified Rank</h3>
          </div>
          <div class="overflow-x-auto">
            <table class="min-w-full text-left text-sm">
              <thead class="bg-slate-50 text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
                <tr>
                  <th class="px-5 py-3 font-semibold">Token</th>
                  <th class="px-5 py-3 font-semibold">24H</th>
                  <th class="px-5 py-3 font-semibold">Volume</th>
                  <th class="px-5 py-3 font-semibold">Holders</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in unifiedRank.slice(0, 10)" :key="`${item.chain_id}-${item.contract_address}`" class="border-t border-slate-100 dark:border-slate-700">
                  <td class="px-5 py-4 font-medium text-slate-900 dark:text-white">{{ item.symbol }}</td>
                  <td class="px-5 py-4" :class="changeClass(item.percent_change_24h)">{{ formatPercent(item.percent_change_24h) }}</td>
                  <td class="px-5 py-4 text-slate-600 dark:text-slate-300">{{ formatCompact(item.volume_24h) }}</td>
                  <td class="px-5 py-4 text-slate-600 dark:text-slate-300">{{ formatCompact(item.holders) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </article>
      </section>

      <section class="grid gap-6 xl:grid-cols-2">
        <article class="rounded-3xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
          <div class="border-b border-slate-200 px-5 py-4 dark:border-slate-700">
            <h3 class="text-lg font-semibold text-slate-900 dark:text-white">Smart Money Inflow</h3>
          </div>
          <div class="overflow-x-auto">
            <table class="min-w-full text-left text-sm">
              <thead class="bg-slate-50 text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
                <tr>
                  <th class="px-5 py-3 font-semibold">Token</th>
                  <th class="px-5 py-3 font-semibold">Inflow</th>
                  <th class="px-5 py-3 font-semibold">Traders</th>
                  <th class="px-5 py-3 font-semibold">Risk</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in smartMoney.slice(0, 10)" :key="`${item.chain_id}-${item.contract_address}`" class="border-t border-slate-100 dark:border-slate-700">
                  <td class="px-5 py-4 font-medium text-slate-900 dark:text-white">{{ item.symbol }}</td>
                  <td class="px-5 py-4 text-cyan-500">{{ formatCompact(item.inflow) }}</td>
                  <td class="px-5 py-4 text-slate-600 dark:text-slate-300">{{ item.traders ?? '--' }}</td>
                  <td class="px-5 py-4 text-slate-600 dark:text-slate-300">{{ item.risk_level ?? '--' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </article>

        <article class="rounded-3xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
          <div class="border-b border-slate-200 px-5 py-4 dark:border-slate-700">
            <h3 class="text-lg font-semibold text-slate-900 dark:text-white">Meme Rank</h3>
          </div>
          <div class="overflow-x-auto">
            <table class="min-w-full text-left text-sm">
              <thead class="bg-slate-50 text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
                <tr>
                  <th class="px-5 py-3 font-semibold">Rank</th>
                  <th class="px-5 py-3 font-semibold">Token</th>
                  <th class="px-5 py-3 font-semibold">Score</th>
                  <th class="px-5 py-3 font-semibold">24H</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in memeRank.slice(0, 10)" :key="`${item.chain_id}-${item.contract_address}`" class="border-t border-slate-100 dark:border-slate-700">
                  <td class="px-5 py-4 text-slate-600 dark:text-slate-300">{{ item.rank ?? '--' }}</td>
                  <td class="px-5 py-4 font-medium text-slate-900 dark:text-white">{{ item.symbol }}</td>
                  <td class="px-5 py-4 text-slate-600 dark:text-slate-300">{{ item.score ?? '--' }}</td>
                  <td class="px-5 py-4" :class="changeClass(item.price_change_pct)">{{ formatPercent(item.price_change_pct) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </article>
      </section>

      <article class="rounded-3xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
        <div class="border-b border-slate-200 px-5 py-4 dark:border-slate-700">
          <h3 class="text-lg font-semibold text-slate-900 dark:text-white">Address PnL</h3>
        </div>
        <div class="overflow-x-auto">
          <table class="min-w-full text-left text-sm">
            <thead class="bg-slate-50 text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
              <tr>
                <th class="px-5 py-3 font-semibold">Address</th>
                <th class="px-5 py-3 font-semibold">PnL</th>
                <th class="px-5 py-3 font-semibold">Win Rate</th>
                <th class="px-5 py-3 font-semibold">Volume</th>
                <th class="px-5 py-3 font-semibold">Trades</th>
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
  </div>
</template>

<script setup>
defineOptions({ name: 'Web3MarketRank' })

import { useWeb3MarketRankPage } from '@/modules/market'

const {
  error,
  chainId,
  rankType,
  chainOptions,
  unifiedOptions,
  socialHype,
  unifiedRank,
  smartMoney,
  memeRank,
  addressPnl,
  summaryCards,
  formatPercent,
  formatCompact,
  changeClass,
} = useWeb3MarketRankPage()
</script>
