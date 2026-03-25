"""
数据库连接与 Session 管理
"""
import os
import logging
from pathlib import Path
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.infra.db.schema import Base

db_logger = logging.getLogger(__name__)

from config import settings

# 数据库文件路径/连接串（可通过环境变量覆盖）
_DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "heimdall.db"
DB_URL = settings.DATABASE_URL or f"sqlite:///{_DEFAULT_DB_PATH}"

# 确保 data 目录存在（仅针对 sqlite 文件场景）
if DB_URL.startswith("sqlite:///"):
    os.makedirs(_DEFAULT_DB_PATH.parent, exist_ok=True)

# 创建数据库引擎
_engine_kwargs = {
    'echo': False,
    'pool_pre_ping': True,       # 自动检测失效连接
    'pool_recycle': 3600,        # 每小时回收连接
}

if DB_URL.startswith("sqlite"):
    # SQLite: 禁用连接池的线程检查（因为 run_in_executor 跨线程使用）
    _engine_kwargs['connect_args'] = {"check_same_thread": False}
else:
    # PostgreSQL / MySQL: 配置连接池大小
    _engine_kwargs['pool_size'] = 10
    _engine_kwargs['max_overflow'] = 20

engine = create_engine(DB_URL, **_engine_kwargs)

# Session 工厂
SessionLocal = sessionmaker(bind=engine)

def init_db():
    """
    初始化数据库，创建所有表
    """
    Base.metadata.create_all(engine)
    try:
        from app.services.backtest.strategy_library import StrategyLibraryService

        StrategyLibraryService().ensure_defaults()
    except Exception as exc:
        db_logger.warning(f"策略库初始化失败: {exc}")
    db_logger.info(f"数据库初始化完成: {DB_URL}")

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
