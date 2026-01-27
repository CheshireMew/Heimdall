"""
应用配置和环境变量管理
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
from pathlib import Path

class Settings(BaseSettings):
    """应用配置"""
    
    # 应用设置
    APP_NAME: str = "Heimdall"
    DEBUG: bool = True
    
    # 数据库配置（默认使用项目内 data 目录的绝对路径，避免工作目录差异导致多份 sqlite）
    _BASE_DIR = Path(__file__).resolve().parent.parent
    DATABASE_URL: str = f"sqlite:///{_BASE_DIR / 'data' / 'heimdall.db'}"
    
    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # API密钥
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    
    # 交易所配置
    EXCHANGE: str = "binance"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
