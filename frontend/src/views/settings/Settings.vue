<template>
  <div class="h-full overflow-y-auto p-6">
    <div class="mx-auto flex max-w-5xl flex-col gap-6">
      <div>
        <h2 class="text-2xl font-bold text-gray-900 dark:text-white">{{ $t('settings.title') }}</h2>
      </div>

      <section class="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
        <div class="grid gap-4 md:grid-cols-2">
          <label class="block">
            <span class="mb-1 block text-xs font-bold uppercase text-gray-500 dark:text-gray-400">{{ $t('settings.timezone') }}</span>
            <AppTimezoneSelect />
          </label>
          <label class="block">
            <span class="mb-1 block text-xs font-bold uppercase text-gray-500 dark:text-gray-400">{{ $t('settings.currency') }}</span>
            <AppCurrencySelect />
          </label>
        </div>
        <div class="mt-4 text-sm text-gray-500 dark:text-gray-400">
          {{ $t('settings.currencyRate') }}: {{ ratesAreFallback ? $t('settings.currencyFallback') : formatDateTime(ratesUpdatedAt, { hour12: false }) }}
        </div>
      </section>

      <section class="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
        <div class="mb-6 flex items-center justify-between gap-4">
          <div>
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">大模型提供商</h3>
            <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">用于 AI 分析和 AI 多空判断。</p>
          </div>
          <span
            class="rounded-lg px-3 py-1 text-xs font-semibold"
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

        <label v-if="form.provider === 'deepseek'" class="mt-5 flex items-center justify-between rounded-lg border border-gray-200 px-4 py-3 dark:border-gray-700">
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
            class="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
            :disabled="saving || !canSave"
            @click="saveConfig"
          >
            {{ saving ? '保存中...' : '保存配置' }}
          </button>
          <span v-if="message" class="text-sm text-emerald-600 dark:text-emerald-300">{{ message }}</span>
          <span v-if="error" class="text-sm text-rose-600 dark:text-rose-300">{{ error }}</span>
        </div>
      </section>

      <section class="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
        <div class="grid gap-3 text-sm text-gray-600 dark:text-gray-400 md:grid-cols-2">
          <div>{{ $t('settings.env') }}: {{ $t('settings.production') }}</div>
          <div>{{ $t('settings.version') }}: 2.0.0 (Vue + FastAPI)</div>
          <div>{{ $t('settings.db') }}: PostgreSQL</div>
          <div>{{ $t('settings.cache') }}: Redis</div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
defineOptions({ name: 'Settings' })

import { computed, onMounted, reactive, ref } from 'vue'
import request from '@/api/request'
import AppCurrencySelect from '@/components/AppCurrencySelect.vue'
import AppTimezoneSelect from '@/components/AppTimezoneSelect.vue'
import { useDateTime } from '@/composables/useDateTime'
import { useMoney } from '@/composables/useMoney'

const { ratesAreFallback, ratesUpdatedAt } = useMoney()
const { formatDateTime } = useDateTime()

const presets = ref([])
const apiKeyDraft = ref('')
const saving = ref(false)
const message = ref('')
const error = ref('')
const form = reactive({
  provider: 'deepseek',
  apiKeySet: false,
  apiKeyPreview: '',
  baseUrl: '',
  modelId: '',
  reasoningEnabled: false,
})

const selectedPreset = computed(() => presets.value.find(item => item.id === form.provider))
const isCustomProvider = computed(() => form.provider === 'custom')
const canSave = computed(() => {
  const hasApiKey = Boolean(apiKeyDraft.value || form.apiKeySet)
  if (!hasApiKey) return false
  if (isCustomProvider.value) return Boolean(form.baseUrl && form.modelId)
  return true
})

const applyConfig = (config) => {
  presets.value = config.presets || []
  form.provider = config.provider || 'deepseek'
  form.apiKeySet = Boolean(config.apiKeySet)
  form.apiKeyPreview = config.apiKeyPreview || ''
  form.baseUrl = config.baseUrl || ''
  form.modelId = config.modelId || ''
  form.reasoningEnabled = Boolean(config.reasoningEnabled)
  apiKeyDraft.value = ''
}

const applyProviderPreset = () => {
  if (form.provider !== 'deepseek') form.reasoningEnabled = false
  if (isCustomProvider.value) {
    form.baseUrl = ''
    form.modelId = ''
    return
  }
  const preset = selectedPreset.value
  if (!preset) return
  form.baseUrl = preset.baseUrl
  form.modelId = form.provider === 'deepseek' && form.reasoningEnabled ? 'deepseek-reasoner' : preset.defaultModel
}

const handleProviderChange = () => {
  form.apiKeySet = false
  form.apiKeyPreview = ''
  apiKeyDraft.value = ''
  applyProviderPreset()
}

const loadConfig = async () => {
  error.value = ''
  try {
    const response = await request.get('/llm-config')
    applyConfig(response.data)
  } catch (err) {
    console.error('Load LLM config failed', err)
    error.value = '加载配置失败'
  }
}

const saveConfig = async () => {
  if (!canSave.value) return
  saving.value = true
  message.value = ''
  error.value = ''
  try {
    const response = await request.put('/llm-config', {
      provider: form.provider,
      apiKey: apiKeyDraft.value || null,
      baseUrl: form.baseUrl,
      modelId: form.modelId,
      reasoningEnabled: form.reasoningEnabled,
    })
    applyConfig(response.data)
    message.value = '配置已保存'
  } catch (err) {
    console.error('Save LLM config failed', err)
    error.value = '保存配置失败'
  } finally {
    saving.value = false
  }
}

onMounted(loadConfig)
</script>

<style scoped>
.input {
  @apply w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-semibold text-gray-900 outline-none transition focus:border-blue-500 disabled:cursor-not-allowed disabled:bg-gray-100 disabled:text-gray-500 dark:border-gray-700 dark:bg-gray-900 dark:text-white dark:disabled:bg-gray-950 dark:disabled:text-gray-500;
}
</style>
