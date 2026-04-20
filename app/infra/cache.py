"""
Redis cache service.
"""
from __future__ import annotations

import json
from typing import Any

import redis

from config import settings
from utils.logger import logger


class RedisService:
    def __init__(self, app_settings=settings) -> None:
        self.settings = app_settings
        self.client = None
        self._connection_attempted = False

    def connect(self, *, force: bool = False) -> None:
        if self._connection_attempted and not force:
            return
        self._connection_attempted = True
        try:
            pool = redis.ConnectionPool(
                host=self.settings.REDIS_HOST,
                port=self.settings.REDIS_PORT,
                db=self.settings.REDIS_DB,
                password=self.settings.REDIS_PASSWORD or None,
                decode_responses=True,
            )
            self.client = redis.Redis(connection_pool=pool)
            self.client.ping()
            logger.info("[OK] Redis 连接成功")
        except Exception as exc:
            logger.warning(f"Redis 连接失败 (将降级运行): {exc}")
            self.client = None

    def _ensure_client(self) -> bool:
        if self.client is not None:
            return True
        self.connect()
        return self.client is not None

    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        if not self._ensure_client():
            return False
        try:
            payload = json.dumps(value) if isinstance(value, (dict, list)) else value
            return bool(self.client.setex(key, ttl, payload))
        except Exception as exc:
            logger.warning(f"Redis Set Error: {exc}")
            return False

    def get(self, key: str) -> Any | None:
        if not self._ensure_client():
            return None
        try:
            value = self.client.get(key)
            if not value:
                return None
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception as exc:
            logger.warning(f"Redis Get Error: {exc}")
            return None

    def delete(self, key: str) -> bool:
        if not self._ensure_client():
            return False
        try:
            return bool(self.client.delete(key))
        except Exception as exc:
            logger.warning(f"Redis Delete Error: {exc}")
            return False


def build_cache_service(app_settings=settings) -> RedisService:
    return RedisService(app_settings)
