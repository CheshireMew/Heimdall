<template>
  <div v-if="panel.editorContract && panel.versionDraft.config && (panel.editorTemplate || panel.useGlobalIndicatorCatalog)" class="grid grid-cols-1 gap-4 xl:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
    <div class="space-y-4">
      <div class="editor-section">
        <div class="section-title">{{ $t('backtest.executionConfig') }}</div>
        <div class="grid grid-cols-1 gap-3 md:grid-cols-2">
          <div>
            <label class="label">{{ $t('backtest.marketType') }}</label>
            <select v-model="panel.versionDraft.config.execution.market_type" class="input" @change="panel.syncExecutionConfig">
              <option v-for="item in panel.editorContract.market_type_options" :key="item.key" :value="item.key">
                {{ item.label }}
              </option>
            </select>
          </div>
          <div>
            <label class="label">{{ $t('backtest.positionDirection') }}</label>
            <select v-model="panel.versionDraft.config.execution.direction" class="input" :disabled="panel.versionDraft.config.execution.market_type === 'spot'">
              <option v-for="item in panel.editorContract.direction_options" :key="item.key" :value="item.key">
                {{ item.label }}
              </option>
            </select>
          </div>
        </div>
        <p class="text-xs text-gray-500 dark:text-gray-400">{{ $t('backtest.executionConfigHint') }}</p>
      </div>

      <div class="editor-section">
        <div class="flex items-center justify-between gap-3">
          <div class="section-title">{{ $t('backtest.indicatorConfig') }}</div>
          <div class="flex gap-2">
            <select v-model="panel.newIndicatorType" class="input !w-[180px]">
              <option v-for="indicator in panel.availableIndicators" :key="indicator?.key ?? String(indicator)" :value="indicator?.key">
                {{ indicator?.name ?? indicator?.key ?? '-' }}
              </option>
            </select>
            <button class="btn-secondary px-3" @click="panel.addIndicator">{{ $t('backtest.addIndicator') }}</button>
          </div>
        </div>
        <div v-for="indicator in panel.indicatorCards" :key="indicator.id" class="editor-card space-y-3">
          <div class="flex items-center justify-between gap-3">
            <div>
              <div class="font-semibold text-gray-900 dark:text-white">{{ indicator.label }}</div>
              <div class="text-xs text-gray-500 dark:text-gray-400">{{ indicator.typeLabel }} · {{ indicator.timeframeLabel }}</div>
            </div>
            <button class="btn-danger" @click="panel.removeIndicator(indicator.id)">{{ $t('backtest.remove') }}</button>
          </div>
          <div>
            <label class="label">{{ $t('backtest.indicatorTimeframe') }}</label>
            <select v-model="panel.versionDraft.config.indicators[indicator.id].timeframe" class="input">
              <option v-for="item in panel.editorContract.timeframe_options" :key="item.key" :value="item.key">
                {{ item.label }}
              </option>
            </select>
          </div>
          <div class="grid grid-cols-1 gap-3 md:grid-cols-2">
            <div v-for="param in indicator.params" :key="param?.key ?? String(param)">
              <label v-if="param.type !== 'bool'" class="label">{{ param.label }}</label>
              <input
                v-if="param.type !== 'bool'"
                v-model.number="panel.versionDraft.config.indicators[indicator.id].params[param.key]"
                class="input"
                type="number"
                :min="param.min ?? undefined"
                :max="param.max ?? undefined"
                :step="param.step ?? undefined"
              />
              <label v-else class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-300">
                <input v-model="panel.versionDraft.config.indicators[indicator.id].params[param.key]" type="checkbox" />
                <span>{{ param.label }}</span>
              </label>
            </div>
          </div>
        </div>
      </div>

      <div class="rounded-lg border border-gray-200 bg-white p-3 dark:border-gray-700 dark:bg-gray-900/50">
        <div class="text-xs font-bold uppercase tracking-wide text-gray-500 dark:text-gray-400">{{ $t('backtest.templateRules') }}</div>
        <div class="mt-2 text-sm text-gray-700 dark:text-gray-200">
          <div class="font-semibold">{{ $t('backtest.availableIndicators') }}</div>
          <div class="mt-1">{{ panel.availableIndicators.map((item) => item?.name || item?.key || '-').join(' / ') || '-' }}</div>
        </div>
        <div class="mt-3 text-sm text-gray-700 dark:text-gray-200">
          <div class="font-semibold">{{ $t('backtest.availableOperators') }}</div>
          <div class="mt-1">{{ panel.operatorOptions.map((item) => item?.label || item?.key || '-').join(' / ') || '-' }}</div>
        </div>
        <div class="mt-3 text-sm text-gray-700 dark:text-gray-200">
          <div class="font-semibold">{{ $t('backtest.groupLogic') }}</div>
          <div class="mt-1">{{ panel.groupLogicOptions.map((item) => item?.label || item?.key || '-').join(' / ') || '-' }}</div>
        </div>
      </div>
    </div>

    <div class="space-y-4">
      <div class="editor-section space-y-4">
        <div class="section-title">{{ $t('backtest.regimeBuilder') }}</div>

        <div class="editor-card space-y-3">
          <div class="flex items-center justify-between gap-3">
            <div>
              <div class="font-semibold text-gray-900 dark:text-white">{{ panel.versionDraft.config.trend.label || $t('backtest.trendBranch') }}</div>
              <div class="text-xs text-gray-500 dark:text-gray-400">{{ $t('backtest.trendBranchHint') }}</div>
            </div>
            <label class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-300">
              <input v-model="panel.versionDraft.config.trend.enabled" type="checkbox" />
              <span>{{ $t('backtest.enabled') }}</span>
            </label>
          </div>
          <RuleTreeEditor
            :editor-contract="panel.editorContract"
            :node="panel.versionDraft.config.trend.regime"
            :title="$t('backtest.regimeRules')"
            :source-options="panel.sourceOptions"
            :indicator-source-options="panel.indicatorSourceOptions"
            :operator-options="panel.operatorOptions"
            :group-logic-options="panel.groupLogicOptions"
          />
          <RuleTreeEditor
            :editor-contract="panel.editorContract"
            :node="panel.versionDraft.config.trend.long_entry"
            :title="$t('backtest.longEntryRules')"
            :source-options="panel.sourceOptions"
            :indicator-source-options="panel.indicatorSourceOptions"
            :operator-options="panel.operatorOptions"
            :group-logic-options="panel.groupLogicOptions"
          />
          <RuleTreeEditor
            :editor-contract="panel.editorContract"
            :node="panel.versionDraft.config.trend.long_exit"
            :title="$t('backtest.longExitRules')"
            :source-options="panel.sourceOptions"
            :indicator-source-options="panel.indicatorSourceOptions"
            :operator-options="panel.operatorOptions"
            :group-logic-options="panel.groupLogicOptions"
          />
          <RuleTreeEditor
            v-if="panel.versionDraft.config.execution.direction === 'long_short'"
            :editor-contract="panel.editorContract"
            :node="panel.versionDraft.config.trend.short_entry"
            :title="$t('backtest.shortEntryRules')"
            :source-options="panel.sourceOptions"
            :indicator-source-options="panel.indicatorSourceOptions"
            :operator-options="panel.operatorOptions"
            :group-logic-options="panel.groupLogicOptions"
          />
          <RuleTreeEditor
            v-if="panel.versionDraft.config.execution.direction === 'long_short'"
            :editor-contract="panel.editorContract"
            :node="panel.versionDraft.config.trend.short_exit"
            :title="$t('backtest.shortExitRules')"
            :source-options="panel.sourceOptions"
            :indicator-source-options="panel.indicatorSourceOptions"
            :operator-options="panel.operatorOptions"
            :group-logic-options="panel.groupLogicOptions"
          />
        </div>

        <div class="editor-card space-y-3">
          <div class="flex items-center justify-between gap-3">
            <div>
              <div class="font-semibold text-gray-900 dark:text-white">{{ panel.versionDraft.config.range.label || $t('backtest.rangeBranch') }}</div>
              <div class="text-xs text-gray-500 dark:text-gray-400">{{ $t('backtest.rangeBranchHint') }}</div>
            </div>
            <label class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-300">
              <input v-model="panel.versionDraft.config.range.enabled" type="checkbox" />
              <span>{{ $t('backtest.enabled') }}</span>
            </label>
          </div>
          <RuleTreeEditor
            :editor-contract="panel.editorContract"
            :node="panel.versionDraft.config.range.regime"
            :title="$t('backtest.regimeRules')"
            :source-options="panel.sourceOptions"
            :indicator-source-options="panel.indicatorSourceOptions"
            :operator-options="panel.operatorOptions"
            :group-logic-options="panel.groupLogicOptions"
          />
          <RuleTreeEditor
            :editor-contract="panel.editorContract"
            :node="panel.versionDraft.config.range.long_entry"
            :title="$t('backtest.longEntryRules')"
            :source-options="panel.sourceOptions"
            :indicator-source-options="panel.indicatorSourceOptions"
            :operator-options="panel.operatorOptions"
            :group-logic-options="panel.groupLogicOptions"
          />
          <RuleTreeEditor
            :editor-contract="panel.editorContract"
            :node="panel.versionDraft.config.range.long_exit"
            :title="$t('backtest.longExitRules')"
            :source-options="panel.sourceOptions"
            :indicator-source-options="panel.indicatorSourceOptions"
            :operator-options="panel.operatorOptions"
            :group-logic-options="panel.groupLogicOptions"
          />
          <RuleTreeEditor
            v-if="panel.versionDraft.config.execution.direction === 'long_short'"
            :editor-contract="panel.editorContract"
            :node="panel.versionDraft.config.range.short_entry"
            :title="$t('backtest.shortEntryRules')"
            :source-options="panel.sourceOptions"
            :indicator-source-options="panel.indicatorSourceOptions"
            :operator-options="panel.operatorOptions"
            :group-logic-options="panel.groupLogicOptions"
          />
          <RuleTreeEditor
            v-if="panel.versionDraft.config.execution.direction === 'long_short'"
            :editor-contract="panel.editorContract"
            :node="panel.versionDraft.config.range.short_exit"
            :title="$t('backtest.shortExitRules')"
            :source-options="panel.sourceOptions"
            :indicator-source-options="panel.indicatorSourceOptions"
            :operator-options="panel.operatorOptions"
            :group-logic-options="panel.groupLogicOptions"
          />
        </div>
      </div>
      <div class="editor-section">
        <div class="section-title">{{ $t('backtest.riskPanel') }}</div>
        <div class="grid grid-cols-1 gap-3 md:grid-cols-2">
          <div>
            <label class="label">{{ $t('backtest.stoplossLabel') }}</label>
            <input v-model.number="panel.versionDraft.config.risk.stoploss" class="input" type="number" step="0.001" />
          </div>
          <div class="editor-card space-y-2">
            <label class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-300">
              <input v-model="panel.versionDraft.config.risk.trailing.enabled" type="checkbox" />
              <span>{{ $t('backtest.trailingStop') }}</span>
            </label>
            <div class="grid grid-cols-2 gap-2">
              <div>
                <label class="label">{{ $t('backtest.trailingPositive') }}</label>
                <input v-model.number="panel.versionDraft.config.risk.trailing.positive" class="input" type="number" step="0.001" />
              </div>
              <div>
                <label class="label">{{ $t('backtest.trailingOffset') }}</label>
                <input v-model.number="panel.versionDraft.config.risk.trailing.offset" class="input" type="number" step="0.001" />
              </div>
            </div>
            <label class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-300">
              <input v-model="panel.versionDraft.config.risk.trailing.only_offset_reached" type="checkbox" />
              <span>{{ $t('backtest.trailingOffsetOnly') }}</span>
            </label>
          </div>
        </div>
        <div class="editor-card space-y-3">
          <div class="flex items-center justify-between gap-3">
            <div class="font-semibold text-gray-900 dark:text-white">{{ $t('backtest.roiTargets') }}</div>
            <button class="btn-secondary px-3" @click="panel.addRoiTarget">{{ $t('backtest.addRoiTarget') }}</button>
          </div>
          <div v-for="target in panel.versionDraft.config.risk.roi_targets" :key="target.id" class="grid grid-cols-[1fr_1fr_auto] gap-2">
            <input v-model.number="target.minutes" class="input" type="number" min="0" step="1" />
            <input v-model.number="target.profit" class="input" type="number" step="0.001" />
            <button class="btn-danger" @click="panel.removeRoiTarget(target.id)">{{ $t('backtest.remove') }}</button>
          </div>
        </div>
        <div class="editor-card space-y-3">
          <div class="flex items-center justify-between gap-3">
            <div class="font-semibold text-gray-900 dark:text-white">{{ $t('backtest.partialExits') }}</div>
            <button class="btn-secondary px-3" @click="panel.addPartialExit">{{ $t('backtest.addPartialExit') }}</button>
          </div>
          <div v-for="item in panel.versionDraft.config.risk.partial_exits" :key="item.id" class="grid grid-cols-[1fr_1fr_auto] gap-2">
            <input v-model.number="item.profit" class="input" type="number" step="0.001" />
            <input v-model.number="item.size_pct" class="input" type="number" min="1" max="100" step="1" />
            <button class="btn-danger" @click="panel.removePartialExit(item.id)">{{ $t('backtest.remove') }}</button>
          </div>
        </div>
      </div>

      <div class="editor-section">
        <div class="text-xs font-bold uppercase tracking-wide text-gray-500 dark:text-gray-400">{{ $t('backtest.parameterSpacePanel') }}</div>
        <div v-for="field in panel.optimizableTargets" :key="field.path">
          <label class="label">{{ field.label }}</label>
          <input v-model="panel.versionDraft.parameterSpaceValues[field.path]" class="input" type="text" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import RuleTreeEditor from '@/components/RuleTreeEditor.vue'
import type { BacktestStrategyBuilderPanel } from '@/modules/backtest/editorViewTypes'

const props = defineProps<{ panel: BacktestStrategyBuilderPanel }>()
const panel = props.panel
</script>

<style scoped>
.label { @apply block text-gray-500 dark:text-gray-400 text-xs font-bold mb-1; }
.input { @apply w-full bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-gray-900 dark:text-white outline-none focus:border-blue-500 transition-colors; }
.btn-secondary { @apply bg-gray-100 hover:bg-gray-200 dark:bg-gray-900 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-200 py-2 rounded-lg font-bold transition border border-gray-200 dark:border-gray-700; }
.btn-danger { @apply bg-red-50 hover:bg-red-100 dark:bg-red-950/40 dark:hover:bg-red-900/40 text-red-600 dark:text-red-300 px-3 py-2 rounded-lg font-bold transition border border-red-200 dark:border-red-800; }
.section-title { @apply text-sm font-bold text-gray-900 dark:text-white; }
.editor-section { @apply rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900/50 p-3 space-y-3; }
.editor-card { @apply rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/40 p-3; }
</style>
