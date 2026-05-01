from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker

from config.settings import AppSettings


class DatabaseRuntime:
    def __init__(self, *, database_url: str, source: str) -> None:
        self.database_url = database_url
        self.source = source
        self.engine = self._create_engine(database_url)
        self.session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)

    def get_session(self) -> Session:
        return self.session_factory()

    @contextmanager
    def session_scope(self):
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def dispose(self) -> None:
        self.engine.dispose()

    @staticmethod
    def _create_engine(database_url: str) -> Engine:
        if database_url.startswith("sqlite"):
            sqlite_path = make_url(database_url).database
            if sqlite_path and sqlite_path != ":memory:":
                os.makedirs(Path(sqlite_path).parent, exist_ok=True)

        engine_kwargs: dict[str, object] = {
            "echo": False,
            "pool_pre_ping": True,
            "pool_recycle": 3600,
        }

        if database_url.startswith("sqlite"):
            engine_kwargs["connect_args"] = {"check_same_thread": False}
        else:
            engine_kwargs["pool_size"] = 10
            engine_kwargs["max_overflow"] = 20

        return create_engine(database_url, **engine_kwargs)


def resolve_database_url(app_settings: AppSettings) -> tuple[str, str]:
    database_url = app_settings.DATABASE_URL.strip()
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL 未配置。Heimdall 的数据库唯一入口是 DATABASE_URL；"
            "服务器部署请配置 PostgreSQL 连接串，例如 "
            "postgresql://user:password@host:5432/heimdall。"
        )
    return database_url, "settings"


def build_database_runtime(app_settings: AppSettings) -> DatabaseRuntime:
    database_url, source = resolve_database_url(app_settings)
    return DatabaseRuntime(database_url=database_url, source=source)
