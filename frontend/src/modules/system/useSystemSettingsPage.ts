import { computed, onMounted, reactive, ref } from 'vue'

import { systemApi, type LlmProviderConfigResponse } from './api'

interface LlmConfigForm {
  provider: string
  apiKeySet: boolean
  apiKeyPreview: string
  baseUrl: string
  modelId: string
  reasoningEnabled: boolean
}

export const useSystemSettingsPage = () => {
  const presets = ref<LlmProviderConfigResponse['presets']>([])
  const apiKeyDraft = ref('')
  const saving = ref(false)
  const message = ref('')
  const error = ref('')
  const form = reactive<LlmConfigForm>({
    provider: 'deepseek',
    apiKeySet: false,
    apiKeyPreview: '',
    baseUrl: '',
    modelId: '',
    reasoningEnabled: false,
  })

  const selectedPreset = computed(() => presets.value.find((item) => item.id === form.provider) || null)
  const isCustomProvider = computed(() => form.provider === 'custom')
  const canSave = computed(() => {
    const hasApiKey = Boolean(apiKeyDraft.value || form.apiKeySet)
    if (!hasApiKey) return false
    if (isCustomProvider.value) return Boolean(form.baseUrl && form.modelId)
    return true
  })

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
      const response = await systemApi.getLlmConfig()
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
      const response = await systemApi.updateLlmConfig({
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

  return {
    presets,
    apiKeyDraft,
    saving,
    message,
    error,
    form,
    selectedPreset,
    isCustomProvider,
    canSave,
    applyProviderPreset,
    handleProviderChange,
    saveConfig,
  }
}
