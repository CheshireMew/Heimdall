<template>
  <div v-if="panel.show" class="editor-section">
    <div class="section-title">{{ $t('backtest.templateCreator') }}</div>
    <div class="grid grid-cols-1 gap-3 md:grid-cols-2">
      <div>
        <label class="label">{{ $t('backtest.templateKey') }}</label>
        <input v-model="panel.templateDraft.key" class="input" type="text" />
      </div>
      <div>
        <label class="label">{{ $t('backtest.templateName') }}</label>
        <input v-model="panel.templateDraft.name" class="input" type="text" />
      </div>
    </div>
    <div class="grid grid-cols-1 gap-3 md:grid-cols-2">
      <div>
        <label class="label">{{ $t('backtest.category') }}</label>
        <input v-model="panel.templateDraft.category" class="input" type="text" />
      </div>
      <div>
        <label class="label">{{ $t('backtest.description') }}</label>
        <input v-model="panel.templateDraft.description" class="input" type="text" />
      </div>
    </div>
    <div>
      <label class="label">{{ $t('backtest.allowedIndicators') }}</label>
      <div class="grid grid-cols-2 gap-2 text-sm text-gray-700 dark:text-gray-200 md:grid-cols-3">
        <label v-for="indicator in panel.indicators" :key="indicator?.key ?? String(indicator)" class="flex items-center gap-2">
          <input :checked="panel.templateDraft.indicator_keys.includes(indicator?.key)" type="checkbox" @change="indicator?.key && panel.toggleTemplateIndicator(indicator.key)" />
          <span>{{ indicator?.name ?? indicator?.key ?? '-' }}</span>
        </label>
      </div>
    </div>
    <button class="btn-primary w-full" @click="panel.createTemplate">{{ $t('backtest.saveTemplate') }}</button>
  </div>
</template>

<script setup lang="ts">
import type { BacktestTemplateCreatorPanel } from '@/modules/backtest/editorViewTypes'

const props = defineProps<{ panel: BacktestTemplateCreatorPanel }>()
const panel = props.panel
</script>

<style scoped>
.label { @apply block text-gray-500 dark:text-gray-400 text-xs font-bold mb-1; }
.input { @apply w-full bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-gray-900 dark:text-white outline-none focus:border-blue-500 transition-colors; }
.btn-primary { @apply bg-blue-600 hover:bg-blue-500 text-white py-2 rounded-lg font-bold transition disabled:opacity-50; }
.section-title { @apply text-sm font-bold text-gray-900 dark:text-white; }
.editor-section { @apply rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900/50 p-3 space-y-3; }
</style>
