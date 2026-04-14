<template>
  <div class="h-full overflow-y-auto bg-slate-50 dark:bg-slate-900 transition-colors">
    <div class="mx-auto max-w-7xl p-6 space-y-6">
      <section class="rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800/90">
        <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.3em] text-cyan-600 dark:text-cyan-400">Binance Web3</p>
            <h2 class="mt-2 text-3xl font-semibold text-slate-900 dark:text-white">Token 研究占位</h2>
            <p class="mt-3 text-sm text-slate-600 dark:text-slate-300">Token 信息和安全审计接口先保留契约。</p>
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

      <section v-if="error" class="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-600 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-300">
        {{ error }}
      </section>

      <section class="grid gap-6 xl:grid-cols-[1.4fr_1fr]">
        <article class="rounded-3xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
          <div class="border-b border-slate-200 px-5 py-4 dark:border-slate-700">
            <h3 class="text-lg font-semibold text-slate-900 dark:text-white">Token Info</h3>
          </div>
          <div class="divide-y divide-slate-100 dark:divide-slate-700">
            <div v-for="item in tokenInfoFeatures" :key="item.feature" class="p-5">
              <div class="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p class="text-base font-semibold text-slate-900 dark:text-white">{{ item.feature }}</p>
                  <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">{{ item.skill_name }} {{ item.skill_version }}</p>
                </div>
                <span class="rounded-full bg-cyan-50 px-3 py-1 text-xs font-semibold uppercase text-cyan-700 dark:bg-cyan-500/10 dark:text-cyan-300">{{ item.status }}</span>
              </div>
              <div class="mt-4 overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-700">
                <table class="min-w-full text-left text-xs">
                  <thead class="bg-slate-50 text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
                    <tr>
                      <th class="px-4 py-3 font-semibold">Method</th>
                      <th class="px-4 py-3 font-semibold">Params</th>
                      <th class="px-4 py-3 font-semibold">Fields</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="endpoint in item.reserved_endpoints" :key="endpoint.url" class="border-t border-slate-100 dark:border-slate-700">
                      <td class="px-4 py-3 font-medium text-slate-900 dark:text-white">{{ endpoint.method }}</td>
                      <td class="px-4 py-3 text-slate-600 dark:text-slate-300">{{ endpoint.params?.join(', ') }}</td>
                      <td class="px-4 py-3 text-slate-600 dark:text-slate-300">{{ item.response_fields.slice(0, 8).join(', ') }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </article>

        <div class="space-y-6">
          <article class="rounded-3xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
            <div class="border-b border-slate-200 px-5 py-4 dark:border-slate-700">
              <h3 class="text-lg font-semibold text-slate-900 dark:text-white">支持链</h3>
            </div>
            <div class="grid grid-cols-2 gap-3 p-5">
              <div v-for="chain in features[0]?.supported_chains || []" :key="chain.chain_id" class="rounded-2xl bg-slate-50 p-4 dark:bg-slate-900">
                <p class="text-sm font-semibold text-slate-900 dark:text-white">{{ chain.name }}</p>
                <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">{{ chain.chain_id }} {{ chain.platform || '' }}</p>
              </div>
            </div>
          </article>

          <article class="rounded-3xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
            <div class="border-b border-slate-200 px-5 py-4 dark:border-slate-700">
              <h3 class="text-lg font-semibold text-slate-900 dark:text-white">Token Audit</h3>
            </div>
            <div v-for="item in auditFeatures" :key="item.feature" class="p-5">
              <div class="flex items-center justify-between gap-3">
                <div>
                  <p class="text-base font-semibold text-slate-900 dark:text-white">{{ item.feature }}</p>
                  <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">{{ item.skill_name }} {{ item.skill_version }}</p>
                </div>
                <span class="rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold uppercase text-amber-700 dark:bg-amber-500/10 dark:text-amber-300">{{ item.status }}</span>
              </div>
              <div class="mt-4 space-y-2">
                <p v-for="note in item.notes.slice(2, 6)" :key="note" class="text-sm text-slate-600 dark:text-slate-300">{{ note }}</p>
              </div>
            </div>
          </article>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
defineOptions({ name: 'BinanceTokenResearch' })

import { useBinanceTokenResearchPage } from '@/modules/market'

const {
  loading,
  error,
  features,
  tokenInfoFeatures,
  auditFeatures,
  fetchData,
} = useBinanceTokenResearchPage()
</script>
