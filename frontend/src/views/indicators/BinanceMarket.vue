<template>
  <div class="h-full overflow-y-auto bg-[radial-gradient(circle_at_top,rgba(8,145,178,0.08),transparent_38%),linear-gradient(180deg,#f8fafc_0%,#eef2ff_100%)] dark:bg-slate-950">
    <div class="space-y-6 p-6 lg:p-8">
      <section class="grid gap-6 lg:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)] 2xl:grid-cols-[1.6fr_1fr] 2xl:gap-8">
        <div class="space-y-6">
          <section class="space-y-4">
            <div class="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
              <div>
                <h3 class="text-xl font-semibold text-slate-900">排行榜</h3>
                <p class="mt-1 text-sm text-slate-500">左边保留原来的行情浏览位。</p>
              </div>

              <div class="flex flex-wrap items-center gap-3 text-sm">
                <button
                  type="button"
                  @click="autoRefresh = !autoRefresh"
                  class="flex items-center gap-2 rounded-xl bg-slate-50 px-3 py-1.5 ring-1 ring-slate-200 transition hover:bg-slate-100"
                >
                  <span class="text-slate-500">自动刷新</span>
                  <span :class="autoRefresh ? 'font-semibold text-cyan-600' : 'text-slate-400'">{{ autoRefresh ? '开启' : '关闭' }}</span>
                </button>

                <button
                  @click="fetchData"
                  :disabled="loading"
                  class="rounded-xl bg-slate-900 px-4 py-1.5 font-medium text-white transition hover:bg-slate-800 disabled:opacity-50"
                >
                  {{ loading ? '刷新中...' : '刷新' }}
                </button>
              </div>
            </div>

            <div class="grid gap-6 xl:grid-cols-2">
              <article class="overflow-hidden rounded-[30px] border border-slate-200/70 bg-white/90 shadow-sm xl:col-span-2">
                <div class="flex items-center justify-between border-b border-slate-200 px-5 py-4">
                  <div>
                    <h4 class="text-lg font-semibold text-slate-900">合约榜</h4>
                    <p class="text-sm text-slate-500">点 24H 或资金费率切换排序</p>
                  </div>
                  <div class="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
                    {{ contractSort.field === 'price_change_pct' ? '按 24H 排序' : '按资金费率排序' }}
                  </div>
                </div>

                <div class="overflow-x-auto">
                  <table class="min-w-full text-left text-sm">
                    <thead class="bg-slate-50 text-slate-500">
                      <tr>
                        <th class="px-5 py-3 font-semibold">Symbol</th>
                        <th class="px-5 py-3 font-semibold">
                          <button
                            type="button"
                            @click="toggleContractSort('price_change_pct')"
                            class="inline-flex items-center gap-2 transition"
                            :class="contractSort.field === 'price_change_pct' ? 'text-slate-900' : 'hover:text-slate-700'"
                          >
                            <span>24H</span>
                            <span class="text-xs">{{ contractSort.field === 'price_change_pct' ? (contractSort.direction === 'desc' ? '↓' : '↑') : '↕' }}</span>
                          </button>
                        </th>
                        <th class="px-5 py-3 font-semibold">Price</th>
                        <th class="px-5 py-3 font-semibold">
                          <button
                            type="button"
                            @click="toggleContractSort('funding_rate_pct')"
                            class="inline-flex items-center gap-2 transition"
                            :class="contractSort.field === 'funding_rate_pct' ? 'text-slate-900' : 'hover:text-slate-700'"
                          >
                            <span>Funding</span>
                            <span class="text-xs">{{ contractSort.field === 'funding_rate_pct' ? (contractSort.direction === 'desc' ? '↓' : '↑') : '↕' }}</span>
                          </button>
                        </th>
                        <th class="px-5 py-3 font-semibold">Quote Vol</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr
                        v-for="item in contractRows"
                        :key="`${item.market}-${item.symbol}`"
                        class="cursor-pointer border-t border-slate-100 transition hover:bg-slate-50"
                        @click="selectedKey = toItemKey(item)"
                      >
                        <td class="px-5 py-4 font-medium text-slate-900">
                          <button
                            type="button"
                            class="rounded-full px-2 py-1 transition hover:bg-cyan-50 hover:text-cyan-700"
                            @click.stop="openChart(item)"
                          >
                            {{ displaySymbol(item.symbol) }}
                          </button>
                        </td>
                        <td class="px-5 py-4" :class="valueTone(item.price_change_pct)">{{ formatSigned(item.price_change_pct) }}</td>
                        <td class="px-5 py-4 text-slate-600">{{ formatPrice(item.mark_price ?? item.last_price) }}</td>
                        <td class="px-5 py-4" :class="valueTone(item.funding_rate_pct)">{{ formatSigned(item.funding_rate_pct, 4) }}</td>
                        <td class="px-5 py-4 text-slate-600">{{ formatCompact(item.quote_volume) }}</td>
                      </tr>
                      <tr v-if="!contractRows.length">
                        <td colspan="5" class="px-5 py-8 text-center text-sm text-slate-400">当前没有可展示的合约数据</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </article>

              <article class="overflow-hidden rounded-[30px] border border-slate-200/70 bg-white/90 shadow-sm xl:col-span-2">
                <div class="flex items-center justify-between border-b border-slate-200 px-5 py-4">
                  <div>
                    <h4 class="text-lg font-semibold text-slate-900">现货榜</h4>
                    <p class="text-sm text-slate-500">点 24H 切换涨跌排序</p>
                  </div>
                  <div class="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
                    {{ spotSortDirection === 'desc' ? '按涨幅排序' : '按跌幅排序' }}
                  </div>
                </div>
                <div class="overflow-x-auto">
                  <table class="min-w-full text-left text-sm">
                    <thead class="bg-slate-50 text-slate-500">
                      <tr>
                        <th class="px-5 py-3 font-semibold">Symbol</th>
                        <th class="px-5 py-3 font-semibold">
                          <button
                            type="button"
                            @click="toggleSpotSort"
                            class="inline-flex items-center gap-2 transition text-slate-900"
                          >
                            <span>24H</span>
                            <span class="text-xs">{{ spotSortDirection === 'desc' ? '↓' : '↑' }}</span>
                          </button>
                        </th>
                        <th class="px-5 py-3 font-semibold">Price</th>
                        <th class="px-5 py-3 font-semibold">Quote Vol</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="item in spotRows" :key="item.symbol" class="border-t border-slate-100">
                        <td class="px-5 py-4 font-medium text-slate-900">
                          <button
                            type="button"
                            class="rounded-full px-2 py-1 transition hover:bg-cyan-50 hover:text-cyan-700"
                            @click="openChart({ ...item, market_label: '现货' })"
                          >
                            {{ displaySymbol(item.symbol) }}
                          </button>
                        </td>
                        <td class="px-5 py-4" :class="valueTone(item.price_change_pct)">{{ formatSigned(item.price_change_pct) }}</td>
                        <td class="px-5 py-4 text-slate-600">{{ formatPrice(item.last_price) }}</td>
                        <td class="px-5 py-4 text-slate-600">{{ formatCompact(item.quote_volume) }}</td>
                      </tr>
                      <tr v-if="!spotRows.length">
                        <td colspan="4" class="px-5 py-8 text-center text-sm text-slate-400">当前没有可展示的现货数据</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </article>

              <article class="overflow-hidden rounded-[30px] border border-slate-200/70 bg-white/90 shadow-sm xl:col-span-2">
                <div class="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 px-5 py-4">
                  <div>
                    <h4 class="text-lg font-semibold text-slate-900">Web3 热度榜</h4>
                    <p class="text-sm text-slate-500">搜索、趋势、社交、交易和聪明钱合成</p>
                  </div>
                  <div class="flex items-center gap-2">
                    <select
                      v-model="web3ChainId"
                      class="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700 outline-none"
                    >
                      <option v-for="item in web3ChainOptions" :key="item.value" :value="item.value">{{ item.label }}</option>
                    </select>
                    <button
                      type="button"
                      class="rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-800 disabled:opacity-50"
                      :disabled="web3Loading"
                      @click="fetchWeb3HeatRank"
                    >
                      {{ web3Loading ? '刷新中...' : '刷新' }}
                    </button>
                  </div>
                </div>
                <div v-if="web3Error" class="border-b border-rose-100 bg-rose-50 px-5 py-3 text-sm text-rose-600">{{ web3Error }}</div>
                <div class="overflow-x-auto">
                  <table class="min-w-full text-left text-sm">
                    <thead class="bg-slate-50 text-slate-500">
                      <tr>
                        <th class="px-5 py-3 font-semibold">Rank</th>
                        <th class="px-5 py-3 font-semibold">Token</th>
                        <th class="px-5 py-3 font-semibold">Score</th>
                        <th class="px-5 py-3 font-semibold">24H</th>
                        <th class="px-5 py-3 font-semibold">MCap</th>
                        <th class="px-5 py-3 font-semibold">Liq</th>
                        <th class="px-5 py-3 font-semibold">Smart</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr
                        v-for="item in web3HeatRank"
                        :key="`${item.chain_id}-${item.contract_address}`"
                        class="cursor-pointer border-t border-slate-100 transition hover:bg-cyan-50/70"
                        @click="openWeb3Token(item)"
                      >
                        <td class="px-5 py-4 text-slate-500">{{ item.rank ?? '--' }}</td>
                        <td class="px-5 py-4">
                          <div class="flex items-center gap-3">
                            <img v-if="item.icon_url" :src="item.icon_url" alt="" class="h-7 w-7 rounded-full" />
                            <span v-else class="h-7 w-7 rounded-full bg-slate-100" />
                            <div>
                              <button type="button" class="font-semibold text-slate-900 transition hover:text-cyan-700">
                                {{ item.symbol || '--' }}
                              </button>
                              <div class="max-w-[160px] truncate text-xs text-slate-400">{{ item.contract_address }}</div>
                            </div>
                          </div>
                        </td>
                        <td class="px-5 py-4 font-semibold text-cyan-700">{{ formatScore(item.heat_score) }}</td>
                        <td class="px-5 py-4" :class="valueTone(item.metrics?.percent_change_24h)">{{ formatSigned(item.metrics?.percent_change_24h) }}</td>
                        <td class="px-5 py-4 text-slate-600">{{ formatCompact(item.metrics?.market_cap) }}</td>
                        <td class="px-5 py-4 text-slate-600">{{ formatCompact(item.metrics?.liquidity) }}</td>
                        <td class="px-5 py-4 text-slate-600">{{ formatCompact(item.metrics?.smart_money_inflow) }}</td>
                      </tr>
                      <tr v-if="!web3HeatRank.length">
                        <td colspan="7" class="px-5 py-8 text-center text-sm text-slate-400">当前没有可展示的 Web3 热度数据</td>
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
                class="rounded-[20px] border border-slate-200/70 bg-white/85 p-3 shadow-sm backdrop-blur"
              >
                <div class="flex items-center justify-between">
                  <p class="text-[10px] font-semibold uppercase tracking-wider text-slate-500">{{ card.label }}</p>
                  <p class="text-[10px] text-slate-400">{{ card.hint }}</p>
                </div>
                <p class="mt-1 text-2xl font-bold text-slate-900">{{ card.value }}</p>
              </article>
            </section>

            <section v-if="error" class="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-600">
              {{ error }}
            </section>

            <div class="flex flex-col gap-3 rounded-[30px] border border-slate-200/70 bg-white/90 p-4 shadow-sm">
              <div class="flex flex-col gap-4 px-2 xl:flex-row xl:items-center xl:justify-between">
                <div class="flex flex-wrap items-baseline gap-3">
                  <h2 class="text-xl font-bold text-slate-900">异动监控</h2>
                  <span class="rounded bg-slate-900 px-2 py-0.5 text-xs font-semibold text-white">{{ monitor.quote_asset }}</span>
                  <span class="text-xs text-slate-500">更新于 {{ formatTime(monitor.updated_at) }}</span>
                </div>

                <label class="flex w-fit items-center gap-2 rounded-xl bg-slate-50 px-3 py-1.5 text-sm ring-1 ring-slate-200">
                  <span class="text-slate-500">涨幅阈值</span>
                  <input v-model.number="minRisePct" type="number" min="1" max="30" step="0.5" class="w-14 bg-transparent text-center font-semibold text-slate-900 outline-none" />
                </label>
              </div>
              <div class="flex flex-wrap items-center gap-3">
                <div class="flex flex-wrap gap-2 rounded-full border border-slate-200 bg-slate-50 p-1">
                  <button
                    v-for="item in [
                      { key: 'focus', label: '优先关注' },
                      { key: 'momentum', label: '有动能' },
                      { key: 'natural', label: '走势自然' },
                      { key: 'all', label: '全部' },
                    ]"
                    :key="item.key"
                    @click="mode = item.key"
                    class="rounded-full px-4 py-2 text-sm transition"
                    :class="mode === item.key ? 'bg-slate-900 text-white' : 'text-slate-600 hover:bg-slate-100'"
                  >
                    {{ item.label }}
                  </button>
                </div>

                <div class="flex flex-wrap gap-2 rounded-full border border-slate-200 bg-slate-50 p-1">
                  <button
                    v-for="item in [
                      { key: 'all', label: '全部市场' },
                      { key: 'spot', label: '现货' },
                      { key: 'usdm', label: 'U 本位' },
                    ]"
                    :key="item.key"
                    @click="marketFilter = item.key"
                    class="rounded-full px-4 py-2 text-sm transition"
                    :class="marketFilter === item.key ? 'bg-cyan-500 text-slate-950' : 'text-slate-600 hover:bg-slate-100'"
                  >
                    {{ item.label }}
                  </button>
                </div>
              </div>
            </div>

            <div class="grid gap-6 2xl:grid-cols-[minmax(0,1.08fr),360px]">
              <article class="overflow-hidden rounded-[30px] border border-slate-200/70 bg-white/90 shadow-sm">
                <div class="flex items-center justify-between border-b border-slate-200 px-5 py-4">
                  <div>
                    <h4 class="text-lg font-semibold text-slate-900">监控列表</h4>
                    <p class="text-sm text-slate-500">{{ filteredItems.length }} 个结果</p>
                  </div>
                </div>

                <div class="overflow-x-auto">
                  <table class="min-w-full text-left text-sm">
                    <thead class="bg-slate-50 text-slate-500">
                      <tr>
                        <th class="px-5 py-3 font-semibold">标的</th>
                        <th class="px-4 py-3 font-semibold">当天</th>
                        <th class="px-4 py-3 font-semibold">15m</th>
                        <th class="px-4 py-3 font-semibold">1h</th>
                        <th class="px-4 py-3 font-semibold">自然度</th>
                        <th class="px-4 py-3 font-semibold">动能</th>
                        <th class="px-5 py-3 font-semibold">状态</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr
                        v-for="item in filteredItems"
                        :key="`${item.market}-${item.symbol}`"
                        class="cursor-pointer border-t border-slate-100 transition hover:bg-slate-50"
                        :class="toItemKey(selectedItem) === toItemKey(item) ? 'bg-cyan-50/80' : ''"
                        @click="selectedKey = toItemKey(item)"
                      >
                        <td class="px-5 py-4">
                          <div class="flex items-center gap-3">
                            <span class="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-600">{{ item.market_label }}</span>
                            <div>
                              <button
                                type="button"
                                class="font-semibold text-slate-900 transition hover:text-cyan-700"
                                @click.stop="openChart(item)"
                              >
                                {{ displaySymbol(item.symbol) }}
                              </button>
                              <div class="text-xs text-slate-500">{{ formatPrice(item.mark_price ?? item.last_price) }}</div>
                            </div>
                          </div>
                        </td>
                        <td class="px-4 py-4 font-medium" :class="valueTone(item.price_change_pct)">{{ formatSigned(item.price_change_pct) }}</td>
                        <td class="px-4 py-4" :class="valueTone(item.change_15m_pct)">{{ formatSigned(item.change_15m_pct) }}</td>
                        <td class="px-4 py-4" :class="valueTone(item.change_1h_pct)">{{ formatSigned(item.change_1h_pct) }}</td>
                        <td class="px-4 py-4 text-slate-700">{{ formatScore(item.natural_score) }}</td>
                        <td class="px-4 py-4 text-slate-700">{{ formatScore(item.momentum_score) }}</td>
                        <td class="px-5 py-4">
                          <span class="inline-flex rounded-full px-3 py-1 text-xs font-semibold ring-1" :class="verdictTone(item.verdict)">
                            {{ item.verdict }}
                          </span>
                        </td>
                      </tr>
                      <tr v-if="!filteredItems.length">
                        <td colspan="7" class="px-5 py-10 text-center text-sm text-slate-500">
                          当前筛选下没有结果
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </article>

              <article class="rounded-[30px] border border-slate-200/70 bg-white/90 p-5 shadow-sm" v-if="selectedItem">
                <div class="flex items-start justify-between gap-4">
                  <div>
                    <div class="flex items-center gap-2">
                      <span class="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-600">{{ selectedItem.market_label }}</span>
                      <button
                        type="button"
                        class="text-2xl font-semibold text-slate-900 transition hover:text-cyan-700"
                        @click="openChart(selectedItem)"
                      >
                        {{ displaySymbol(selectedItem.symbol) }}
                      </button>
                    </div>
                    <p class="mt-2 text-sm text-slate-500">{{ selectedItem.follow_status }}</p>
                  </div>
                  <span class="inline-flex rounded-full px-3 py-1 text-xs font-semibold ring-1" :class="verdictTone(selectedItem.verdict)">
                    {{ selectedItem.verdict }}
                  </span>
                </div>

                <div class="mt-5 grid grid-cols-2 gap-3">
                  <div class="rounded-2xl bg-slate-50 px-4 py-3">
                    <div class="text-xs uppercase tracking-[0.18em] text-slate-400">当天</div>
                    <div class="mt-2 text-lg font-semibold" :class="valueTone(selectedItem.price_change_pct)">{{ formatSigned(selectedItem.price_change_pct) }}</div>
                  </div>
                  <div class="rounded-2xl bg-slate-50 px-4 py-3">
                    <div class="text-xs uppercase tracking-[0.18em] text-slate-400">成交额</div>
                    <div class="mt-2 text-lg font-semibold text-slate-900">{{ formatCompact(selectedItem.quote_volume) }}</div>
                  </div>
                  <div class="rounded-2xl bg-slate-50 px-4 py-3">
                    <div class="text-xs uppercase tracking-[0.18em] text-slate-400">自然度</div>
                    <div class="mt-2 text-lg font-semibold text-slate-900">{{ formatScore(selectedItem.natural_score) }}</div>
                  </div>
                  <div class="rounded-2xl bg-slate-50 px-4 py-3">
                    <div class="text-xs uppercase tracking-[0.18em] text-slate-400">动能</div>
                    <div class="mt-2 text-lg font-semibold text-slate-900">{{ formatScore(selectedItem.momentum_score) }}</div>
                  </div>
                </div>

                <div class="mt-5 space-y-3 rounded-[26px] bg-slate-950 p-4 text-white">
                  <div class="flex items-center justify-between text-sm">
                    <span class="text-slate-400">15m / 1h</span>
                    <span>{{ formatSigned(selectedItem.change_15m_pct) }} / {{ formatSigned(selectedItem.change_1h_pct) }}</span>
                  </div>
                  <div class="flex items-center justify-between text-sm">
                    <span class="text-slate-400">距高点</span>
                    <span :class="valueTone(selectedItem.pullback_from_high_pct, false)">{{ formatSigned(selectedItem.pullback_from_high_pct) }}</span>
                  </div>
                  <div class="flex items-center justify-between text-sm">
                    <span class="text-slate-400">EMA20 偏离</span>
                    <span>{{ formatSigned(selectedItem.ema20_gap_15m_pct) }} / {{ formatSigned(selectedItem.ema20_gap_1h_pct) }}</span>
                  </div>
                  <div class="flex items-center justify-between text-sm">
                    <span class="text-slate-400">RSI</span>
                    <span>{{ formatSigned(selectedItem.rsi_15m, 1, '', false) }} / {{ formatSigned(selectedItem.rsi_1h, 1, '', false) }}</span>
                  </div>
                  <div class="flex items-center justify-between text-sm" v-if="selectedItem.funding_rate_pct !== null && selectedItem.funding_rate_pct !== undefined">
                    <span class="text-slate-400">Funding</span>
                    <span :class="valueTone(selectedItem.funding_rate_pct)">{{ formatSigned(selectedItem.funding_rate_pct, 3) }}</span>
                  </div>
                </div>

                <div class="mt-5">
                  <h5 class="text-sm font-semibold text-slate-900">判断依据</h5>
                  <div class="mt-3 flex flex-wrap gap-2">
                    <span
                      v-for="reason in selectedItem.reasons"
                      :key="reason"
                      class="rounded-full bg-cyan-50 px-3 py-1.5 text-sm text-cyan-700"
                    >
                      {{ reason }}
                    </span>
                  </div>
                </div>
              </article>
            </div>
          </section>
        </div>
      </section>
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
      :chart-colors="chartColors"
      :format-score="formatScore"
      :format-price="formatPrice"
      :format-signed="formatSigned"
      :format-compact="formatCompact"
      :value-tone="valueTone"
      @close="closeWeb3Token"
      @update:interval="web3KlineInterval = $event"
    />

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
      @close="closeChart"
      @load-more="loadMoreChartHistory"
      @update:timeframe="chartTimeframe = $event"
    />
  </div>
</template>

<script setup lang="ts">
defineOptions({ name: 'BinanceMarket' })

import BinanceSymbolChartDialog from '@/components/market/BinanceSymbolChartDialog.vue'
import BinanceWeb3TokenDialog from '@/components/market/BinanceWeb3TokenDialog.vue'
import { useBinanceMarketPage } from '@/modules/market'

const {
  loading,
  error,
  minRisePct,
  mode,
  marketFilter,
  autoRefresh,
  monitor,
  spotRows,
  spotSortDirection,
  contractRows,
  contractSort,
  web3ChainId,
  web3ChainOptions,
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
  fetchWeb3HeatRank,
  openWeb3Token,
  closeWeb3Token,
  filteredItems,
  selectedItem,
  selectedKey,
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
  valueTone,
  verdictTone,
  toItemKey,
} = useBinanceMarketPage()
</script>
