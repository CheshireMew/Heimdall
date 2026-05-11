import { computed, onMounted, reactive, ref } from 'vue'

import type {
  FredApiConfigResponse,
  LlmProviderConfigResponse,
  LlmProviderPresetResponse,
  SystemConfigResponse,
} from './contracts'
import { systemApi } from './api'

interface LlmConfigForm {
  provider: string
  apiKeySet: boolean
  apiKeyPreview: string
  baseUrl: string
  modelId: string
  reasoningEnabled: boolean
}

interface FredApiConfigForm {
  apiKeySet: boolean
  apiKeyPreview: string
  source: string
}

export const useSystemSettingsPage = () => {
  const systemConfig = ref<SystemConfigResponse | null>(null)
  const presets = ref<LlmProviderPresetResponse[]>([])
  const apiKeyDraft = ref('')
  const fredApiKeyDraft = ref('')
  const saving = ref(false)
  const fredSaving = ref(false)
  const message = ref('')
  const error = ref('')
  const fredMessage = ref('')
  const fredError = ref('')
  const form = reactive<LlmConfigForm>({
    provider: 'deepseek',
    apiKeySet: false,
    apiKeyPreview: '',
    baseUrl: '',
    modelId: '',
    reasoningEnabled: false,
  })
  const fredForm = reactive<FredApiConfigForm>({
    apiKeySet: false,
    apiKeyPreview: '',
    source: 'unset',
  })

  const selectedPreset = computed(() => presets.value.find((item) => item.id === form.provider) || null)
  const isCustomProvider = computed(() => form.provider === 'custom')
  const canSave = computed(() => {
    const hasApiKey = Boolean(apiKeyDraft.value || form.apiKeySet)
    if (!hasApiKey) return false
    if (isCustomProvider.value) return Boolean(form.baseUrl && form.modelId)
    return true
  })
  const canSaveFred = computed(() => Boolean(fredApiKeyDraft.value))

  const applyConfig = (config: LlmProviderConfigResponse) => {
    presets.value = config.presets || []
    form.provider = config.provider || 'deepseek'
    form.apiKeySet = Boolean(config.apiKeySet)
    form.apiKeyPreview = config.apiKeyPreview || ''
    form.baseUrl = config.baseUrl || ''
    form.modelId = config.modelId || ''
    form.reasoningEnabled = Boolean(config.reasoningEnabled)
    apiKeyDraft.value = ''
  }

  const applyFredConfig = (config: FredApiConfigResponse) => {
    fredForm.apiKeySet = Boolean(config.apiKeySet)
    fredForm.apiKeyPreview = config.apiKeyPreview || ''
    fredForm.source = config.source || 'unset'
    fredApiKeyDraft.value = ''
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
    fredError.value = ''
    try {
      const [systemResponse, llmResponse, fredResponse] = await Promise.all([
        systemApi.getConfig(),
        systemApi.getLlmConfig(),
        systemApi.getFredApiConfig(),
      ])
      systemConfig.value = systemResponse
      applyConfig(llmResponse)
      applyFredConfig(fredResponse)
    } catch (err) {
      console.error('Load system config failed', err)
      error.value = '加载配置失败'
    }
  }

  const saveConfig = async () => {
    if (!canSave.value) return
    saving.value = true
    message.value = ''
    error.value = ''
    try {
      const response = await systemApi.updateLlmConfig({
        provider: form.provider,
        apiKey: apiKeyDraft.value || null,
        baseUrl: form.baseUrl,
        modelId: form.modelId,
        reasoningEnabled: form.reasoningEnabled,
      })
      applyConfig(response)
      message.value = '配置已保存'
    } catch (err) {
      console.error('Save LLM config failed', err)
      error.value = '保存配置失败'
    } finally {
      saving.value = false
    }
  }

  const saveFredConfig = async () => {
    if (!canSaveFred.value) return
    fredSaving.value = true
    fredMessage.value = ''
    fredError.value = ''
    try {
      const response = await systemApi.updateFredApiConfig({
        apiKey: fredApiKeyDraft.value,
      })
      applyFredConfig(response)
      fredMessage.value = 'FRED API Key 已保存'
    } catch (err) {
      console.error('Save FRED API config failed', err)
      fredError.value = '保存 FRED API Key 失败'
    } finally {
      fredSaving.value = false
    }
  }

  onMounted(loadConfig)

  return {
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
    selectedPreset,
    isCustomProvider,
    canSave,
    canSaveFred,
    applyProviderPreset,
    handleProviderChange,
    saveConfig,
    saveFredConfig,
  }
}

