"""
数据库连接与 Session 管理
"""
import os
from pathlib import Path
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.schema import Base, BacktestRun, BacktestSignal  # 导入模型以便 init_db 使用
from config import settings

# 数据库文件路径/连接串（可通过环境变量覆盖）
_DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "heimdall.db"
DB_URL = settings.DATABASE_URL or f"sqlite:///{_DEFAULT_DB_PATH}"

# 确保 data 目录存在（仅针对 sqlite 文件场景）
if DB_URL.startswith("sqlite:///"):
    os.makedirs(_DEFAULT_DB_PATH.parent, exist_ok=True)

# 创建数据库引擎
engine = create_engine(DB_URL, echo=False)

# Session 工厂
SessionLocal = sessionmaker(bind=engine)

def init_db():
    """
    初始化数据库，创建所有表
    """
    Base.metadata.create_all(engine)
    print(f"数据库初始化完成: {DB_URL}")

def get_session():
    """
    获取数据库会话
    """
    return SessionLocal()

@contextmanager
def session_scope():
    """
    提供事务型会话上下文，异常时回滚并确保关闭
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    init_db()

