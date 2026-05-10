<template>
  <div class="app-page">
    <div class="mx-auto flex max-w-5xl flex-col gap-6 px-4 py-8 sm:px-6 lg:px-8 lg:py-10">
      <div>
        <h2 class="app-title">{{ $t('settings.title') }}</h2>
      </div>

      <section class="app-panel p-6">
        <div class="grid gap-4 md:grid-cols-3">
          <label class="block">
            <span class="mb-1 block text-xs font-bold uppercase tracking-wide text-stone-500 dark:text-gray-400">{{ $t('settings.language') }}</span>
            <AppLanguageSelect />
          </label>
          <label class="block">
            <span class="mb-1 block text-xs font-bold uppercase tracking-wide text-stone-500 dark:text-gray-400">{{ $t('settings.timezone') }}</span>
            <AppTimezoneSelect />
          </label>
          <label class="block">
            <span class="mb-1 block text-xs font-bold uppercase tracking-wide text-stone-500 dark:text-gray-400">{{ $t('settings.currency') }}</span>
            <AppCurrencySelect />
          </label>
        </div>
        <div class="mt-4 text-sm text-gray-500 dark:text-gray-400">
          {{ $t('settings.currencyRate') }}: {{ ratesAreFallback ? $t('settings.currencyFallback') : formatDateTime(ratesUpdatedAt, { hour12: false }) }}
        </div>
      </section>

      <section class="app-panel p-6">
        <div class="mb-6 flex items-center justify-between gap-4">
          <div>
            <h3 class="app-section-title">大模型提供商</h3>
            <p class="app-muted mt-1 text-sm">用于 AI 分析和 AI 多空判断。</p>
          </div>
          <span
            class="px-3 py-1 text-xs font-semibold"
            :class="form.apiKeySet ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300' : 'bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-300'"
          >
            {{ form.apiKeySet ? 'API Key 已设置' : 'API Key 未设置' }}
          </span>
        </div>

        <div class="grid gap-5 md:grid-cols-2">
          <label class="space-y-2">
            <span class="text-sm font-medium text-gray-700 dark:text-gray-300">平台</span>
            <select v-model="form.provider" class="input" @change="handleProviderChange">
              <option v-for="preset in presets" :key="preset.id" :value="preset.id">
                {{ preset.label }}
              </option>
            </select>
          </label>

          <label class="space-y-2">
            <span class="text-sm font-medium text-gray-700 dark:text-gray-300">API Key</span>
            <input
              v-model.trim="apiKeyDraft"
              class="input"
              type="password"
              autocomplete="off"
              :placeholder="form.apiKeyPreview || '请输入 API Key'"
            />
          </label>

          <label class="space-y-2">
            <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Base URL</span>
            <input
              v-model.trim="form.baseUrl"
              class="input"
              type="text"
              :disabled="!isCustomProvider"
            />
          </label>

          <label class="space-y-2">
            <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Model ID</span>
            <input
              v-model.trim="form.modelId"
              class="input"
              type="text"
              :disabled="!isCustomProvider"
            />
          </label>
        </div>

        <label v-if="form.provider === 'deepseek'" class="mt-5 flex items-center justify-between border border-[#e4ded3] px-4 py-3 dark:border-gray-700">
          <span>
            <span class="block text-sm font-medium text-gray-900 dark:text-white">推理模式</span>
            <span class="block text-xs text-gray-500 dark:text-gray-400">
              {{ form.reasoningEnabled ? 'deepseek-reasoner' : 'deepseek-chat' }}
            </span>
          </span>
          <input v-model="form.reasoningEnabled" class="h-5 w-5" type="checkbox" @change="applyProviderPreset" />
        </label>

        <div class="mt-6 flex items-center gap-3">
          <button
            class="app-button-primary px-4 py-2"
            :disabled="saving || !canSave"
            @click="saveConfig"
          >
            {{ saving ? '保存中...' : '保存配置' }}
          </button>
          <span v-if="message" class="text-sm text-emerald-600 dark:text-emerald-300">{{ message }}</span>
          <span v-if="error" class="text-sm text-rose-600 dark:text-rose-300">{{ error }}</span>
        </div>
      </section>

      <section class="app-panel p-6">
        <div class="mb-6 flex items-center justify-between gap-4">
          <div>
            <h3 class="app-section-title">FRED 数据源</h3>
            <p class="app-muted mt-1 text-sm">用于美债收益率、联邦基金利率和宏观指数数据。</p>
          </div>
          <span
            class="px-3 py-1 text-xs font-semibold"
            :class="fredForm.apiKeySet ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300' : 'bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-300'"
          >
            {{ fredForm.apiKeySet ? 'API Key 已设置' : 'API Key 未设置' }}
          </span>
        </div>

        <div class="grid gap-5 md:grid-cols-[1fr_auto] md:items-end">
          <label class="space-y-2">
            <span class="text-sm font-medium text-gray-700 dark:text-gray-300">FRED API Key</span>
            <input
              v-model.trim="fredApiKeyDraft"
              class="input"
              type="password"
              autocomplete="off"
              :placeholder="fredForm.apiKeyPreview || '请输入 FRED API Key'"
            />
          </label>

          <button
            class="app-button-primary px-4 py-2"
            :disabled="fredSaving || !canSaveFred"
            @click="saveFredConfig"
          >
            {{ fredSaving ? '保存中...' : '保存' }}
          </button>
        </div>

        <div class="mt-3 flex items-center gap-3 text-sm">
          <span class="text-gray-500 dark:text-gray-400">来源: {{ fredForm.source }}</span>
          <span v-if="fredMessage" class="text-emerald-600 dark:text-emerald-300">{{ fredMessage }}</span>
          <span v-if="fredError" class="text-rose-600 dark:text-rose-300">{{ fredError }}</span>
        </div>
      </section>

      <section class="app-panel p-6">
        <div class="grid gap-3 text-sm text-stone-600 dark:text-gray-400 md:grid-cols-2">
          <div>{{ $t('settings.env') }}: {{ $t('settings.production') }}</div>
          <div>{{ $t('settings.version') }}: 2.0.0 (Vue + FastAPI)</div>
          <div>{{ $t('settings.db') }}: {{ systemConfig?.runtime?.database_engine || '-' }}</div>
          <div>{{ $t('settings.cache') }}: {{ systemConfig?.runtime?.cache_backend || '-' }}</div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
defineOptions({ name: 'Settings' })

import AppCurrencySelect from '@/components/AppCurrencySelect.vue'
import AppLanguageSelect from '@/components/AppLanguageSelect.vue'
import AppTimezoneSelect from '@/components/AppTimezoneSelect.vue'
import { useDateTime } from '@/composables/useDateTime'
import { useMoney } from '@/composables/useMoney'
import { useSystemSettingsPage } from '@/modules/system'

const { ratesAreFallback, ratesUpdatedAt } = useMoney()
const { formatDateTime } = useDateTime()
const {
  systemConfig,
  presets,
  apiKeyDraft,
  fredApiKeyDraft,
  saving,
  fredSaving,
  message,
  error,
  fredMessage,
  fredError,
  form,
  fredForm,
  isCustomProvider,
  canSave,
  canSaveFred,
  applyProviderPreset,
  handleProviderChange,
  saveConfig,
  saveFredConfig,
} = useSystemSettingsPage()
</script>

<style scoped>
.input {
  @apply w-full border bg-white px-3 py-2 text-sm font-semibold text-stone-900 outline-none transition focus:border-emerald-700 disabled:cursor-not-allowed disabled:bg-stone-100 disabled:text-stone-500 dark:border-gray-700 dark:bg-gray-900 dark:text-white dark:disabled:bg-gray-950 dark:disabled:text-gray-500;
  border-color: #e4ded3;
}
</style>
