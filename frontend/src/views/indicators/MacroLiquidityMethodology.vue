<template>
  <div class="macro-detail-page min-h-full overflow-y-auto text-slate-900 dark:text-slate-100">
    <section class="flex w-full flex-col gap-6 px-3 py-5 sm:px-4 lg:px-5 xl:px-6">
      <div class="flex flex-col gap-4 border-b border-stone-200 pb-5 dark:border-slate-800 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <RouterLink class="detail-back-link" :to="{ name: 'IndicatorsMacro' }">返回宏观经济</RouterLink>
          <p class="detail-kicker mt-4">DLI 计算原理</p>
          <h1 class="detail-title mt-2">美元流动性评分如何生成</h1>
          <p class="mt-3 max-w-3xl text-sm leading-6 text-stone-600 dark:text-slate-400">
            DLI 不是单个宏观指标，而是把政策流动性、融资成本、信用压力和风险偏好代理放入同一评分框架。分数越高，代表当前环境相对历史样本越宽松。
          </p>
        </div>
        <div class="flex flex-wrap items-center gap-3">
          <RouterLink class="detail-secondary-button" :to="{ name: 'IndicatorsMacroHistory' }">历史走势</RouterLink>
          <button class="detail-primary-button" :disabled="loading" @click="load">
            {{ loading ? '刷新中...' : '刷新数据' }}
          </button>
        </div>
      </div>

      <div v-if="error" class="border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-500/40 dark:bg-red-950/40 dark:text-red-200">
        {{ error }}
      </div>

      <section class="grid gap-4 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
        <article class="detail-panel p-5">
          <p class="detail-kicker">状态边界</p>
          <h2 class="mt-2 text-lg font-semibold text-slate-950 dark:text-white">四阶段判定</h2>
          <div class="mt-5 grid gap-3 sm:grid-cols-2">
            <div v-for="regime in regimes" :key="regime.title" class="method-card">
              <div class="method-swatch" :style="{ background: regime.color }"></div>
              <h3 class="mt-3 text-sm font-semibold text-slate-950 dark:text-white">{{ regime.title }}</h3>
              <p class="mt-1 text-xs text-stone-500 dark:text-slate-400">{{ regime.range }}</p>
              <p class="mt-3 text-xs leading-5 text-stone-600 dark:text-slate-400">{{ regime.description }}</p>
            </div>
          </div>
        </article>

        <article class="detail-panel p-5">
          <p class="detail-kicker">计算流程</p>
          <h2 class="mt-2 text-lg font-semibold text-slate-950 dark:text-white">从指标到综合评分</h2>
          <ol class="mt-5 space-y-4">
            <li v-for="step in methodologySteps" :key="step.title" class="method-step">
              <span>{{ step.index }}</span>
              <div>
                <h3 class="text-sm font-semibold text-slate-950 dark:text-white">{{ step.title }}</h3>
                <p class="mt-1 text-xs leading-5 text-stone-600 dark:text-slate-400">{{ step.body }}</p>
              </div>
            </li>
          </ol>
        </article>
      </section>

      <section class="detail-panel">
        <div class="border-b border-stone-200 p-5 dark:border-slate-800">
          <p class="detail-kicker">指标权重</p>
          <h2 class="mt-2 text-lg font-semibold text-slate-950 dark:text-white">当前纳入 DLI 的驱动项</h2>
          <p class="mt-2 text-sm text-stone-500 dark:text-slate-400">
            权重分为原始权重和有效权重。有效权重会根据当前可用数据覆盖率重新归一，避免缺失指标直接扭曲综合分。
          </p>
        </div>
        <div class="overflow-x-auto">
          <table class="min-w-full text-left text-sm">
            <thead class="method-table-head">
              <tr>
                <th class="px-5 py-3 font-semibold">指标</th>
                <th class="px-5 py-3 font-semibold">分组</th>
                <th class="px-5 py-3 font-semibold">方向</th>
                <th class="px-5 py-3 font-semibold">原始权重</th>
                <th class="px-5 py-3 font-semibold">有效权重</th>
                <th class="px-5 py-3 font-semibold">当前分数</th>
                <th class="px-5 py-3 font-semibold">贡献</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="driver in drivers" :key="driver.definition.id" class="method-table-row">
                <td class="px-5 py-4">
                  <div class="font-semibold text-slate-950 dark:text-white">{{ driver.definition.label }}</div>
                  <div class="mt-1 text-xs text-stone-500 dark:text-slate-500">{{ driver.definition.description }}</div>
                </td>
                <td class="px-5 py-4">{{ groupLabel(driver.definition.group) }}</td>
                <td class="px-5 py-4">{{ polarityLabel(driver.definition.polarity) }}</td>
                <td class="px-5 py-4">{{ componentWeight(driver) }}</td>
                <td class="px-5 py-4">{{ formatWeight(driver.effectiveWeight) }}</td>
                <td class="px-5 py-4">{{ driver.score }}</td>
                <td class="px-5 py-4" :class="driver.contribution && driver.contribution >= 0 ? 'text-[#0f6b4f] dark:text-emerald-300' : 'text-[#c84c28] dark:text-orange-300'">
                  {{ formatContribution(driver.contribution) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useMacroLiquidityPage, type MacroDriver, type MacroGroupId, type MacroPolarity } from '@/modules/market'

const {
  loading,
  error,
  thresholds,
  drivers,
  load,
} = useMacroLiquidityPage(365)

const thresholdValues = computed(() => ({
  p20: thresholds.value?.p20 ?? 43,
  p50: thresholds.value?.p50 ?? 50,
  p80: thresholds.value?.p80 ?? 68,
}))

const regimes = computed(() => [
  {
    title: '流动性收紧',
    range: `≤ P20 (${thresholdValues.value.p20.toFixed(1)})`,
    color: '#c84c28',
    description: '综合分处于历史低分位，说明关键指标整体偏向抽走流动性或抬高融资压力。',
  },
  {
    title: '中性偏紧',
    range: `P20-P50 (${thresholdValues.value.p20.toFixed(1)}-${thresholdValues.value.p50.toFixed(1)})`,
    color: '#c9873a',
    description: '未进入极端收紧，但低于历史中位数，风险资产仍需考虑宏观压力。',
  },
  {
    title: '中性偏松',
    range: `P50-P80 (${thresholdValues.value.p50.toFixed(1)}-${thresholdValues.value.p80.toFixed(1)})`,
    color: '#8a8f56',
    description: '高于历史中位数，流动性环境边际友好，但不是极端宽松。',
  },
  {
    title: '流动性宽松',
    range: `≥ P80 (${thresholdValues.value.p80.toFixed(1)})`,
    color: '#0f6b4f',
    description: '综合分处于历史高分位，美元流动性通常对风险偏好形成支撑。',
  },
])

const methodologySteps = [
  {
    index: '01',
    title: '统一方向',
    body: '每个指标先定义方向：有些指标越高越支撑风险资产，例如美联储资产负债表、M2；有些指标越低越支撑，例如 TGA、ON RRP、利率、VIX 和美元指数。',
  },
  {
    index: '02',
    title: '和自身历史比较',
    body: '当前值不直接横向相加，而是放回自身历史窗口，计算稳健 z-score 和历史分位，解决不同单位、频率和量纲不可比的问题。',
  },
  {
    index: '03',
    title: '转为 0-100 分',
    body: '每个指标转换成支持度分数。50 是中性附近，越接近 100 越宽松，越接近 0 越收紧。',
  },
  {
    index: '04',
    title: '按分组权重汇总',
    body: '政策与准备金池、融资与利率、信用与中介、风险与价格四组分别加权。若部分指标缺失，可用组内权重会重新归一。',
  },
  {
    index: '05',
    title: '用历史分位定义状态',
    body: '综合分再和历史综合分分布比较，使用 P20、P50、P80 划分四个状态，而不是用固定绝对分数硬切。',
  },
]

const groupLabel = (group: MacroGroupId) => ({
  policy: '政策与准备金池',
  funding: '融资与利率',
  credit: '信用与中介',
  risk: '风险与价格',
}[group])

const polarityLabel = (polarity: MacroPolarity) => (
  polarity === 'higherSupports' ? '越高越宽松' : '越低越宽松'
)

const formatWeight = (value: number) => `${value.toFixed(2)}%`
const formatContribution = (value: number | null) => (
  typeof value === 'number' ? `${value >= 0 ? '+' : ''}${value.toFixed(2)}` : '--'
)
const componentWeight = (driver: MacroDriver) => `${driver.rawWeight.toFixed(2)}%`

onMounted(() => {
  load()
})
</script>

<style scoped>
.macro-detail-page {
  background: #f7f4ed;
}

.dark .macro-detail-page {
  background:
    radial-gradient(circle at top left, rgba(8, 145, 178, 0.16), transparent 34rem),
    linear-gradient(180deg, #020713 0%, #030816 52%, #020617 100%);
}

.detail-panel,
.method-card {
  border: 1px solid #e4ded3;
  background: rgba(255, 255, 255, 0.88);
}

.dark .detail-panel,
.dark .method-card {
  border-color: rgba(30, 41, 59, 0.95);
  background: rgba(2, 6, 23, 0.72);
}

.method-card {
  padding: 0.9rem;
}

.detail-kicker {
  color: #0f6b4f;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.detail-title {
  color: #14110f;
  font-family: Georgia, "Times New Roman", serif;
  font-size: clamp(2rem, 4vw, 3.25rem);
  font-weight: 600;
  letter-spacing: 0;
  line-height: 1.1;
}

.dark .detail-title {
  color: #ffffff;
}

.detail-back-link,
.detail-primary-button,
.detail-secondary-button {
  border: 1px solid #0f6b4f;
  padding: 0.65rem 0.95rem;
  font-size: 0.82rem;
  font-weight: 700;
}

.detail-back-link,
.detail-secondary-button {
  background: #ffffff;
  color: #0f6b4f;
}

.detail-primary-button {
  background: #0f6b4f;
  color: #ffffff;
}

.detail-primary-button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.method-swatch {
  height: 0.35rem;
  width: 3rem;
}

.method-step {
  display: grid;
  grid-template-columns: 2.25rem minmax(0, 1fr);
  gap: 0.9rem;
}

.method-step span {
  color: #0f6b4f;
  font-family: Georgia, "Times New Roman", serif;
  font-size: 1.35rem;
  font-weight: 700;
}

.method-table-head {
  background: rgba(237, 243, 238, 0.9);
  color: #0f172a;
}

.dark .method-table-head {
  background: rgba(15, 23, 42, 0.86);
  color: #e2e8f0;
}

.method-table-row {
  border-top: 1px solid #eee7dc;
}

.dark .method-table-row {
  border-color: rgba(30, 41, 59, 0.75);
}
</style>
