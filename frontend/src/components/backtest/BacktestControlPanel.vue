<template>
  <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 transition-colors">
    <h2 class="text-xl font-bold mb-4 text-gray-900 dark:text-white">{{ $t('backtest.new') }}</h2>
    <div class="space-y-5">
      <section class="space-y-3">
        <div>
          <label class="label">{{ $t('backtest.strategy') }}</label>
          <select v-model="page.config.strategy_key" class="input" @change="page.syncStrategyVersion">
            <option v-for="item in page.strategies" :key="item.key" :value="item.key">{{ item.name }}</option>
          </select>
        </div>
        <div>
          <label class="label">{{ $t('backtest.version') }}</label>
          <select v-model="page.config.strategy_version" class="input">
            <option v-for="item in page.selectedStrategyVersions" :key="item.version" :value="item.version">
              v{{ item.version }} · {{ item.name }}
            </option>
          </select>
        </div>
        <div
          v-if="page.selectedStrategy"
          class="rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/40 px-3 py-3 text-sm text-gray-600 dark:text-gray-300"
        >
          <div class="font-semibold text-gray-900 dark:text-white">{{ page.selectedStrategy.name }}</div>
          <div class="mt-1">{{ page.selectedStrategy.description || '-' }}</div>
          <div class="mt-2 text-xs text-gray-500 dark:text-gray-400">
            {{ $t('backtest.selectedVersion') }}: v{{ page.config.strategy_version }} · {{ page.selectedVersion?.name || '-' }}
          </div>
        </div>
        <div class="flex gap-2">
          <button class="btn-secondary flex-1" :disabled="!page.editorReady" @click="page.fillVersionDraft">{{ $t('backtest.fillFromCurrent') }}</button>
          <button class="btn-secondary flex-1" :disabled="!page.editorReady" @click="page.showVersionEditor = !page.showVersionEditor">
            {{ page.showVersionEditor ? $t('backtest.hideVersionEditor') : $t('backtest.showVersionEditor') }}
          </button>
        </div>
      </section>

      <BacktestVersionEditor :page="page" />
      <BacktestRunForm :page="page" />
    </div>
  </div>
</template>

<script setup lang="ts">
import BacktestRunForm from '@/components/backtest/BacktestRunForm.vue'
import BacktestVersionEditor from '@/components/backtest/BacktestVersionEditor.vue'
import type { BacktestPageState } from '@/modules/backtest/useBacktestPage'

const props = defineProps<{ page: BacktestPageState }>()
const page = props.page
</script>

<style scoped>
.label { @apply block text-gray-500 dark:text-gray-400 text-xs font-bold mb-1; }
.input { @apply w-full bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-gray-900 dark:text-white outline-none focus:border-blue-500 transition-colors; }
.btn-secondary { @apply bg-gray-100 hover:bg-gray-200 dark:bg-gray-900 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-200 py-2 rounded-lg font-bold transition border border-gray-200 dark:border-gray-700; }
</style>
