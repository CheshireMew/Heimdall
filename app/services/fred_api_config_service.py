from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.schemas.config import FredApiConfigResponse
from config import settings


class FredApiConfigService:
    def __init__(self, config_path: Path | None = None) -> None:
        self.config_path = config_path or settings.FRED_CONFIG_PATH

    def read_config(self) -> FredApiConfigResponse:
        api_key, source = self._resolve_api_key()
        return FredApiConfigResponse.model_validate({
            "apiKey": "",
            "apiKeySet": bool(api_key),
            "apiKeyPreview": self._mask_api_key(api_key),
            "source": source,
        })

    def read_effective_api_key(self) -> str:
        api_key, _source = self._resolve_api_key()
        return api_key

    def save_config(self, payload: dict[str, Any]) -> FredApiConfigResponse:
        api_key = self.read_effective_api_key()
        if "apiKey" in payload and payload.get("apiKey") is not None:
            api_key = str(payload.get("apiKey") or "").strip()

        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps({"apiKey": api_key}, ensure_ascii=False, indent=2), encoding="utf-8")
        settings.FRED_API_KEY = api_key
        return self.read_config()

    def _resolve_api_key(self) -> tuple[str, str]:
        raw = self._read_raw_config()
        if "apiKey" in raw:
            api_key = str(raw.get("apiKey") or "").strip()
            return api_key, "saved" if api_key else "unset"

        api_key = str(settings.FRED_API_KEY or "").strip()
        return api_key, "env" if api_key else "unset"

    def _read_raw_config(self) -> dict[str, Any]:
        if not self.config_path.exists():
            return {}
        try:
            data = json.loads(self.config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return data if isinstance(data, dict) else {}

    def _mask_api_key(self, api_key: str) -> str:
        key = str(api_key or "").strip()
        if not key:
            return ""
        if len(key) <= 8:
            return key[:2] + "*" * max(len(key) - 4, 1) + key[-2:]
        return f"{key[:4]}{'*' * 8}{key[-4:]}"


_default_service: FredApiConfigService | None = None


def get_fred_api_key() -> str:
    global _default_service
    if _default_service is None:
        _default_service = FredApiConfigService()
    return _default_service.read_effective_api_key()
