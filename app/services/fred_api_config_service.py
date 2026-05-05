from __future__ import annotations

from pathlib import Path
from typing import Any

from app.contracts.dto.config import FredApiConfigResponse
from app.services.config_file import mask_secret, read_json_object, write_json_object
from config import settings


class FredApiConfigService:
    def __init__(self, config_path: Path | None = None) -> None:
        self.config_path = config_path or settings.FRED_CONFIG_PATH

    def read_config(self) -> FredApiConfigResponse:
        api_key, source = self._resolve_api_key()
        return FredApiConfigResponse.model_validate({
            "apiKey": "",
            "apiKeySet": bool(api_key),
            "apiKeyPreview": mask_secret(api_key),
            "source": source,
        })

    def read_effective_api_key(self) -> str:
        api_key, _source = self._resolve_api_key()
        return api_key

    def save_config(self, payload: dict[str, Any]) -> FredApiConfigResponse:
        api_key = self.read_effective_api_key()
        if "apiKey" in payload and payload.get("apiKey") is not None:
            api_key = str(payload.get("apiKey") or "").strip()

        write_json_object(self.config_path, {"apiKey": api_key})
        settings.FRED_API_KEY = api_key
        return self.read_config()

    def _resolve_api_key(self) -> tuple[str, str]:
        raw = read_json_object(self.config_path)
        if "apiKey" in raw:
            api_key = str(raw.get("apiKey") or "").strip()
            return api_key, "saved" if api_key else "unset"

        api_key = str(settings.FRED_API_KEY or "").strip()
        return api_key, "env" if api_key else "unset"


_default_service: FredApiConfigService | None = None


def get_fred_api_key() -> str:
    global _default_service
    if _default_service is None:
        _default_service = FredApiConfigService()
    return _default_service.read_effective_api_key()
