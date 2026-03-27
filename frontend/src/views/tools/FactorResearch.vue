<template>
  <div class="h-full overflow-y-auto bg-slate-50 transition-colors dark:bg-slate-900">
    <div class="mx-auto max-w-7xl space-y-6 p-6">
      <section class="panel p-6">
        <div class="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
          <div class="max-w-4xl">
            <div class="text-xs font-semibold uppercase tracking-[0.26em] text-cyan-600 dark:text-cyan-300">{{ $t('factorResearch.eyebrow') }}</div>
            <h1 class="mt-3 text-3xl font-semibold tracking-tight text-slate-900 dark:text-white">{{ $t('factorResearch.title') }}</h1>
            <p class="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">{{ $t('factorResearch.subtitle') }}</p>
          </div>
          <div class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200">
            {{ $t('factorResearch.hint') }}
            <div class="mt-2 text-xs text-slate-500 dark:text-slate-400">
              {{ $t('factorResearch.forwardHorizons') }}: {{ page.catalog.forward_horizons.length ? page.catalog.forward_horizons.join(' / ') : '--' }}
            </div>
          </div>
        </div>
      </section>

      <section class="panel p-5">
        <div class="grid gap-4 xl:grid-cols-[repeat(5,minmax(0,1fr))_auto]">
          <div>
            <label class="label">{{ $t('factorResearch.symbol') }}</label>
            <select v-model="page.form.symbol" class="input">
              <option v-for="item in page.catalog.symbols" :key="item" :value="item">{{ item }}</option>
            </select>
          </div>
          <div>
            <label class="label">{{ $t('factorResearch.timeframe') }}</label>
            <select v-model="page.form.timeframe" class="input">
              <option v-for="item in page.catalog.timeframes" :key="item" :value="item">{{ $t(`compare.tf.${item}`) }}</option>
            </select>
          </div>
          <div>
            <label class="label">{{ $t('factorResearch.lookbackDays') }}</label>
            <input v-model.number="page.form.days" class="input" type="number" min="60" step="10" />
          </div>
          <div>
            <label class="label">{{ $t('factorResearch.horizonBars') }}</label>
            <input v-model.number="page.form.horizon_bars" class="input" type="number" min="1" step="1" />
          </div>
          <div>
            <label class="label">{{ $t('factorResearch.maxLagBars') }}</label>
            <input v-model.number="page.form.max_lag_bars" class="input" type="number" min="0" step="1" />
          </div>
          <button class="primary-btn" :disabled="page.loading || page.catalogLoading" @click="page.runAnalysis">
            {{ page.loading ? $t('factorResearch.analyzing') : $t('factorResearch.run') }}
          </button>
        </div>

        <div class="mt-5 grid gap-5 xl:grid-cols-[minmax(0,0.72fr)_minmax(0,1fr)]">
          <div class="card-shell">
            <div class="section-title">{{ $t('factorResearch.categoryScope') }}</div>
            <div class="section-subtitle">{{ $t('factorResearch.categoryScopeHint') }}</div>
            <div class="mt-4 flex flex-wrap gap-2">
              <button v-for="category in page.catalog.categories" :key="category" class="chip" :class="page.categoryChipClass(category)" @click="page.toggleCategory(category)">
                {{ category }}
              </button>
            </div>
          </div>

          <div class="card-shell">
            <div class="flex items-center justify-between gap-3">
              <div>
                <div class="section-title">{{ $t('factorResearch.factorPool') }}</div>
                <div class="section-subtitle">{{ $t('factorResearch.factorPoolHint') }}</div>
              </div>
              <button class="text-sm font-medium text-cyan-600 dark:text-cyan-300" @click="page.resetFactorSelection">{{ $t('factorResearch.useAll') }}</button>
            </div>
            <div class="mt-4 flex max-h-40 flex-wrap gap-2 overflow-y-auto pr-1">
              <button v-for="factor in page.factorPool" :key="factor.factor_id" class="chip" :class="page.factorChipClass(factor.factor_id)" @click="page.toggleFactor(factor.factor_id)">
                {{ factor.name }}
              </button>
            </div>
          </div>
        </div>
      </section>

      <section v-if="page.error" class="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-600 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-200">
        {{ page.error }}
      </section>

      <section v-if="page.summary" class="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <article class="summary-card">
          <div class="summary-label">{{ $t('factorResearch.target') }}</div>
          <div class="summary-value">{{ page.summary.target_label }}</div>
          <div class="summary-hint">{{ page.summary.symbol }} · {{ page.summary.timeframe }}</div>
        </article>
        <article class="summary-card">
          <div class="summary-label">{{ $t('factorResearch.factorCount') }}</div>
          <div class="summary-value">{{ page.summary.factor_count }}</div>
          <div class="summary-hint">{{ $t('factorResearch.blendCount') }} {{ page.summary.blend_factor_count }}</div>
        </article>
        <article class="summary-card">
          <div class="summary-label">{{ $t('factorResearch.sampleRange') }}</div>
          <div class="summary-value text-lg">{{ page.formatDate(page.summary.sample_range.start) }}</div>
          <div class="summary-hint">{{ page.formatDate(page.summary.sample_range.end) }}</div>
        </article>
        <article class="summary-card">
          <div class="summary-label">{{ $t('factorResearch.forwardHorizons') }}</div>
          <div class="summary-value">{{ page.summary.forward_horizons.join(' / ') }}</div>
          <div class="summary-hint">{{ $t('factorResearch.horizonBars') }} {{ page.summary.horizon_bars }}</div>
        </article>
        <article class="summary-card">
          <div class="summary-label">{{ $t('factorResearch.datasetId') }}</div>
          <div class="summary-value">#{{ page.summary.dataset_id }}</div>
          <div class="summary-hint">{{ $t('factorResearch.maxLagBars') }} {{ page.summary.max_lag_bars }}</div>
        </article>
      </section>

      <div class="grid gap-6 2xl:grid-cols-[360px_minmax(0,1fr)]">
        <aside class="space-y-6">
          <section class="panel p-5">
            <div class="flex items-start justify-between gap-3">
              <div>
                <h2 class="text-lg font-semibold text-slate-900 dark:text-white">{{ $t('factorResearch.recentRuns') }}</h2>
                <p class="text-sm text-slate-500 dark:text-slate-400">{{ $t('factorResearch.recentRunsHint') }}</p>
              </div>
              <div class="text-xs text-slate-400">{{ page.runsLoading ? $t('factorResearch.loadingRuns') : page.runs.length }}</div>
            </div>
            <div class="mt-4 space-y-3">
              <button v-for="run in page.runs" :key="run.id" class="block w-full rounded-2xl border px-4 py-3 text-left transition" :class="run.id === page.selectedRunId ? 'border-cyan-500 bg-cyan-50 dark:border-cyan-400 dark:bg-cyan-500/10' : 'border-slate-200 bg-white hover:border-slate-300 dark:border-slate-700 dark:bg-slate-800/70 dark:hover:border-slate-600'" @click="page.loadRun(run.id)">
                <div class="flex items-start justify-between gap-3">
                  <div>
                    <div class="text-sm font-semibold text-slate-900 dark:text-white">{{ run.summary.symbol }} · {{ run.summary.timeframe }}</div>
                    <div class="mt-1 text-xs text-slate-500 dark:text-slate-400">{{ page.formatDate(run.created_at) }}</div>
                  </div>
                  <div class="text-xs text-slate-400">#{{ run.id }}</div>
                </div>
                <div class="mt-3 grid grid-cols-3 gap-2 text-xs">
                  <div class="mini-stat">
                    <div class="mini-stat-label">{{ $t('factorResearch.blendCount') }}</div>
                    <div class="mini-stat-value">{{ run.summary.blend_factor_count }}</div>
                  </div>
                  <div class="mini-stat">
                    <div class="mini-stat-label">{{ $t('factorResearch.lookbackDays') }}</div>
                    <div class="mini-stat-value">{{ run.summary.days }}</div>
                  </div>
                  <div class="mini-stat">
                    <div class="mini-stat-label">{{ $t('factorResearch.horizonBars') }}</div>
                    <div class="mini-stat-value">{{ run.summary.horizon_bars }}</div>
                  </div>
                </div>
              </button>
              <div v-if="!page.runsLoading && !page.runs.length" class="rounded-2xl border border-dashed border-slate-200 px-4 py-6 text-center text-sm text-slate-500 dark:border-slate-700 dark:text-slate-400">
                {{ $t('factorResearch.noRuns') }}
              </div>
            </div>
          </section>

          <section class="panel p-5">
            <div>
              <h2 class="text-lg font-semibold text-slate-900 dark:text-white">{{ $t('factorResearch.blendTitle') }}</h2>
              <p class="text-sm text-slate-500 dark:text-slate-400">{{ $t('factorResearch.blendSubtitle') }}</p>
            </div>
            <div v-if="page.blend" class="mt-4 space-y-4">
              <div class="grid grid-cols-2 gap-3">
                <div class="mini-stat">
                  <div class="mini-stat-label">{{ $t('factorResearch.entryThreshold') }}</div>
                  <div class="mini-stat-value">{{ page.formatNumber(page.blend.entry_threshold, 3) }}</div>
                </div>
                <div class="mini-stat">
                  <div class="mini-stat-label">{{ $t('factorResearch.exitThreshold') }}</div>
                  <div class="mini-stat-value">{{ page.formatNumber(page.blend.exit_threshold, 3) }}</div>
                </div>
              </div>
              <div class="space-y-2">
                <div v-for="item in page.blend.selected_factors" :key="item.factor_id" class="rounded-2xl border border-slate-200 bg-slate-50 px-3 py-3 dark:border-slate-700 dark:bg-slate-900/60">
                  <div class="flex items-start justify-between gap-3">
                    <div>
                      <div class="text-sm font-semibold text-slate-900 dark:text-white">{{ item.name }}</div>
                      <div class="mt-1 text-xs text-slate-500 dark:text-slate-400">{{ item.category }}</div>
                    </div>
                    <div class="text-sm font-semibold text-slate-900 dark:text-white">{{ page.formatNumber(item.weight, 3) }}</div>
                  </div>
                  <div class="mt-3 grid grid-cols-3 gap-2 text-xs">
                    <div class="mini-stat">
                      <div class="mini-stat-label">{{ $t('factorResearch.score') }}</div>
                      <div class="mini-stat-value" :class="page.scoreClass(item.score)">{{ page.formatNumber(item.score, 2) }}</div>
                    </div>
                    <div class="mini-stat">
                      <div class="mini-stat-label">{{ $t('factorResearch.stability') }}</div>
                      <div class="mini-stat-value">{{ page.formatPct(item.stability) }}</div>
                    </div>
                    <div class="mini-stat">
                      <div class="mini-stat-label">{{ $t('factorResearch.turnover') }}</div>
                      <div class="mini-stat-value">{{ page.formatPct(item.turnover) }}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="mt-4 rounded-2xl border border-dashed border-slate-200 px-4 py-6 text-center text-sm text-slate-500 dark:border-slate-700 dark:text-slate-400">
              {{ $t('factorResearch.noBlend') }}
            </div>
          </section>

          <section class="panel p-5">
            <div>
              <h2 class="text-lg font-semibold text-slate-900 dark:text-white">{{ $t('factorResearch.executionTitle') }}</h2>
              <p class="text-sm text-slate-500 dark:text-slate-400">{{ $t('factorResearch.executionSubtitle') }}</p>
            </div>
            <div class="mt-4 grid gap-4 sm:grid-cols-2">
              <div>
                <label class="label">{{ $t('backtest.initialCash') }}</label>
                <input v-model.number="page.executionForm.initial_cash" class="input" type="number" min="1000" step="1000" />
              </div>
              <div>
                <label class="label">{{ $t('backtest.feeRate') }}</label>
                <input v-model.number="page.executionForm.fee_rate" class="input" type="number" min="0" step="0.01" />
              </div>
              <div>
                <label class="label">{{ $t('backtest.positionSize') }}</label>
                <input v-model.number="page.executionForm.position_size_pct" class="input" type="number" min="1" max="100" step="1" />
              </div>
              <div>
                <label class="label">{{ $t('backtest.stakeMode') }}</label>
                <select v-model="page.executionForm.stake_mode" class="input">
                  <option value="fixed">{{ $t('backtest.stakeModeFixed') }}</option>
                  <option value="unlimited">{{ $t('backtest.stakeModeUnlimited') }}</option>
                </select>
              </div>
              <div>
                <label class="label">{{ $t('factorResearch.entryThreshold') }}</label>
                <input v-model.number="page.executionForm.entry_threshold" class="input" type="number" step="0.01" />
              </div>
              <div>
                <label class="label">{{ $t('factorResearch.exitThreshold') }}</label>
                <input v-model.number="page.executionForm.exit_threshold" class="input" type="number" step="0.01" />
              </div>
              <div>
                <label class="label">{{ $t('backtest.stoplossLabel') }}</label>
                <input v-model.number="page.executionForm.stoploss_pct" class="input" type="number" step="0.01" />
              </div>
              <div>
                <label class="label">{{ $t('factorResearch.takeprofit') }}</label>
                <input v-model.number="page.executionForm.takeprofit_pct" class="input" type="number" min="0" step="0.01" />
              </div>
              <div class="sm:col-span-2">
                <label class="label">{{ $t('factorResearch.maxHoldBars') }}</label>
                <input v-model.number="page.executionForm.max_hold_bars" class="input" type="number" min="1" step="1" />
              </div>
            </div>
            <p class="mt-4 text-sm leading-6 text-slate-500 dark:text-slate-400">{{ $t('factorResearch.executionHint') }}</p>
            <div class="mt-4 flex flex-col gap-3">
              <button class="primary-btn" :disabled="!page.selectedRunId || !!page.executionLoading" @click="page.startExecution('backtest')">
                {{ page.executionLoading === 'backtest' ? $t('backtest.running') : $t('factorResearch.runBacktest') }}
              </button>
              <button class="secondary-btn" :disabled="!page.selectedRunId || !!page.executionLoading" @click="page.startExecution('paper')">
                {{ page.executionLoading === 'paper' ? $t('backtest.running') : $t('factorResearch.startPaper') }}
              </button>
            </div>
          </section>
        </aside>

        <section class="space-y-6">
          <div class="grid gap-6 xl:grid-cols-[minmax(0,0.92fr)_minmax(0,1.08fr)]">
            <section class="panel overflow-hidden">
              <div class="border-b border-slate-200 px-5 py-4 dark:border-slate-700">
                <h2 class="text-lg font-semibold text-slate-900 dark:text-white">{{ $t('factorResearch.rankingTitle') }}</h2>
                <p class="text-sm text-slate-500 dark:text-slate-400">{{ $t('factorResearch.rankingSubtitle') }}</p>
              </div>
              <div class="max-h-[880px] overflow-y-auto">
                <button v-for="item in page.ranking" :key="item.factor_id" class="block w-full border-b border-slate-100 px-5 py-4 text-left transition last:border-b-0 hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-900/50" :class="item.factor_id === page.selectedFactorId ? 'bg-cyan-50 dark:bg-cyan-500/10' : ''" @click="page.selectFactor(item.factor_id)">
                  <div class="flex items-start justify-between gap-3">
                    <div>
                      <div class="text-sm font-semibold text-slate-900 dark:text-white">{{ item.name }}</div>
                      <div class="mt-1 text-xs text-slate-500 dark:text-slate-400">{{ item.category }} · {{ item.feature_mode }}</div>
                    </div>
                    <div class="text-right">
                      <div class="text-xl font-semibold" :class="page.scoreClass(item.score)">{{ page.formatNumber(item.score, 2) }}</div>
                      <div class="text-xs text-slate-400">{{ $t('factorResearch.score') }}</div>
                    </div>
                  </div>
                  <div class="mt-3 grid grid-cols-4 gap-2 text-xs">
                    <div class="mini-stat">
                      <div class="mini-stat-label">{{ $t('factorResearch.correlation') }}</div>
                      <div class="mini-stat-value" :class="page.correlationClass(item.correlation)">{{ page.formatNumber(item.correlation, 3) }}</div>
                    </div>
                    <div class="mini-stat">
                      <div class="mini-stat-label">{{ $t('factorResearch.stability') }}</div>
                      <div class="mini-stat-value">{{ page.formatPct(item.stability) }}</div>
                    </div>
                    <div class="mini-stat">
                      <div class="mini-stat-label">{{ $t('factorResearch.turnover') }}</div>
                      <div class="mini-stat-value">{{ page.formatPct(item.turnover) }}</div>
                    </div>
                    <div class="mini-stat">
                      <div class="mini-stat-label">{{ $t('factorResearch.bestLag') }}</div>
                      <div class="mini-stat-value">+{{ item.best_lag }}</div>
                    </div>
                  </div>
                </button>
                <div v-if="!page.ranking.length && !page.loading" class="px-5 py-12 text-center text-sm text-slate-500 dark:text-slate-400">
                  {{ $t('factorResearch.noRanking') }}
                </div>
              </div>
            </section>

            <section v-if="page.selectedDetail" class="space-y-6">
              <div class="panel p-5">
                <div class="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
                  <div>
                    <div class="text-xs font-semibold uppercase tracking-[0.24em] text-cyan-600 dark:text-cyan-300">{{ page.selectedDetail.category }}</div>
                    <h2 class="mt-2 text-2xl font-semibold text-slate-900 dark:text-white">{{ page.selectedDetail.name }}</h2>
                    <p class="mt-2 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-300">{{ page.selectedDetail.description || $t('factorResearch.noDescription') }}</p>
                  </div>
                  <div class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm dark:border-slate-700 dark:bg-slate-900/60">
                    <div class="text-slate-500 dark:text-slate-400">{{ $t('factorResearch.sampleRange') }}</div>
                    <div class="mt-1 font-semibold text-slate-900 dark:text-white">{{ page.formatDate(page.selectedDetail.sample_range.start) }} - {{ page.formatDate(page.selectedDetail.sample_range.end) }}</div>
                  </div>
                </div>
              </div>

              <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                <article class="metric-card">
                  <div class="metric-label">{{ $t('factorResearch.correlation') }}</div>
                  <div class="metric-value" :class="page.correlationClass(page.selectedDetail.correlation)">{{ page.formatNumber(page.selectedDetail.correlation, 3) }}</div>
                </article>
                <article class="metric-card">
                  <div class="metric-label">{{ $t('factorResearch.rankCorrelation') }}</div>
                  <div class="metric-value" :class="page.correlationClass(page.selectedDetail.rank_correlation)">{{ page.formatNumber(page.selectedDetail.rank_correlation, 3) }}</div>
                </article>
                <article class="metric-card">
                  <div class="metric-label">{{ $t('factorResearch.hitRate') }}</div>
                  <div class="metric-value text-slate-900 dark:text-white">{{ page.formatPct(page.selectedDetail.hit_rate) }}</div>
                </article>
                <article class="metric-card">
                  <div class="metric-label">{{ $t('factorResearch.quantileSpread') }}</div>
                  <div class="metric-value" :class="page.correlationClass(page.selectedDetail.quantile_spread)">{{ page.formatPct(page.selectedDetail.quantile_spread) }}</div>
                </article>
                <article class="metric-card">
                  <div class="metric-label">{{ $t('factorResearch.turnover') }}</div>
                  <div class="metric-value text-slate-900 dark:text-white">{{ page.formatPct(page.selectedDetail.turnover) }}</div>
                </article>
                <article class="metric-card">
                  <div class="metric-label">{{ $t('factorResearch.icIr') }}</div>
                  <div class="metric-value" :class="page.correlationClass(page.selectedDetail.ic_ir)">{{ page.formatNumber(page.selectedDetail.ic_ir, 3) }}</div>
                </article>
              </div>

              <section class="panel p-5">
                <div class="detail-head">
                  <div>
                    <h3 class="detail-title">{{ $t('factorResearch.forwardMetricsTitle') }}</h3>
                    <p class="detail-subtitle">{{ $t('factorResearch.forwardMetricsSubtitle') }}</p>
                  </div>
                </div>
                <div class="overflow-x-auto">
                  <table class="min-w-full text-sm">
                    <thead>
                      <tr class="border-b border-slate-200 text-left text-slate-500 dark:border-slate-700 dark:text-slate-400">
                        <th class="px-2 py-3">{{ $t('factorResearch.forwardBarsShort') }}</th>
                        <th class="px-2 py-3">{{ $t('factorResearch.correlation') }}</th>
                        <th class="px-2 py-3">{{ $t('factorResearch.rankCorrelation') }}</th>
                        <th class="px-2 py-3">{{ $t('factorResearch.icIr') }}</th>
                        <th class="px-2 py-3">{{ $t('factorResearch.hitRate') }}</th>
                        <th class="px-2 py-3">{{ $t('factorResearch.quantileSpread') }}</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="item in page.selectedDetail.forward_metrics" :key="item.horizon" class="border-b border-slate-100 last:border-b-0 dark:border-slate-800">
                        <td class="px-2 py-3 font-medium text-slate-900 dark:text-white">+{{ item.horizon }}</td>
                        <td class="px-2 py-3" :class="page.correlationClass(item.correlation)">{{ page.formatNumber(item.correlation, 3) }}</td>
                        <td class="px-2 py-3" :class="page.correlationClass(item.rank_correlation)">{{ page.formatNumber(item.rank_correlation, 3) }}</td>
                        <td class="px-2 py-3" :class="page.correlationClass(item.ic_ir)">{{ page.formatNumber(item.ic_ir, 3) }}</td>
                        <td class="px-2 py-3 text-slate-900 dark:text-white">{{ page.formatPct(item.hit_rate) }}</td>
                        <td class="px-2 py-3" :class="page.correlationClass(item.quantile_spread)">{{ page.formatPct(item.quantile_spread) }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </section>
            </section>
          </div>

          <section v-if="page.selectedDetail" class="grid gap-6 xl:grid-cols-2">
            <section class="detail-card">
              <div class="detail-head">
                <div>
                  <h3 class="detail-title">{{ $t('factorResearch.seriesTitle') }}</h3>
                  <p class="detail-subtitle">{{ $t('factorResearch.seriesSubtitle') }}</p>
                </div>
              </div>
              <div class="h-[320px]">
                <FactorLineChart :dark="page.isDark" :categories="page.selectedDetail.normalized_series.map((item) => item.date.slice(0, 10))" :series="[
                  { name: $t('factorResearch.priceZ'), data: page.selectedDetail.normalized_series.map((item) => item.price_z), color: '#0f172a' },
                  { name: $t('factorResearch.factorZ'), data: page.selectedDetail.normalized_series.map((item) => item.factor_z), color: '#06b6d4' },
                ]" />
              </div>
            </section>

            <section class="detail-card">
              <div class="detail-head">
                <div>
                  <h3 class="detail-title">{{ $t('factorResearch.blendSeriesTitle') }}</h3>
                  <p class="detail-subtitle">{{ $t('factorResearch.blendSeriesSubtitle') }}</p>
                </div>
              </div>
              <div class="h-[320px]">
                <FactorLineChart :dark="page.isDark" :categories="(page.blend?.normalized_series || []).map((item) => item.date.slice(0, 10))" :series="[
                  { name: $t('factorResearch.priceZ'), data: (page.blend?.normalized_series || []).map((item) => item.price_z), color: '#0f172a' },
                  { name: $t('factorResearch.blendScore'), data: (page.blend?.normalized_series || []).map((item) => item.factor_z), color: '#14b8a6' },
                ]" />
              </div>
            </section>
          </section>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import FactorLineChart from '@/components/factors/FactorLineChart.vue'
import { useFactorResearchPage } from '@/modules/factors/useFactorResearchPage'

const page = useFactorResearchPage()
</script>

<style scoped>
.panel { @apply rounded-3xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800; }
.label { @apply mb-1 block text-xs font-bold uppercase tracking-wide text-slate-500 dark:text-slate-400; }
.input { @apply w-full rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-cyan-500 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100; }
.primary-btn { @apply rounded-2xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-cyan-600 dark:hover:bg-cyan-500; }
.secondary-btn { @apply rounded-2xl border border-slate-300 px-5 py-3 text-sm font-semibold text-slate-700 transition hover:border-slate-400 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-600 dark:text-slate-100 dark:hover:border-slate-500 dark:hover:bg-slate-800; }
.summary-card { @apply rounded-3xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-800; }
.summary-label { @apply text-xs font-bold uppercase tracking-wide text-slate-500 dark:text-slate-400; }
.summary-value { @apply mt-3 text-2xl font-semibold text-slate-900 dark:text-white; }
.summary-hint { @apply mt-2 text-xs text-slate-500 dark:text-slate-400; }
.metric-card { @apply rounded-3xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-800; }
.metric-label { @apply text-xs font-bold uppercase tracking-wide text-slate-500 dark:text-slate-400; }
.metric-value { @apply mt-3 text-2xl font-semibold; }
.detail-card { @apply rounded-3xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-800; }
.detail-head { @apply mb-4 flex items-center justify-between gap-3; }
.detail-title { @apply text-lg font-semibold text-slate-900 dark:text-white; }
.detail-subtitle { @apply mt-1 text-sm text-slate-500 dark:text-slate-400; }
.card-shell { @apply rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900/50; }
.section-title { @apply text-sm font-semibold text-slate-900 dark:text-white; }
.section-subtitle { @apply mt-1 text-xs text-slate-500 dark:text-slate-400; }
.chip { @apply rounded-full border px-3 py-1.5 text-sm font-medium transition; }
.mini-stat { @apply rounded-xl bg-slate-100 px-3 py-2 dark:bg-slate-900; }
.mini-stat-label { @apply text-[11px] uppercase tracking-wide text-slate-400; }
.mini-stat-value { @apply mt-1 font-semibold text-slate-900 dark:text-white; }
</style>
