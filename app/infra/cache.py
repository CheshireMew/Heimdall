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
    _instance: "RedisService | None" = None

    def __new__(cls) -> "RedisService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.client = None
            cls._instance._connection_attempted = False
        return cls._instance

    def connect(self, *, force: bool = False) -> None:
        if self._connection_attempted and not force:
            return
        self._connection_attempted = True
        try:
            pool = redis.ConnectionPool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD or None,
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


redis_service = RedisService()
