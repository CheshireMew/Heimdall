from __future__ import annotations

from pydantic import BaseModel, Field


class LlmProviderPresetResponse(BaseModel):
    id: str
    label: str
    baseUrl: str
    defaultModel: str
    supportsReasoning: bool = False


class LlmProviderConfigResponse(BaseModel):
    provider: str
    apiKey: str = ""
    apiKeySet: bool = False
    baseUrl: str
    modelId: str
    reasoningEnabled: bool = False
    presets: list[LlmProviderPresetResponse] = Field(default_factory=list)


class LlmProviderConfigUpdateRequest(BaseModel):
    provider: str
    apiKey: str | None = None
    baseUrl: str = ""
    modelId: str = ""
    reasoningEnabled: bool = False
