<template>
  <div class="macro-page min-h-full overflow-y-auto bg-[#020713] text-slate-100">
    <section class="mx-auto flex w-full max-w-7xl flex-col gap-8 px-4 py-6 sm:px-6 lg:px-8">
      <div class="grid gap-6 lg:grid-cols-[minmax(0,1.15fr)_minmax(360px,0.85fr)] lg:items-end">
        <div class="space-y-6 py-3">
          <div class="inline-flex items-center gap-2 border border-emerald-400/30 bg-emerald-400/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-emerald-300">
            Dollar Liquidity Monitor
          </div>
          <div class="space-y-4">
            <h1 class="max-w-3xl text-4xl font-semibold leading-tight text-white sm:text-5xl">
              美元流动性看板
            </h1>
            <p class="max-w-3xl text-sm leading-6 text-slate-400 sm:text-base">
              把 Fed 资产负债表、TGA、ON RRP、政策利率、美元指数、波动率和 M2 放在同一页，先看美元流动性主线，再下钻到每个宏观指标。
            </p>
          </div>

          <div class="grid gap-3 sm:grid-cols-3">
            <div class="macro-stat">
              <span>流动性状态</span>
              <strong :class="scoreToneClass">{{ scoreLabel }}</strong>
            </div>
            <div class="macro-stat">
              <span>综合评分</span>
              <strong>{{ score === null ? '--' : score }}</strong>
            </div>
            <div class="macro-stat">
              <span>最近更新</span>
              <strong>{{ lastUpdated }}</strong>
            </div>
          </div>

          <div class="flex flex-wrap items-center gap-3">
            <button class="macro-primary-button" :disabled="loading" @click="load">
              {{ loading ? '刷新中...' : '刷新宏观数据' }}
            </button>
            <a class="macro-secondary-button" href="#macro-drivers">
              查看核心驱动
            </a>
          </div>
        </div>

        <div class="border border-slate-800 bg-slate-950/60 p-4 shadow-2xl shadow-cyan-950/20">
          <div class="mb-4 flex items-center justify-between">
            <div>
              <div class="text-sm font-semibold text-white">关键脉冲</div>
              <div class="text-xs text-slate-500">过去 {{ lookbackDays }} 天历史</div>
            </div>
            <div class="h-2 w-2 bg-emerald-400"></div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <article v-for="card in heroCards" :key="card.definition.id" class="mini-card">
              <div class="flex items-start justify-between gap-2">
                <div class="min-w-0">
                  <div class="truncate text-[11px] uppercase text-slate-500">{{ card.definition.shortLabel }}</div>
                  <div class="mt-1 text-lg font-semibold text-white">{{ card.valueLabel }}</div>
                </div>
                <span :class="['change-pill', toneClass(card.tone)]">{{ card.changeLabel }}</span>
              </div>
              <MacroSparkline
                class="mt-2"
                :history="card.indicator?.history || []"
                :color="sparkColor(card.tone)"
                :mode="card.definition.id === 'TGA' || card.definition.id === 'ONRRP' ? 'bar' : 'line'"
                height="62px"
              />
            </article>
          </div>
        </div>
      </div>

      <div v-if="error" class="border border-red-500/40 bg-red-950/40 px-4 py-3 text-sm text-red-200">
        {{ error }}
      </div>

      <div v-if="loading" class="grid gap-4 md:grid-cols-3">
        <div v-for="item in 6" :key="item" class="h-44 animate-pulse border border-slate-800 bg-slate-900/50"></div>
      </div>

      <template v-else>
        <section class="grid gap-4 lg:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
          <div class="macro-panel p-5">
            <div class="mb-5 flex items-start justify-between">
              <div>
                <div class="panel-kicker">DLI 流动性评分</div>
                <h2 class="mt-2 text-lg font-semibold text-white">综合压力仪表盘</h2>
              </div>
              <span class="border border-slate-700 px-2 py-1 text-xs text-slate-400">0-100</span>
            </div>

            <div class="flex items-end justify-between gap-4">
              <div>
                <div :class="['text-4xl font-semibold', scoreToneClass]">{{ score === null ? '--' : score }}</div>
                <div class="mt-2 text-sm text-slate-400">{{ scoreLabel }}</div>
              </div>
              <div class="w-full max-w-sm">
                <div class="mb-2 flex justify-between text-[11px] text-slate-500">
                  <span>收紧</span>
                  <span>中性</span>
                  <span>宽松</span>
                </div>
                <div class="relative h-3 bg-slate-800">
                  <div class="absolute inset-y-0 left-0 bg-orange-500" :style="{ width: `${scoreWidth}%` }"></div>
                  <div class="absolute inset-y-0 left-[43%] w-px bg-slate-950"></div>
                  <div class="absolute inset-y-0 left-[68%] w-px bg-slate-950"></div>
                </div>
              </div>
            </div>

            <div class="mt-6 space-y-2 border-t border-slate-800 pt-4">
              <div v-for="item in alerts" :key="item" class="flex gap-2 text-sm text-slate-300">
                <span class="mt-2 h-1.5 w-1.5 flex-shrink-0 bg-emerald-400"></span>
                <span>{{ item }}</span>
              </div>
            </div>
          </div>

          <div class="macro-panel p-5">
            <div class="panel-kicker">今日重点</div>
            <h2 class="mt-2 text-lg font-semibold text-white">评分分解与归因</h2>
            <div class="mt-5 space-y-3">
              <div v-for="driver in drivers.slice(0, 7)" :key="driver.definition.id" class="driver-row">
                <div class="grid grid-cols-[120px_minmax(0,1fr)_44px] items-center gap-3">
                  <div class="min-w-0">
                    <div class="truncate text-sm font-medium text-slate-200">{{ driver.definition.shortLabel }}</div>
                    <div class="text-[11px] text-slate-500">{{ driver.valueLabel }}</div>
                  </div>
                  <div class="h-3 bg-slate-800">
                    <div
                      :class="driver.score >= 50 ? 'bg-emerald-400' : 'bg-orange-500'"
                      class="h-full"
                      :style="{ width: `${driver.score}%` }"
                    ></div>
                  </div>
                  <div :class="['text-right text-xs font-semibold', driver.score >= 50 ? 'text-emerald-300' : 'text-orange-300']">
                    {{ driver.score }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section v-for="group in groups" :key="group.id" class="space-y-3">
          <div class="flex flex-col justify-between gap-2 border-l-2 border-emerald-400 pl-3 sm:flex-row sm:items-end">
            <div>
              <h2 class="text-lg font-semibold text-white">{{ group.title }}</h2>
              <p class="mt-1 text-sm text-slate-500">{{ group.description }}</p>
            </div>
          </div>

          <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            <article v-for="card in group.cards" :key="card.definition.id" class="metric-card">
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                  <div class="truncate text-xs uppercase tracking-wide text-slate-500">{{ card.definition.shortLabel }}</div>
                  <h3 class="mt-1 text-sm font-semibold text-white">{{ card.definition.label }}</h3>
                </div>
                <span :class="['change-pill', toneClass(card.tone)]">{{ card.changeLabel }}</span>
              </div>

              <div class="mt-4 flex items-end justify-between gap-3">
                <div class="text-2xl font-semibold text-white">{{ card.valueLabel }}</div>
                <div class="text-right text-[11px] text-slate-500">{{ card.freshness }}</div>
              </div>

              <MacroSparkline
                class="mt-3"
                :history="card.indicator?.history || []"
                :color="sparkColor(card.tone)"
                :mode="card.definition.id === 'TGA' || card.definition.id === 'ONRRP' ? 'bar' : 'line'"
              />

              <p class="mt-3 border-t border-slate-800 pt-3 text-xs leading-5 text-slate-500">
                {{ card.definition.description }}
              </p>
            </article>
          </div>
        </section>

        <section id="macro-drivers" class="macro-panel p-5">
          <div class="panel-kicker">关键驱动</div>
          <h2 class="mt-2 text-lg font-semibold text-white">流动性贡献条</h2>
          <div class="mt-5 space-y-3">
            <div v-for="driver in drivers" :key="driver.definition.id" class="grid gap-2 sm:grid-cols-[150px_minmax(0,1fr)_56px] sm:items-center">
              <div>
                <div class="text-sm font-medium text-slate-200">{{ driver.definition.label }}</div>
                <div class="text-[11px] text-slate-500">30 日 {{ driver.changeLabel }}</div>
              </div>
              <div class="relative h-5 bg-slate-800">
                <div class="absolute inset-y-0 left-1/2 w-px bg-slate-950"></div>
                <div
                  v-if="driver.score >= 50"
                  class="absolute inset-y-0 left-1/2 bg-emerald-400"
                  :style="{ width: `${driver.score - 50}%` }"
                ></div>
                <div
                  v-else
                  class="absolute inset-y-0 bg-orange-500"
                  :style="{ left: `${driver.score}%`, width: `${50 - driver.score}%` }"
                ></div>
              </div>
              <div :class="['text-right text-sm font-semibold', driver.score >= 50 ? 'text-emerald-300' : 'text-orange-300']">
                {{ driver.score }}
              </div>
            </div>
          </div>
        </section>
      </template>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import MacroSparkline from '@/components/market/MacroSparkline.vue'
import { useMacroLiquidityPage, type MacroMetricCard } from '@/modules/market'

const lookbackDays = 365
const {
  loading,
  error,
  score,
  scoreLabel,
  scoreTone,
  heroCards,
  groups,
  drivers,
  alerts,
  lastUpdated,
  load,
} = useMacroLiquidityPage(lookbackDays)

const scoreWidth = computed(() => Math.max(0, Math.min(100, score.value ?? 0)))
const scoreToneClass = computed(() => {
  if (scoreTone.value === 'support') return 'text-emerald-300'
  if (scoreTone.value === 'pressure') return 'text-orange-300'
  return 'text-cyan-300'
})

const toneClass = (tone: MacroMetricCard['tone']) => {
  if (tone === 'support') return 'border-emerald-400/40 bg-emerald-400/10 text-emerald-300'
  if (tone === 'pressure') return 'border-orange-400/40 bg-orange-400/10 text-orange-300'
  return 'border-slate-600 bg-slate-800/70 text-slate-300'
}

const sparkColor = (tone: MacroMetricCard['tone']) => {
  if (tone === 'support') return '#34d399'
  if (tone === 'pressure') return '#fb923c'
  return '#38bdf8'
}

onMounted(() => {
  load()
})
</script>

<style scoped>
.macro-page {
  background:
    radial-gradient(circle at top left, rgba(8, 145, 178, 0.16), transparent 34rem),
    linear-gradient(180deg, #020713 0%, #030816 52%, #020617 100%);
}

.macro-stat,
.mini-card,
.metric-card,
.macro-panel {
  border: 1px solid rgba(30, 41, 59, 0.95);
  background: rgba(2, 6, 23, 0.72);
}

.macro-stat {
  padding: 0.85rem 1rem;
}

.macro-stat span {
  display: block;
  font-size: 0.68rem;
  color: #64748b;
}

.macro-stat strong {
  margin-top: 0.35rem;
  display: block;
  font-size: 0.95rem;
}

.macro-primary-button,
.macro-secondary-button {
  border: 1px solid rgba(45, 212, 191, 0.35);
  padding: 0.7rem 1rem;
  font-size: 0.82rem;
  font-weight: 700;
  transition: background-color 0.18s ease, border-color 0.18s ease;
}

.macro-primary-button {
  background: #20e3b2;
  color: #04111d;
}

.macro-primary-button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.macro-secondary-button {
  background: rgba(15, 23, 42, 0.65);
  color: #cbd5e1;
}

.mini-card,
.metric-card {
  padding: 0.9rem;
}

.metric-card {
  min-height: 17rem;
}

.change-pill {
  flex-shrink: 0;
  border-width: 1px;
  padding: 0.18rem 0.4rem;
  font-size: 0.68rem;
  font-weight: 700;
}

.panel-kicker {
  color: #34d399;
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.driver-row {
  border: 1px solid rgba(30, 41, 59, 0.75);
  background: rgba(15, 23, 42, 0.32);
  padding: 0.7rem;
}
</style>
