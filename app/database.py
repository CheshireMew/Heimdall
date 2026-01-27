"""
数据库连接和会话管理（应用层复用 models.database 定义，避免重复元数据）
"""
from models.database import engine, SessionLocal, Base  # 复用统一的 Engine/Session/Base

# 依赖注入：获取数据库会话
def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
