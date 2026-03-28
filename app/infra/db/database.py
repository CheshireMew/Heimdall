"""
数据库连接与 Session 管理
"""
import os
import logging
from pathlib import Path
from contextlib import contextmanager
from sqlalchemy import create_engine, inspect, text
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
_initialized = False

def init_db():
    """
    初始化数据库，创建所有表
    """
    global _initialized
    if _initialized:
        return
    Base.metadata.create_all(engine)
    _ensure_backtest_run_contract_columns()
    try:
        from app.services.backtest.strategy_defaults_service import StrategyDefaultsService

        StrategyDefaultsService().ensure_defaults()
    except Exception as exc:
        db_logger.warning(f"策略库初始化失败: {exc}")
    _initialized = True
    db_logger.info(f"数据库初始化完成: {DB_URL}")

def get_session():
    """
    获取数据库会话
    """
    return SessionLocal()


def _ensure_backtest_run_contract_columns() -> None:
    inspector = inspect(engine)
    if "backtest_runs" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("backtest_runs")}
    statements: list[str] = []
    if "execution_mode" not in existing_columns:
        statements.append(
            "ALTER TABLE backtest_runs ADD COLUMN execution_mode VARCHAR(20) NOT NULL DEFAULT 'backtest'"
        )
    if "engine" not in existing_columns:
        statements.append(
            "ALTER TABLE backtest_runs ADD COLUMN engine VARCHAR(50) NOT NULL DEFAULT 'Freqtrade'"
        )

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_backtest_runs_mode_created_at "
                "ON backtest_runs (execution_mode, created_at)"
            )
        )
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_backtest_runs_mode_engine_status_created_at "
                "ON backtest_runs (execution_mode, engine, status, created_at)"
            )
        )

    from app.infra.db.schema import BacktestRun

    with session_scope() as session:
        runs = session.query(BacktestRun).all()
        for run in runs:
            metadata = dict(run.metadata_info or {})
            next_execution_mode = str(metadata.get("execution_mode") or run.execution_mode or "backtest")
            next_engine = str(metadata.get("engine") or run.engine or "Freqtrade")
            changed = False
            if run.execution_mode != next_execution_mode:
                run.execution_mode = next_execution_mode
                changed = True
            if run.engine != next_engine:
                run.engine = next_engine
                changed = True
            if metadata.pop("execution_mode", None) is not None:
                changed = True
            if metadata.pop("engine", None) is not None:
                changed = True
            if changed:
                run.metadata_info = metadata

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
