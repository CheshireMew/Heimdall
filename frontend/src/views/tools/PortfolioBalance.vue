<template>
  <div class="h-full p-6">
    <div class="grid gap-6 xl:grid-cols-[20rem_minmax(0,1fr)]">
      <aside class="space-y-6">
        <section class="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-800">
          <div class="flex items-start justify-between gap-3">
            <div>
              <div class="text-xs font-semibold uppercase tracking-[0.24em] text-sky-600 dark:text-sky-300">
                {{ $t('portfolioBalance.eyebrow') }}
              </div>
              <h1 class="mt-2 text-2xl font-semibold text-slate-900 dark:text-white">
                {{ $t('portfolioBalance.title') }}
              </h1>
            </div>
            <button
              type="button"
              class="inline-flex h-11 w-11 items-center justify-center rounded-2xl border border-sky-200 bg-sky-50 text-sky-700 transition hover:bg-sky-100 dark:border-sky-800 dark:bg-sky-950/40 dark:text-sky-200 dark:hover:bg-sky-900/50"
              @click="createPortfolio"
            >
              <PlusIcon class="h-5 w-5" />
            </button>
          </div>

          <div class="mt-5 space-y-3">
            <div
              v-for="portfolio in portfolios"
              :key="portfolio.id"
              class="w-full rounded-2xl border px-4 py-4 text-left transition"
              :class="portfolio.id === activePortfolioId
                ? 'border-sky-300 bg-sky-50 dark:border-sky-700 dark:bg-sky-950/30'
                : 'border-slate-200 bg-slate-50 hover:border-slate-300 dark:border-slate-700 dark:bg-slate-900/60 dark:hover:border-slate-600'"
            >
              <div class="flex items-start justify-between gap-3">
                <button type="button" class="min-w-0 flex-1 text-left" @click="selectPortfolio(portfolio.id)">
                  <div class="truncate text-base font-semibold text-slate-900 dark:text-white">{{ portfolio.name }}</div>
                </button>
                <button
                  type="button"
                  class="inline-flex h-8 w-8 items-center justify-center rounded-xl border border-transparent text-slate-400 transition hover:border-rose-200 hover:text-rose-600 dark:hover:border-rose-800 dark:hover:text-rose-300"
                  @click.stop="deletePortfolio(portfolio.id)"
                >
                  <TrashIcon class="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        </section>

        <section class="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-800">
          <h2 class="text-lg font-semibold text-slate-900 dark:text-white">{{ $t('portfolioBalance.strategyTitle') }}</h2>

          <div class="mt-4 space-y-3">
            <div class="rounded-2xl px-4 py-4" :class="strategyCardClass(plan.suggestedAction)">
              <div class="text-xs font-semibold uppercase tracking-wide">{{ $t('portfolioBalance.nextAction') }}</div>
              <div class="mt-2 text-lg font-semibold">{{ $t(`portfolioBalance.suggestedActions.${plan.suggestedAction}`) }}</div>
              <div class="mt-1 text-sm opacity-80">{{ $t(`portfolioBalance.reasons.${plan.suggestedReason}`) }}</div>
            </div>
            <div class="grid grid-cols-2 gap-3 text-sm">
              <div class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 dark:border-slate-700 dark:bg-slate-900/60">
                <div class="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">{{ $t('portfolioBalance.nextReviewDate') }}</div>
                <div class="mt-1 font-semibold text-slate-900 dark:text-white">{{ formatDate(plan.nextReviewDate) }}</div>
              </div>
              <div class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 dark:border-slate-700 dark:bg-slate-900/60">
                <div class="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">{{ $t('portfolioBalance.daysUntilReview') }}</div>
                <div class="mt-1 font-semibold text-slate-900 dark:text-white">{{ plan.daysUntilReview }}</div>
              </div>
            </div>
          </div>
        </section>
      </aside>

      <main v-if="activePortfolio" class="space-y-6">
        <section class="rounded-3xl border border-slate-200 bg-[radial-gradient(circle_at_top_left,_rgba(14,165,233,0.18),_transparent_42%),linear-gradient(135deg,_rgba(15,23,42,0.04),_rgba(14,165,233,0.08))] p-6 shadow-sm dark:border-slate-700 dark:bg-[radial-gradient(circle_at_top_left,_rgba(56,189,248,0.16),_transparent_36%),linear-gradient(135deg,_rgba(15,23,42,0.88),_rgba(8,47,73,0.78))]">
          <div class="grid gap-6 lg:grid-cols-[minmax(0,1fr)_26rem]">
            <div>
              <div class="grid gap-4 md:grid-cols-2">
                <label class="block">
                  <span class="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-300">{{ $t('portfolioBalance.portfolioName') }}</span>
                  <input v-model.trim="activePortfolio.name" type="text" class="w-full rounded-2xl border border-slate-300 bg-white/80 px-4 py-3 text-slate-900 outline-none transition focus:border-sky-500 dark:border-slate-600 dark:bg-slate-900/70 dark:text-white" />
                </label>
                <AppDateField
                  v-model="tracking.inceptionDate"
                  :label="$t('portfolioBalance.inceptionDate')"
                  input-class="w-full rounded-2xl border border-slate-300 bg-white/80 px-4 py-3 text-slate-900 outline-none transition focus:border-sky-500 dark:border-slate-600 dark:bg-slate-900/70 dark:text-white"
                  label-class="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-300"
                />
              </div>
            </div>

            <div class="grid grid-cols-2 gap-3">
              <div class="rounded-2xl border border-white/70 bg-white/80 p-4 backdrop-blur dark:border-white/10 dark:bg-slate-900/70">
                <div class="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">{{ $t('portfolioBalance.totalValue') }}</div>
                <div class="mt-2 text-2xl font-semibold text-slate-900 dark:text-white">{{ formatMoney(plan.totalValue) }}</div>
              </div>
              <div class="rounded-2xl border border-white/70 bg-white/80 p-4 backdrop-blur dark:border-white/10 dark:bg-slate-900/70">
                <div class="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">{{ $t('portfolioBalance.outOfBand') }}</div>
                <div class="mt-2 text-2xl font-semibold text-amber-600 dark:text-amber-300">{{ plan.outOfBandCount }}</div>
              </div>
              <div class="rounded-2xl border border-white/70 bg-white/80 p-4 backdrop-blur dark:border-white/10 dark:bg-slate-900/70">
                <div class="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">{{ $t('portfolioBalance.maxDrift') }}</div>
                <div class="mt-2 text-2xl font-semibold text-rose-600 dark:text-rose-300">{{ formatPercent(plan.maxDriftWeight) }}</div>
              </div>
              <div class="rounded-2xl border border-white/70 bg-white/80 p-4 backdrop-blur dark:border-white/10 dark:bg-slate-900/70">
                <div class="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
                  {{ activePortfolio.holdingsSource === 'paper' ? $t('portfolioBalance.holdingsModePaper') : $t('portfolioBalance.virtualCapital') }}
                </div>
                <div class="mt-2 text-2xl font-semibold text-emerald-600 dark:text-emerald-300">
                  {{ activePortfolio.holdingsSource === 'paper' ? $t('portfolioBalance.holdingsModePaperValue') : formatMoney(plan.trackingCapital) }}
                </div>
              </div>
            </div>
          </div>
        </section>

        <section class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800">
          <div class="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <h2 class="text-xl font-semibold text-slate-900 dark:text-white">{{ $t('portfolioBalance.configTitle') }}</h2>
            </div>
            <div class="flex flex-wrap gap-3">
              <button
                type="button"
                class="inline-flex items-center justify-center rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm font-medium text-emerald-700 transition hover:bg-emerald-100 disabled:cursor-not-allowed disabled:opacity-60 dark:border-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-200 dark:hover:bg-emerald-900/50"
                :disabled="importLoading"
                @click="importLatestPaperHoldings"
              >
                <ArrowDownTrayIcon class="mr-2 h-4 w-4" />
                {{ importLoading ? $t('portfolioBalance.importing') : $t('portfolioBalance.importPaperHoldings') }}
              </button>
              <button
                type="button"
                class="inline-flex items-center justify-center rounded-xl border border-sky-200 bg-sky-50 px-4 py-2 text-sm font-medium text-sky-700 transition hover:bg-sky-100 disabled:cursor-not-allowed disabled:opacity-60 dark:border-sky-800 dark:bg-sky-950/40 dark:text-sky-200 dark:hover:bg-sky-900/50"
                :disabled="marketLoading"
                @click="refreshMarketPrices"
              >
                <ArrowPathIcon class="mr-2 h-4 w-4" />
                {{ marketLoading ? $t('portfolioBalance.refreshing') : $t('portfolioBalance.refreshPrices') }}
              </button>
              <button
                type="button"
                class="inline-flex items-center justify-center rounded-xl border border-slate-200 bg-slate-50 px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-900/50 dark:text-slate-200 dark:hover:bg-slate-900"
                @click="addAsset"
              >
                <PlusIcon class="mr-2 h-4 w-4" />
                {{ $t('portfolioBalance.addAsset') }}
              </button>
            </div>
          </div>

          <div v-if="sourceMessage || sourceError || lastImportedRun" class="mt-4 space-y-2 text-sm">
            <div v-if="sourceMessage" class="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-emerald-800 dark:border-emerald-900/70 dark:bg-emerald-950/30 dark:text-emerald-200">
              {{ sourceMessage }}
            </div>
            <div v-if="sourceError" class="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-rose-800 dark:border-rose-900/70 dark:bg-rose-950/30 dark:text-rose-200">
              {{ sourceError }}
            </div>
            <div v-if="lastImportedRun" class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300">
              {{ $t('portfolioBalance.importSource', { id: lastImportedRun.id, updated: formatDateTime(lastImportedRun.metadata?.paper_live?.last_updated || lastImportedRun.created_at) }) }}
            </div>
          </div>

          <div class="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <label class="block">
              <span class="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">{{ $t('portfolioBalance.reviewFrequency') }}</span>
              <select v-model="strategy.reviewFrequency" class="w-full rounded-xl border border-slate-300 bg-slate-50 px-4 py-3 text-slate-900 outline-none transition focus:border-sky-500 dark:border-slate-600 dark:bg-slate-900 dark:text-white">
                <option value="daily">{{ $t('portfolioBalance.frequencies.daily') }}</option>
                <option value="weekly">{{ $t('portfolioBalance.frequencies.weekly') }}</option>
                <option value="monthly">{{ $t('portfolioBalance.frequencies.monthly') }}</option>
                <option value="quarterly">{{ $t('portfolioBalance.frequencies.quarterly') }}</option>
              </select>
            </label>
            <label class="block">
              <span class="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">{{ $t('portfolioBalance.virtualCapital') }}</span>
              <input v-model.number="tracking.virtualCapital" type="number" min="0" step="1000" class="w-full rounded-xl border border-slate-300 bg-slate-50 px-4 py-3 text-slate-900 outline-none transition focus:border-sky-500 dark:border-slate-600 dark:bg-slate-900 dark:text-white" />
            </label>
            <label class="block">
              <span class="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">{{ $t('portfolioBalance.rebalanceBand') }}</span>
              <input v-model.number="strategy.rebalanceBand" type="number" min="0" max="100" step="0.5" class="w-full rounded-xl border border-slate-300 bg-slate-50 px-4 py-3 text-slate-900 outline-none transition focus:border-sky-500 dark:border-slate-600 dark:bg-slate-900 dark:text-white" />
            </label>
            <label class="block">
              <span class="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">{{ $t('portfolioBalance.minTradeAmount') }}</span>
              <input v-model.number="strategy.minTradeAmount" type="number" min="0" step="100" class="w-full rounded-xl border border-slate-300 bg-slate-50 px-4 py-3 text-slate-900 outline-none transition focus:border-sky-500 dark:border-slate-600 dark:bg-slate-900 dark:text-white" />
            </label>
          </div>
        </section>

        <section class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800">
          <div class="overflow-hidden rounded-2xl border border-slate-200 dark:border-slate-700">
            <div class="overflow-x-auto">
              <table class="min-w-full divide-y divide-slate-200 dark:divide-slate-700">
                <thead class="bg-slate-50 dark:bg-slate-900/60">
                  <tr class="text-left text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                    <th class="px-4 py-3">{{ $t('portfolioBalance.symbol') }}</th>
                    <th class="px-4 py-3">
                      <span :class="hasExactTargetWeightSum ? 'text-emerald-600 dark:text-emerald-300' : 'text-rose-600 dark:text-rose-300'">
                        {{ $t('portfolioBalance.targetWeight') }} ({{ formatWeightSum(plan.targetWeightInputSum) }})
                      </span>
                    </th>
                    <th class="px-4 py-3">{{ $t('portfolioBalance.price') }}</th>
                    <th class="px-4 py-3">{{ $t('portfolioBalance.unitsHeld') }}</th>
                    <th class="px-4 py-3">{{ $t('portfolioBalance.currentValue') }}</th>
                    <th class="px-4 py-3">{{ $t('portfolioBalance.trackingDiffValue') }}</th>
                    <th class="px-4 py-3">{{ $t('portfolioBalance.remove') }}</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-200 bg-white dark:divide-slate-700 dark:bg-slate-800">
                  <tr v-for="asset in assets" :key="asset.id">
                    <td class="px-4 py-3">
                      <input
                        :value="asset.symbol"
                        type="text"
                        :placeholder="$t('portfolioBalance.emptySymbol')"
                        class="w-28 rounded-xl border border-slate-300 bg-slate-50 px-3 py-2 text-slate-900 outline-none transition focus:border-sky-500 dark:border-slate-600 dark:bg-slate-900 dark:text-white"
                        @change="updateAssetSymbol(asset.id, readInputValue($event))"
                      />
                    </td>
                    <td class="px-4 py-3">
                      <input
                        :value="asset.targetWeight"
                        type="number"
                        min="0"
                        step="0.5"
                        class="w-28 rounded-xl border border-slate-300 bg-slate-50 px-3 py-2 text-slate-900 outline-none transition focus:border-sky-500 dark:border-slate-600 dark:bg-slate-900 dark:text-white"
                        @input="updateAssetTargetWeight(asset.id, readInputValue($event))"
                      />
                    </td>
                    <td class="px-4 py-3 text-slate-600 dark:text-slate-300">
                      {{ asset.currentPrice ? formatMoney(asset.currentPrice) : '--' }}
                    </td>
                    <td class="px-4 py-3 text-slate-600 dark:text-slate-300">
                      {{ asset.units ? asset.units.toFixed(8) : '--' }}
                    </td>
                    <td class="px-4 py-3 text-slate-600 dark:text-slate-300">
                      {{ asset.currentPrice && asset.units ? formatMoney(holdingValue(asset)) : '--' }}
                    </td>
                    <td class="px-4 py-3" :class="returnClass(readPlanAsset(asset.id)?.trackingDiffValue || 0)">
                      {{ asset.currentPrice && asset.units ? signedMoney(readPlanAsset(asset.id)?.trackingDiffValue || 0) : '--' }}
                    </td>
                    <td class="px-4 py-3">
                      <button
                        type="button"
                        class="inline-flex items-center rounded-xl border border-slate-300 px-3 py-2 text-sm text-slate-500 transition hover:border-rose-300 hover:text-rose-600 disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-600 dark:text-slate-300 dark:hover:border-rose-500 dark:hover:text-rose-300"
                        :disabled="!canRemoveAsset"
                        @click="removeAsset(asset.id)"
                      >
                        <TrashIcon class="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </section>

        <section class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800">
          <div class="flex flex-col gap-3">
            <div class="flex items-center justify-between gap-4">
              <h2 class="text-xl font-semibold text-slate-900 dark:text-white">{{ $t('portfolioBalance.backtestTitle') }}</h2>
              <button
                type="button"
                class="inline-flex items-center justify-center rounded-xl border border-sky-200 bg-sky-50 px-4 py-2 text-sm font-medium text-sky-700 transition hover:bg-sky-100 disabled:cursor-not-allowed disabled:opacity-60 dark:border-sky-800 dark:bg-sky-950/40 dark:text-sky-200 dark:hover:bg-sky-900/50"
                :disabled="backtestLoading"
                @click="runBacktest"
              >
                <ArrowPathIcon class="mr-2 h-4 w-4" />
                {{ backtestLoading ? $t('portfolioBalance.backtesting') : $t('portfolioBalance.backtestRun') }}
              </button>
            </div>
            <div class="grid gap-4 lg:grid-cols-2">
              <AppDateField
                v-model="backtest.backtestStartDate"
                :label="$t('portfolioBalance.backtestStartDate')"
                :max="today"
              />
              <label class="block">
                <span class="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">{{ $t('portfolioBalance.backtestInitialCapital') }}</span>
                <input v-model.number="backtest.initialCapital" type="number" min="0" step="1000" class="w-full rounded-xl border border-slate-300 bg-slate-50 px-4 py-3 text-slate-900 outline-none transition focus:border-sky-500 dark:border-slate-600 dark:bg-slate-900 dark:text-white" />
              </label>
            </div>
          </div>

          <div v-if="backtestResult" class="mt-5 space-y-5">
            <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900/60">
              <div class="mb-3 text-sm font-semibold text-slate-700 dark:text-slate-200">{{ $t('backtest.equityCurve') }}</div>
              <div class="h-[320px]">
              <BacktestEquityChart :points="backtestResult.equityCurve" />
              </div>
            </div>
            <div class="grid grid-cols-2 gap-3 xl:grid-cols-8">
              <div class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 dark:border-slate-700 dark:bg-slate-900/60">
                <div class="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">{{ $t('portfolioBalance.backtestStartDate') }}</div>
                <div class="mt-1 font-semibold text-slate-900 dark:text-white">{{ formatDate(backtestResult.startDate) }}</div>
              </div>
              <div class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 dark:border-slate-700 dark:bg-slate-900/60">
                <div class="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">{{ $t('portfolioBalance.backtestEndDate') }}</div>
                <div class="mt-1 font-semibold text-slate-900 dark:text-white">{{ formatDate(backtestResult.endDate) }}</div>
              </div>
              <div class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 dark:border-slate-700 dark:bg-slate-900/60">
                <div class="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">{{ $t('portfolioBalance.totalReturn') }}</div>
                <div class="mt-1 font-semibold" :class="returnClass(backtestResult.totalReturnPct)">{{ signedPercent(backtestResult.totalReturnPct) }}</div>
              </div>
              <div class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 dark:border-slate-700 dark:bg-slate-900/60">
                <div class="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">{{ $t('portfolioBalance.annualizedReturn') }}</div>
                <div class="mt-1 font-semibold" :class="returnClass(backtestResult.annualizedReturnPct || 0)">{{ backtestResult.annualizedReturnPct === null ? '--' : signedPercent(backtestResult.annualizedReturnPct) }}</div>
              </div>
              <div class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 dark:border-slate-700 dark:bg-slate-900/60">
                <div class="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">{{ $t('portfolioBalance.maxDrawdown') }}</div>
                <div class="mt-1 font-semibold text-rose-600 dark:text-rose-300">{{ formatPercent(backtestResult.maxDrawdownPct) }}</div>
              </div>
              <div class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 dark:border-slate-700 dark:bg-slate-900/60">
                <div class="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">{{ $t('portfolioBalance.reviewCount') }}</div>
                <div class="mt-1 font-semibold text-slate-900 dark:text-white">{{ backtestResult.reviewCount }}</div>
              </div>
              <div class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 dark:border-slate-700 dark:bg-slate-900/60">
                <div class="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">{{ $t('portfolioBalance.outOfBandReviewCount') }}</div>
                <div class="mt-1 font-semibold text-amber-600 dark:text-amber-300">{{ backtestResult.outOfBandReviewCount }}</div>
              </div>
              <div class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 dark:border-slate-700 dark:bg-slate-900/60">
                <div class="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">{{ $t('portfolioBalance.rebalanceCount') }}</div>
                <div class="mt-1 font-semibold text-slate-900 dark:text-white">{{ backtestResult.rebalanceCount }}</div>
              </div>
            </div>
          </div>
          <div v-else class="mt-5 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-6 text-center text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-900/60 dark:text-slate-400">
            {{ $t('portfolioBalance.noBacktest') }}
          </div>
        </section>
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { ArrowDownTrayIcon, ArrowPathIcon, PlusIcon, TrashIcon } from '@heroicons/vue/24/outline'
import AppDateField from '@/components/AppDateField.vue'
import BacktestEquityChart from '@/components/BacktestEquityChart.vue'
import { usePortfolioBalancePage } from '@/modules/tools'
import { computePortfolioAssetHoldingValue } from '@/modules/tools/portfolioBalance'

const {
  portfolios,
  activePortfolioId,
  activePortfolio,
  assets,
  strategy,
  tracking,
  backtest,
  plan,
  canRemoveAsset,
  importLoading,
  marketLoading,
  backtestLoading,
  sourceMessage,
  sourceError,
  lastImportedRun,
  backtestResult,
  selectPortfolio,
  createPortfolio,
  deletePortfolio,
  addAsset,
  removeAsset,
  updateAssetSymbol,
  updateAssetTargetWeight,
  importLatestPaperHoldings,
  refreshMarketPrices,
  runBacktest,
} = usePortfolioBalancePage()

const today = new Date().toISOString().slice(0, 10)
const formatMoney = (value) => `$${Number(value || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
const signedMoney = (value) => `${value >= 0 ? '+' : '-'}$${Math.abs(Number(value || 0)).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
const formatPercent = (value) => `${Number(value || 0).toFixed(2)}%`
const formatWeightSum = (value) => `${Number(value || 0).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })}%`
const signedPercent = (value) => `${value >= 0 ? '+' : ''}${Number(value || 0).toFixed(2)}%`
const holdingValue = (asset) => computePortfolioAssetHoldingValue(asset)
const readInputValue = (event) => event?.target?.value || ''
const hasExactTargetWeightSum = computed(() => Math.abs(Number(plan.value?.targetWeightInputSum || 0) - 100) < 0.005)
const readPlanAsset = (assetId) => plan.value.assets.find((item) => item.id === assetId) || null

const formatDate = (value) => {
  if (!value) return '--'
  return value
}

const formatDateTime = (value) => {
  if (!value) return '--'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '--'
  return date.toLocaleString()
}

const strategyCardClass = (action) => {
  if (action === 'full') return 'bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-200'
  if (action === 'cashflow') return 'bg-sky-50 text-sky-700 dark:bg-sky-950/40 dark:text-sky-200'
  return 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-200'
}

const returnClass = (value) => {
  if (value > 0) return 'text-emerald-600 dark:text-emerald-300'
  if (value < 0) return 'text-rose-600 dark:text-rose-300'
  return 'text-slate-600 dark:text-slate-300'
}
</script>
