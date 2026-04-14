from __future__ import annotations

import asyncio
import json
from typing import Any

import httpx

from app.services.llm_config_service import read_effective_llm_config
from config import settings
from utils.logger import logger


RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
MAX_RETRIES = 3
BASE_DELAY = 1.0


class LLMClient:
    def __init__(self) -> None:
        llm_config = read_effective_llm_config()
        self.provider = llm_config["provider"]
        self.api_key = llm_config["apiKey"]
        self.base_url = llm_config["baseUrl"]
        self.model = llm_config["modelId"]

        if not self.api_key or len(self.api_key) < 10 or "sk-your-key" in self.api_key:
            logger.warning("[Security] LLM API Key 未配置或无效。AI 分析功能将不可用。")
            self.api_key = None

        self.headers = self._headers()

    async def analyze(self, prompt: str) -> dict[str, Any] | None:
        if not self.api_key:
            return None

        payload = self._payload(prompt)
        url = self._endpoint()

        last_error: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                async with httpx.AsyncClient(timeout=settings.LLM_REQUEST_TIMEOUT) as client:
                    response = await client.post(url, headers=self.headers, json=payload)
                    if response.status_code in RETRYABLE_STATUS_CODES:
                        delay = BASE_DELAY * (2 ** attempt)
                        retry_after = response.headers.get("Retry-After")
                        if retry_after:
                            try:
                                delay = float(retry_after)
                            except ValueError:
                                pass
                        logger.warning(
                            f"LLM API returned {response.status_code}, retrying in {delay:.1f}s "
                            f"(attempt {attempt + 1}/{MAX_RETRIES})"
                        )
                        await asyncio.sleep(delay)
                        continue
                    response.raise_for_status()
                    data = response.json()

                content = self._content_from_response(data)
                try:
                    return json.loads(content.replace("```json", "").replace("```", "").strip())
                except json.JSONDecodeError:
                    logger.error("AI 返回的内容不是有效的 JSON")
                    logger.debug(f"Raw content: {content}")
                    return None
            except httpx.RequestError as exc:
                last_error = exc
                if attempt < MAX_RETRIES - 1:
                    delay = BASE_DELAY * (2 ** attempt)
                    logger.warning(f"LLM API connection error: {exc}, retrying in {delay:.1f}s")
                    await asyncio.sleep(delay)
                    continue
            except httpx.HTTPStatusError as exc:
                logger.error(f"API 请求失败 status={exc.response.status_code}: {exc}")
                return None
            except Exception as exc:
                logger.error(f"未知错误: {exc}")
                return None

        logger.error(f"LLM API failed after {MAX_RETRIES} retries: {last_error}")
        return None

    def _headers(self) -> dict[str, str]:
        if self.provider == "anthropic":
            return {
                "x-api-key": f"{self.api_key}",
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            }
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _payload(self, prompt: str) -> dict[str, Any]:
        if self.provider == "anthropic":
            return {
                "model": self.model,
                "max_tokens": 2048,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": settings.LLM_TEMPERATURE,
            }
        return {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": settings.LLM_TEMPERATURE,
            "stream": False,
        }

    def _endpoint(self) -> str:
        base_url = (self.base_url or "").rstrip("/")
        if self.provider == "anthropic":
            return f"{base_url}/messages"
        if "/v1" in base_url or "/openai" in base_url:
            return f"{base_url}/chat/completions"
        return f"{base_url}/v1/chat/completions"

    def _content_from_response(self, data: dict[str, Any]) -> str:
        if self.provider == "anthropic":
            content_items = data.get("content") or []
            for item in content_items:
                if item.get("type") == "text" and item.get("text"):
                    return item["text"]
            return ""
        return data["choices"][0]["message"]["content"]
