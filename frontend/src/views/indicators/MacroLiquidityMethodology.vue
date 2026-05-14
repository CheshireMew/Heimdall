<template>
  <div class="macro-detail-page min-h-full overflow-y-auto text-slate-900 dark:text-slate-100">
    <section class="flex w-full flex-col gap-6 px-3 py-5 sm:px-4 lg:px-5 xl:px-6">
      <div class="flex flex-col gap-4 border-b border-stone-200 pb-5 dark:border-slate-800 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <RouterLink class="detail-back-link" :to="{ name: 'IndicatorsMacro' }">返回宏观经济</RouterLink>
          <p class="detail-kicker mt-4">DLI 计算原理</p>
          <h1 class="detail-title mt-2">美元流动性评分如何生成</h1>
          <p class="mt-3 max-w-3xl text-sm leading-6 text-stone-600 dark:text-slate-400">
            DLI 是一个当期美元流动性压力测度。它把政策准备金、融资管道、信用中介和市场价格反馈放到同一方向、同一尺度下比较；状态分位越高，代表当前环境相对过去 5 年越紧。
          </p>
        </div>
        <div class="flex flex-wrap items-center gap-3">
          <RouterLink class="detail-secondary-button" :to="{ name: 'IndicatorsMacroHistory' }">历史走势</RouterLink>
          <button class="detail-primary-button" :disabled="loading" @click="refresh">
            {{ loading ? '刷新中...' : '刷新数据' }}
          </button>
        </div>
      </div>

      <div v-if="error" class="border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-500/40 dark:bg-red-950/40 dark:text-red-200">
        {{ error }}
      </div>

      <section class="grid gap-4 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
        <article class="detail-panel p-5">
          <p class="detail-kicker">模型定位</p>
          <h2 class="mt-2 text-lg font-semibold text-slate-950 dark:text-white">当期状态，不是收益预测</h2>
          <div class="mt-5 space-y-3 text-sm leading-6 text-stone-600 dark:text-slate-400">
            <p>这个模型回答的问题是：今天美元流动性压力处在过去几年分布的什么位置。它不回答未来 20 天或 60 天风险资产会涨跌多少。</p>
            <p>原因很直接：TGA、ON RRP、SRF、VIX、信用利差这些指标每天都在变化，今天的状态到几周后通常已经不是同一个状态。把今天的状态拿去预测很远的未来收益，容易把不同状态混在一起。</p>
            <p>因此这里更适合做宏观背景和仓位环境判断，而不是短线交易信号。</p>
          </div>
        </article>

        <article class="detail-panel p-5">
          <p class="detail-kicker">与公开站口径</p>
          <h2 class="mt-2 text-lg font-semibold text-slate-950 dark:text-white">独立复刻，不镜像私有 API</h2>
          <div class="mt-5 space-y-3 text-sm leading-6 text-stone-600 dark:text-slate-400">
            <p>本页模型参考 DollarLiquidity 公开方法论和公开指标结构，但后端使用官方数据源独立计算，不直接代理它的 /api/regime。</p>
            <p>目标站的首页分数使用服务端未完全公开的 regime z-score 细节，因此本地分数可能与目标站有小幅偏差。偏差通常来自单指标 z-score 的窗口、压缩、平滑或采样方式。</p>
            <p>这种设计保留了可解释性和可复现性：每个指标的当前值、压力 z、历史分位、有效权重和贡献都在诊断表中展示。</p>
          </div>
        </article>
      </section>

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
            综合评分先生成压力方向的复合 z-score，再转成 5 年滚动百分位作为状态分数。核心权重为政策与准备金 65%，融资与管道 10%，信用与中介 5%，风险与价格 20%，组内等权。
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
                <th class="px-5 py-3 font-semibold">压力 z</th>
                <th class="px-5 py-3 font-semibold">历史分位</th>
                <th class="px-5 py-3 font-semibold">贡献</th>
                <th class="px-5 py-3 font-semibold">数据滞后</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="driver in drivers" :key="driver.definition.id" class="method-table-row">
                <td class="px-5 py-4">
                  <div class="font-semibold text-slate-950 dark:text-white">{{ driver.definition.label }}</div>
                  <div class="mt-1 text-xs text-stone-500 dark:text-slate-500">{{ driver.definition.description }}</div>
                </td>
                <td class="px-5 py-4">{{ driver.definition.groupLabel }}</td>
                <td class="px-5 py-4">{{ polarityLabel(driver.definition.polarity) }}</td>
                <td class="px-5 py-4">{{ componentWeight(driver) }}</td>
                <td class="px-5 py-4">{{ formatWeight(driver.effectiveWeight) }}</td>
                <td class="px-5 py-4">{{ driver.score }}</td>
                <td class="px-5 py-4" :class="driver.zScore && driver.zScore >= 0 ? 'text-[#c84c28] dark:text-orange-300' : 'text-[#0f6b4f] dark:text-emerald-300'">
                  {{ formatSignedNumber(driver.zScore) }}
                </td>
                <td class="px-5 py-4">{{ formatPercentile(driver.percentile) }}</td>
                <td class="px-5 py-4" :class="driver.contribution && driver.contribution >= 0 ? 'text-[#c84c28] dark:text-orange-300' : 'text-[#0f6b4f] dark:text-emerald-300'">
                  {{ formatSignedNumber(driver.contribution) }}
                </td>
                <td class="px-5 py-4">{{ driver.dataLagLabel }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="grid gap-4 lg:grid-cols-3">
        <article v-for="section in detailSections" :key="section.title" class="detail-panel p-5">
          <p class="detail-kicker">{{ section.kicker }}</p>
          <h2 class="mt-2 text-lg font-semibold text-slate-950 dark:text-white">{{ section.title }}</h2>
          <ul class="mt-5 space-y-3">
            <li v-for="item in section.items" :key="item" class="flex gap-2 text-sm leading-6 text-stone-600 dark:text-slate-400">
              <span class="mt-2 h-1.5 w-1.5 flex-shrink-0 bg-[#0f6b4f] dark:bg-emerald-400"></span>
              <span>{{ item }}</span>
            </li>
          </ul>
        </article>
      </section>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { formatPercentile, formatSignedNumber } from '@/modules/format'
import { useMacroLiquidityPage, type MacroDriver, type MacroPolarity } from '@/modules/market'
import { useMacroRegimes } from '@/modules/market/macroLiquidityPresentation'

const {
  loading,
  error,
  thresholds,
  drivers,
  load,
  refresh,
} = useMacroLiquidityPage(365)

const regimes = useMacroRegimes(thresholds)

const methodologySteps = [
  {
    index: '01',
    title: '多源数据接入',
    body: '采集并对齐 FRED、Treasury Fiscal Data 和 NY Fed Markets 的跨频率序列。TGA 使用财政部 DTS 日频数据；SOFR-IORB、银行现金缓冲和净流动性是派生序列。',
  },
  {
    index: '02',
    title: '统一压力方向',
    body: '所有指标先转成压力方向：数值上升会收紧的指标保留正向；数值下降会收紧的指标反向。处理后，z-score 为正代表收紧压力，z-score 为负代表流动性缓和。',
  },
  {
    index: '03',
    title: '稳健统计标准化',
    body: '核心指标放回 10 年滚动窗口，用中位数和 MAD 计算稳健 z-score，并截断到 [-4, +4]。当 MAD 不可用时，回退到总体标准差，避免零波动序列中断模型。',
  },
  {
    index: '04',
    title: '风险组压缩',
    body: 'VIX、美元指数、10Y 实际利率属于价格反馈项，先用 2 年滚动百分位压缩，再映射回 z-score，降低极端市场价格对总分的循环污染。',
  },
  {
    index: '05',
    title: '按分组权重汇总',
    body: '政策与准备金池占 65%，融资与管道占 10%，信用与中介占 5%，风险与价格占 20%。组内等权；若部分指标缺失，按可用组和可用指标重新归一有效权重。',
  },
  {
    index: '06',
    title: '用历史分位定义状态',
    body: '复合 z-score 再和 5 年滚动分布比较，输出 P0-P100 状态分数，并用 P20、P50、P80 划分宽松、中性偏松、中性偏紧和收紧。',
  },
]

const detailSections = [
  {
    kicker: '公式',
    title: '核心计算',
    items: [
      '单指标压力 z = 方向因子 × (当前值 - 10 年中位数) / (1.4826 × MAD)。',
      '复合 z = 0.65 × 政策组均值 + 0.10 × 融资组均值 + 0.05 × 信用组均值 + 0.20 × 风险组均值。',
      '状态分位 = 当前复合 z 在过去 5 年复合 z 分布中的 percentile rank。',
    ],
  },
  {
    kicker: '数据',
    title: '更新频率',
    items: [
      'TGA、ON RRP、SRF、VIX、美元指数、HY 利差和实际利率通常按日更新。',
      'Fed 总资产、银行现金缓冲和 M2 是周频或月频序列，天然存在更长数据滞后。',
      '看板会展示 data lag，用来判断当前评分是否被某些慢频指标拖慢。',
    ],
  },
  {
    kicker: '限制',
    title: '使用边界',
    items: [
      'DLI 是同期压力测度，不是价格预测器。',
      '权重来自经济传导机制和公开方法论，不是机器学习自动优化。',
      '极端日内事件、数据修订和私有站点的未公开平滑逻辑，都会造成短期偏差。',
    ],
  },
]

const polarityLabel = (polarity: MacroPolarity) => (
  polarity === 'higherTightens' ? '越高越紧' : '越低越紧'
)

const formatWeight = (value: number) => `${value.toFixed(2)}%`
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
