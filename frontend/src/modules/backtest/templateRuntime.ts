import type { StrategyTemplateRuntime } from './contracts'

import type { EditorTemplateRuntimeCarrier } from './editorTypes'

const DEFAULT_TEMPLATE_RUNTIME: Required<StrategyTemplateRuntime> = {
  builder_kind: 'rules',
  capabilities: {
    signal_runtime: true,
    paper: true,
    version_editing: true,
  },
}

export const getTemplateRuntime = (value: EditorTemplateRuntimeCarrier): Required<StrategyTemplateRuntime> => {
  const runtime = value?.template_runtime
  if (!runtime || typeof runtime !== 'object') {
    return DEFAULT_TEMPLATE_RUNTIME
  }
  const capabilities = runtime.capabilities && typeof runtime.capabilities === 'object'
    ? runtime.capabilities
    : DEFAULT_TEMPLATE_RUNTIME.capabilities
  return {
    builder_kind: typeof runtime.builder_kind === 'string' ? runtime.builder_kind : DEFAULT_TEMPLATE_RUNTIME.builder_kind,
    capabilities: {
      signal_runtime: capabilities.signal_runtime !== false,
      paper: capabilities.paper !== false,
      version_editing: capabilities.version_editing !== false,
    },
  }
}

export const supportsPaperTrading = (value: EditorTemplateRuntimeCarrier) => getTemplateRuntime(value).capabilities.paper

export const supportsVersionEditing = (value: EditorTemplateRuntimeCarrier) => getTemplateRuntime(value).capabilities.version_editing
