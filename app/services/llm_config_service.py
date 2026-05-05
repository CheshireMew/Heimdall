from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from app.contracts.dto.config import LlmProviderConfigResponse, LlmProviderPresetResponse
from app.services.config_file import mask_secret, read_json_object, write_json_object
from config import settings


LLM_PROVIDER_PRESETS: dict[str, dict[str, Any]] = {
    "deepseek": {
        "id": "deepseek",
        "label": "DeepSeek",
        "baseUrl": "https://api.deepseek.com/v1",
        "defaultModel": "deepseek-chat",
        "supportsReasoning": True,
    },
    "openai": {
        "id": "openai",
        "label": "OpenAI",
        "baseUrl": "https://api.openai.com/v1",
        "defaultModel": "gpt-5.2-chat-latest",
        "supportsReasoning": False,
    },
    "gemini": {
        "id": "gemini",
        "label": "Google Gemini",
        "baseUrl": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "defaultModel": "gemini-2.5-pro",
        "supportsReasoning": False,
    },
    "anthropic": {
        "id": "anthropic",
        "label": "Anthropic Claude",
        "baseUrl": "https://api.anthropic.com/v1",
        "defaultModel": "claude-opus-4-1-20250805",
        "supportsReasoning": False,
    },
    "glm": {
        "id": "glm",
        "label": "GLM",
        "baseUrl": "https://open.bigmodel.cn/api/paas/v4",
        "defaultModel": "GLM-5.1",
        "supportsReasoning": False,
    },
    "siliconflow": {
        "id": "siliconflow",
        "label": "SiliconFlow",
        "baseUrl": "https://api.siliconflow.cn/v1",
        "defaultModel": "deepseek-ai/DeepSeek-V3.2",
        "supportsReasoning": False,
    },
    "minimax": {
        "id": "minimax",
        "label": "MiniMax",
        "baseUrl": "https://api.minimaxi.com/v1",
        "defaultModel": "MiniMax-M2.7",
        "supportsReasoning": False,
    },
    "custom": {
        "id": "custom",
        "label": "Custom / Local",
        "baseUrl": "",
        "defaultModel": "",
        "supportsReasoning": False,
    },
}


class LlmConfigService:
    def __init__(self, config_path: Path | None = None) -> None:
        self.config_path = config_path or settings.LLM_CONFIG_PATH

    def list_presets(self) -> list[LlmProviderPresetResponse]:
        return [
            LlmProviderPresetResponse.model_validate(deepcopy(item))
            for item in LLM_PROVIDER_PRESETS.values()
        ]

    def read_config(self) -> LlmProviderConfigResponse:
        raw = read_json_object(self.config_path)
        provider = self._resolve_provider(raw.get("provider"))
        preset = LLM_PROVIDER_PRESETS[provider]
        reasoning_enabled = bool(raw.get("reasoningEnabled", settings.AI_MODEL == "deepseek-reasoner"))
        api_key = str(raw.get("apiKey") or settings.DEEPSEEK_API_KEY or "")

        base_url = str(raw.get("baseUrl") or "")
        model_id = str(raw.get("modelId") or "")
        if provider != "custom":
            base_url = preset["baseUrl"]
            model_id = self._preset_model(provider, reasoning_enabled)

        return LlmProviderConfigResponse.model_validate({
            "provider": provider,
            "apiKey": "",
            "apiKeySet": bool(api_key),
            "apiKeyPreview": mask_secret(api_key),
            "baseUrl": base_url,
            "modelId": model_id,
            "reasoningEnabled": reasoning_enabled if provider == "deepseek" else False,
            "presets": self.list_presets(),
        })

    def read_effective_config(self) -> dict[str, Any]:
        raw = read_json_object(self.config_path)
        provider = self._resolve_provider(raw.get("provider"))
        preset = LLM_PROVIDER_PRESETS[provider]
        reasoning_enabled = bool(raw.get("reasoningEnabled", settings.AI_MODEL == "deepseek-reasoner"))
        api_key = str(raw.get("apiKey") or settings.DEEPSEEK_API_KEY or "")

        if provider == "custom":
            base_url = str(raw.get("baseUrl") or settings.DEEPSEEK_BASE_URL or "")
            model_id = str(raw.get("modelId") or settings.AI_MODEL or "")
        else:
            base_url = preset["baseUrl"]
            model_id = self._preset_model(provider, reasoning_enabled)

        return {
            "provider": provider,
            "apiKey": api_key,
            "baseUrl": base_url,
            "modelId": model_id,
            "reasoningEnabled": reasoning_enabled if provider == "deepseek" else False,
        }

    def save_config(self, payload: dict[str, Any]) -> LlmProviderConfigResponse:
        existing = read_json_object(self.config_path)
        provider = self._resolve_provider(payload.get("provider"))
        preset = LLM_PROVIDER_PRESETS[provider]
        reasoning_enabled = bool(payload.get("reasoningEnabled")) if provider == "deepseek" else False

        api_key = existing.get("apiKey", settings.DEEPSEEK_API_KEY or "")
        if "apiKey" in payload and payload.get("apiKey") is not None:
            api_key = str(payload.get("apiKey") or "").strip()

        if provider == "custom":
            base_url = str(payload.get("baseUrl") or "").strip()
            model_id = str(payload.get("modelId") or "").strip()
        else:
            base_url = preset["baseUrl"]
            model_id = self._preset_model(provider, reasoning_enabled)

        saved = {
            "provider": provider,
            "apiKey": api_key,
            "baseUrl": base_url,
            "modelId": model_id,
            "reasoningEnabled": reasoning_enabled,
        }
        write_json_object(self.config_path, saved)
        return self.read_config()

    def _resolve_provider(self, value: Any) -> str:
        return str(value) if value in LLM_PROVIDER_PRESETS else "deepseek"

    def _preset_model(self, provider: str, reasoning_enabled: bool) -> str:
        if provider == "deepseek" and reasoning_enabled:
            return "deepseek-reasoner"
        return str(LLM_PROVIDER_PRESETS[provider]["defaultModel"])
