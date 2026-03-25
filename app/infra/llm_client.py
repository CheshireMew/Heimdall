from __future__ import annotations

import asyncio
import json
from typing import Any

import httpx

from config import settings
from utils.logger import logger


RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
MAX_RETRIES = 3
BASE_DELAY = 1.0


class LLMClient:
    def __init__(self) -> None:
        self.api_key = settings.DEEPSEEK_API_KEY
        self.base_url = settings.DEEPSEEK_BASE_URL
        self.model = settings.AI_MODEL

        if not self.api_key or len(self.api_key) < 10 or "sk-your-key" in self.api_key:
            logger.warning("[Security] DeepSeek API Key 未配置或无效。AI 分析功能将不可用。")
            self.api_key = None

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def analyze(self, prompt: str) -> dict[str, Any] | None:
        if not self.api_key:
            return None

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": settings.LLM_TEMPERATURE,
            "stream": False,
        }
        url = f"{self.base_url}/v1/chat/completions"

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

                content = data["choices"][0]["message"]["content"]
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

