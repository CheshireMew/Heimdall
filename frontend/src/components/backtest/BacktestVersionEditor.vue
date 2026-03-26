<template>
  <div v-if="page.showVersionEditor && page.versionDraft.config" class="rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/40 p-4 space-y-4">
    <div class="section-title">{{ $t('backtest.versionEditor') }}</div>
    <div class="grid grid-cols-2 gap-3">
      <div>
        <label class="label">{{ $t('backtest.strategyKey') }}</label>
        <input v-model="page.versionDraft.key" class="input" type="text" />
      </div>
      <div>
        <label class="label">{{ $t('backtest.versionName') }}</label>
        <input v-model="page.versionDraft.name" class="input" type="text" />
      </div>
    </div>
    <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="label">{{ $t('backtest.template') }}</label>
          <select v-model="page.versionDraft.template" class="input" @change="page.syncVersionDraftTemplate">
            <option value="">{{ $t('backtest.customTemplateMode') }}</option>
            <option v-for="item in page.templates" :key="item?.template ?? String(item)" :value="item?.template">
              {{ item?.name ?? item?.template ?? '-' }}
            </option>
          </select>
        </div>
      <div>
        <label class="label">{{ $t('backtest.category') }}</label>
        <input :value="page.categoryLabel(page.versionDraft.category)" class="input" type="text" readonly />
      </div>
    </div>
    <div>
      <label class="label">{{ $t('backtest.description') }}</label>
      <input v-model="page.versionDraft.description" class="input" type="text" />
    </div>
    <div>
      <label class="label">{{ $t('backtest.notes') }}</label>
      <input v-model="page.versionDraft.notes" class="input" type="text" />
    </div>

    <div class="flex flex-wrap gap-2">
      <button class="btn-secondary px-3" @click="page.startBlankBuilder">{{ $t('backtest.startBlankBuilder') }}</button>
      <button class="btn-secondary px-3" @click="page.showIndicatorCreator = !page.showIndicatorCreator">{{ $t('backtest.indicatorRegistry') }}</button>
      <button class="btn-secondary px-3" @click="page.showTemplateCreator = !page.showTemplateCreator">{{ $t('backtest.templateCreator') }}</button>
    </div>

    <div v-if="page.showIndicatorCreator" class="editor-section">
      <div class="section-title">{{ $t('backtest.indicatorRegistry') }}</div>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div>
          <label class="label">{{ $t('backtest.indicatorKey') }}</label>
          <input v-model="page.indicatorDraft.key" class="input" type="text" />
        </div>
        <div>
          <label class="label">{{ $t('backtest.indicatorName') }}</label>
          <input v-model="page.indicatorDraft.name" class="input" type="text" />
        </div>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div>
          <label class="label">{{ $t('backtest.indicatorEngine') }}</label>
          <select v-model="page.indicatorDraft.engine_key" class="input" @change="page.syncIndicatorDraftEngine">
            <option v-for="engine in page.indicatorEngines" :key="engine?.key ?? String(engine)" :value="engine?.key">
              {{ engine?.name ?? engine?.key ?? '-' }}
            </option>
          </select>
        </div>
        <div>
          <label class="label">{{ $t('backtest.description') }}</label>
          <input v-model="page.indicatorDraft.description" class="input" type="text" />
        </div>
      </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div v-for="param in page.indicatorDraft.params" :key="param?.key ?? String(param)" class="editor-card space-y-2">
            <div class="font-semibold text-gray-900 dark:text-white">{{ param.label }}</div>
            <input v-model="param.label" class="input" type="text" />
          <div class="grid grid-cols-2 gap-2">
            <input v-model.number="param.default" class="input" type="number" step="0.1" />
            <input v-model.number="param.step" class="input" type="number" step="0.1" />
          </div>
          <div class="grid grid-cols-2 gap-2">
            <input v-model.number="param.min" class="input" type="number" step="0.1" />
            <input v-model.number="param.max" class="input" type="number" step="0.1" />
          </div>
        </div>
      </div>
      <button class="btn-primary w-full" @click="page.createIndicator">{{ $t('backtest.saveIndicator') }}</button>
    </div>

    <div v-if="page.showTemplateCreator" class="editor-section">
      <div class="section-title">{{ $t('backtest.templateCreator') }}</div>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div>
          <label class="label">{{ $t('backtest.templateKey') }}</label>
          <input v-model="page.templateDraft.key" class="input" type="text" />
        </div>
        <div>
          <label class="label">{{ $t('backtest.templateName') }}</label>
          <input v-model="page.templateDraft.name" class="input" type="text" />
        </div>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div>
          <label class="label">{{ $t('backtest.category') }}</label>
          <input v-model="page.templateDraft.category" class="input" type="text" />
        </div>
        <div>
          <label class="label">{{ $t('backtest.description') }}</label>
          <input v-model="page.templateDraft.description" class="input" type="text" />
        </div>
      </div>
      <div>
        <label class="label">{{ $t('backtest.allowedIndicators') }}</label>
        <div class="grid grid-cols-2 md:grid-cols-3 gap-2 text-sm text-gray-700 dark:text-gray-200">
          <label v-for="indicator in page.indicators" :key="indicator?.key ?? String(indicator)" class="flex items-center gap-2">
            <input :checked="page.templateDraft.indicator_keys.includes(indicator?.key)" type="checkbox" @change="indicator?.key && page.toggleTemplateIndicator(indicator.key)" />
            <span>{{ indicator?.name ?? indicator?.key ?? '-' }}</span>
          </label>
        </div>
      </div>
      <button class="btn-primary w-full" @click="page.createTemplate">{{ $t('backtest.saveTemplate') }}</button>
    </div>

    <div v-if="page.editorContract && page.versionDraft.config && (page.editorTemplate || page.useGlobalIndicatorCatalog)" class="grid grid-cols-1 xl:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)] gap-4">
      <div class="space-y-4">
        <div class="editor-section">
            <div class="flex items-center justify-between gap-3">
              <div class="section-title">{{ $t('backtest.indicatorConfig') }}</div>
              <div class="flex gap-2">
                <select v-model="page.newIndicatorType" class="input !w-[180px]">
                  <option v-for="indicator in page.availableIndicators" :key="indicator?.key ?? String(indicator)" :value="indicator?.key">
                    {{ indicator?.name ?? indicator?.key ?? '-' }}
                  </option>
                </select>
                <button class="btn-secondary px-3" @click="page.addIndicator">{{ $t('backtest.addIndicator') }}</button>
              </div>
            </div>
          <div v-for="indicator in page.indicatorCards" :key="indicator.id" class="editor-card space-y-3">
            <div class="flex items-center justify-between gap-3">
              <div>
                <div class="font-semibold text-gray-900 dark:text-white">{{ indicator.label }}</div>
                <div class="text-xs text-gray-500 dark:text-gray-400">{{ indicator.typeLabel }}</div>
              </div>
              <button class="btn-danger" @click="page.removeIndicator(indicator.id)">{{ $t('backtest.remove') }}</button>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div v-for="param in indicator.params" :key="param?.key ?? String(param)">
                <label v-if="param.type !== 'bool'" class="label">{{ param.label }}</label>
                <input
                  v-if="param.type !== 'bool'"
                  v-model.number="page.versionDraft.config.indicators[indicator.id].params[param.key]"
                  class="input"
                  type="number"
                  :min="param.min ?? undefined"
                  :max="param.max ?? undefined"
                  :step="param.step ?? undefined"
                />
                <label v-else class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-300">
                  <input v-model="page.versionDraft.config.indicators[indicator.id].params[param.key]" type="checkbox" />
                  <span>{{ param.label }}</span>
                </label>
              </div>
            </div>
          </div>
        </div>
        <div class="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900/50 p-3">
          <div class="text-xs font-bold uppercase tracking-wide text-gray-500 dark:text-gray-400">{{ $t('backtest.templateRules') }}</div>
          <div class="mt-2 text-sm text-gray-700 dark:text-gray-200">
            <div class="font-semibold">{{ $t('backtest.availableIndicators') }}</div>
            <div class="mt-1">{{ page.availableIndicators.map((item) => item?.name || item?.key || '-').join(' / ') || '-' }}</div>
          </div>
          <div class="mt-3 text-sm text-gray-700 dark:text-gray-200">
            <div class="font-semibold">{{ $t('backtest.availableOperators') }}</div>
            <div class="mt-1">{{ page.operatorOptions.map((item) => item?.label || item?.key || '-').join(' / ') || '-' }}</div>
          </div>
          <div class="mt-3 text-sm text-gray-700 dark:text-gray-200">
            <div class="font-semibold">{{ $t('backtest.groupLogic') }}</div>
            <div class="mt-1">{{ page.groupLogicOptions.map((item) => item?.label || item?.key || '-').join(' / ') || '-' }}</div>
          </div>
        </div>
      </div>

      <div class="space-y-4">
        <RuleTreeEditor
          :editor-contract="page.editorContract"
          :node="page.versionDraft.config.entry"
          :title="$t('backtest.entryRules')"
          :source-options="page.sourceOptions"
          :indicator-source-options="page.indicatorSourceOptions"
          :operator-options="page.operatorOptions"
          :group-logic-options="page.groupLogicOptions"
        />
        <RuleTreeEditor
          :editor-contract="page.editorContract"
          :node="page.versionDraft.config.exit"
          :title="$t('backtest.exitRules')"
          :source-options="page.sourceOptions"
          :indicator-source-options="page.indicatorSourceOptions"
          :operator-options="page.operatorOptions"
          :group-logic-options="page.groupLogicOptions"
        />
        <div class="editor-section">
          <div class="section-title">{{ $t('backtest.riskPanel') }}</div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label class="label">{{ $t('backtest.stoplossLabel') }}</label>
              <input v-model.number="page.versionDraft.config.risk.stoploss" class="input" type="number" step="0.001" />
            </div>
            <div class="editor-card space-y-2">
              <label class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-300">
                <input v-model="page.versionDraft.config.risk.trailing.enabled" type="checkbox" />
                <span>{{ $t('backtest.trailingStop') }}</span>
              </label>
              <div class="grid grid-cols-2 gap-2">
                <div>
                  <label class="label">{{ $t('backtest.trailingPositive') }}</label>
                  <input v-model.number="page.versionDraft.config.risk.trailing.positive" class="input" type="number" step="0.001" />
                </div>
                <div>
                  <label class="label">{{ $t('backtest.trailingOffset') }}</label>
                  <input v-model.number="page.versionDraft.config.risk.trailing.offset" class="input" type="number" step="0.001" />
                </div>
              </div>
              <label class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-300">
                <input v-model="page.versionDraft.config.risk.trailing.only_offset_reached" type="checkbox" />
                <span>{{ $t('backtest.trailingOffsetOnly') }}</span>
              </label>
            </div>
          </div>
          <div class="editor-card space-y-3">
            <div class="flex items-center justify-between gap-3">
              <div class="font-semibold text-gray-900 dark:text-white">{{ $t('backtest.roiTargets') }}</div>
              <button class="btn-secondary px-3" @click="page.addRoiTarget">{{ $t('backtest.addRoiTarget') }}</button>
            </div>
            <div v-for="target in page.versionDraft.config.risk.roi_targets" :key="target.id" class="grid grid-cols-[1fr_1fr_auto] gap-2">
              <input v-model.number="target.minutes" class="input" type="number" min="0" step="1" />
              <input v-model.number="target.profit" class="input" type="number" step="0.001" />
              <button class="btn-danger" @click="page.removeRoiTarget(target.id)">{{ $t('backtest.remove') }}</button>
            </div>
          </div>
          <div class="editor-card space-y-3">
            <div class="flex items-center justify-between gap-3">
              <div class="font-semibold text-gray-900 dark:text-white">{{ $t('backtest.partialExits') }}</div>
              <button class="btn-secondary px-3" @click="page.addPartialExit">{{ $t('backtest.addPartialExit') }}</button>
            </div>
            <div v-for="item in page.versionDraft.config.risk.partial_exits" :key="item.id" class="grid grid-cols-[1fr_1fr_auto] gap-2">
              <input v-model.number="item.profit" class="input" type="number" step="0.001" />
              <input v-model.number="item.size_pct" class="input" type="number" min="1" max="100" step="1" />
              <button class="btn-danger" @click="page.removePartialExit(item.id)">{{ $t('backtest.remove') }}</button>
            </div>
          </div>
        </div>
        <div class="editor-section">
          <div class="text-xs font-bold uppercase tracking-wide text-gray-500 dark:text-gray-400">{{ $t('backtest.parameterSpacePanel') }}</div>
          <div v-for="field in page.optimizableTargets" :key="field.path">
            <label class="label">{{ field.label }}</label>
            <input v-model="page.versionDraft.parameterSpaceValues[field.path]" class="input" type="text" />
          </div>
        </div>
      </div>
    </div>

    <label class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-300">
      <input v-model="page.versionDraft.make_default" type="checkbox" />
      <span>{{ $t('backtest.makeDefault') }}</span>
    </label>
    <button class="btn-primary w-full" @click="page.createStrategyVersion">{{ $t('backtest.saveVersion') }}</button>
  </div>
</template>

<script setup lang="ts">
import RuleTreeEditor from '@/components/RuleTreeEditor.vue'
import type { BacktestEditorPageState } from '@/modules/backtest/useBacktestEditorPage'

const props = defineProps<{ page: BacktestEditorPageState }>()
const page = props.page
</script>

<style scoped>
.label { @apply block text-gray-500 dark:text-gray-400 text-xs font-bold mb-1; }
.input { @apply w-full bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-gray-900 dark:text-white outline-none focus:border-blue-500 transition-colors; }
.btn-primary { @apply bg-blue-600 hover:bg-blue-500 text-white py-2 rounded-lg font-bold transition disabled:opacity-50; }
.btn-secondary { @apply bg-gray-100 hover:bg-gray-200 dark:bg-gray-900 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-200 py-2 rounded-lg font-bold transition border border-gray-200 dark:border-gray-700; }
.btn-danger { @apply bg-red-50 hover:bg-red-100 dark:bg-red-950/40 dark:hover:bg-red-900/40 text-red-600 dark:text-red-300 px-3 py-2 rounded-lg font-bold transition border border-red-200 dark:border-red-800; }
.section-title { @apply text-sm font-bold text-gray-900 dark:text-white; }
.editor-section { @apply rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900/50 p-3 space-y-3; }
.editor-card { @apply rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/40 p-3; }
</style>
