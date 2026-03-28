<template>
  <section class="space-y-4">
    <div class="section-title">{{ $t('backtest.versionEditor') }}</div>
    <div class="grid grid-cols-2 gap-3">
      <div>
        <label class="label">{{ $t('backtest.strategyKey') }}</label>
        <input v-model="panel.versionDraft.key" class="input" type="text" />
      </div>
      <div>
        <label class="label">{{ $t('backtest.versionName') }}</label>
        <input v-model="panel.versionDraft.name" class="input" type="text" />
      </div>
    </div>
    <div class="grid grid-cols-2 gap-3">
      <div>
        <label class="label">{{ $t('backtest.template') }}</label>
        <select v-model="panel.versionDraft.template" class="input" @change="panel.syncVersionDraftTemplate">
          <option value="">{{ $t('backtest.customTemplateMode') }}</option>
          <option v-for="item in panel.templates" :key="item?.template ?? String(item)" :value="item?.template">
            {{ item?.name ?? item?.template ?? '-' }}
          </option>
        </select>
      </div>
      <div>
        <label class="label">{{ $t('backtest.category') }}</label>
        <input :value="panel.categoryLabel(panel.versionDraft.category)" class="input" type="text" readonly />
      </div>
    </div>
    <div>
      <label class="label">{{ $t('backtest.description') }}</label>
      <input v-model="panel.versionDraft.description" class="input" type="text" />
    </div>
    <div>
      <label class="label">{{ $t('backtest.notes') }}</label>
      <input v-model="panel.versionDraft.notes" class="input" type="text" />
    </div>

    <div class="flex flex-wrap gap-2">
      <button class="btn-secondary px-3" @click="panel.startBlankBuilder">{{ $t('backtest.startBlankBuilder') }}</button>
      <button class="btn-secondary px-3" @click="panel.toggleIndicatorCreator">{{ $t('backtest.indicatorRegistry') }}</button>
      <button class="btn-secondary px-3" @click="panel.toggleTemplateCreator">{{ $t('backtest.templateCreator') }}</button>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { BacktestVersionMetaPanel } from '@/modules/backtest/editorViewTypes'

const props = defineProps<{ panel: BacktestVersionMetaPanel }>()
const panel = props.panel
</script>

<style scoped>
.label { @apply block text-gray-500 dark:text-gray-400 text-xs font-bold mb-1; }
.input { @apply w-full bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-gray-900 dark:text-white outline-none focus:border-blue-500 transition-colors; }
.btn-secondary { @apply bg-gray-100 hover:bg-gray-200 dark:bg-gray-900 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-200 py-2 rounded-lg font-bold transition border border-gray-200 dark:border-gray-700; }
.section-title { @apply text-sm font-bold text-gray-900 dark:text-white; }
</style>
