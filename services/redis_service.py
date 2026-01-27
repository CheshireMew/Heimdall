"""
Redis 服务封装
"""
import redis
import json
from typing import Optional, Any, Callable
from config import settings
from utils.logger import logger

class RedisService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisService, cls).__new__(cls)
            cls._instance.client = None
            cls._instance.connect()
        return cls._instance
    
    def connect(self):
        """连接到Redis"""
        try:
            pool = redis.ConnectionPool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD or None,
                decode_responses=True  # 自动解码为字符串
            )
            self.client = redis.Redis(connection_pool=pool)
            self.client.ping()  # 测试连接
            logger.info("✅ Redis 连接成功")
        except Exception as e:
            logger.error(f"❌ Redis 连接失败: {e}")
            self.client = None
            
    def set(self, key: str, value: Any, ttl: int = 300):
        """由于数据可能是对象，尝试JSON序列化"""
        if not self.client: return False
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            return self.client.setex(key, ttl, value)
        except Exception as e:
            logger.error(f"Redis Set Error: {e}")
            return False
            
    def get(self, key: str) -> Optional[Any]:
        if not self.client: return None
        try:
            value = self.client.get(key)
            if not value: return None
            
            # 尝试 JSON 反序列化
            try:
                return json.loads(value)
            except:
                return value
        except Exception as e:
            logger.error(f"Redis Get Error: {e}")
            return None
            
    def delete(self, key: str):
        if not self.client: return False
        try:
            return self.client.delete(key)
        except:
            return False

# 全局实例
redis_service = RedisService()
