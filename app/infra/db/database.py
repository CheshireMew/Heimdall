from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from threading import Lock
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker

from config.settings import DEFAULT_DB_PATH, AppSettings, settings


class DatabaseRuntime:
    def __init__(self, *, database_url: str, source: str) -> None:
        self.database_url = database_url
        self.source = source
        self.engine = self._create_engine(database_url)
        self.session_factory = sessionmaker(bind=self.engine)

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
            # SQLite 仍保留跨线程访问选项，因为后台任务会走线程池。
            engine_kwargs["connect_args"] = {"check_same_thread": False}
        else:
            engine_kwargs["pool_size"] = 10
            engine_kwargs["max_overflow"] = 20

        return create_engine(database_url, **engine_kwargs)


def build_postgres_dev_url(app_settings: AppSettings) -> str:
    direct_url = app_settings.POSTGRES_DEV_URL.strip()
    if direct_url:
        return direct_url

    auth = quote_plus(app_settings.POSTGRES_DEV_USER.strip())
    if app_settings.POSTGRES_DEV_PASSWORD:
        auth = f"{auth}:{quote_plus(app_settings.POSTGRES_DEV_PASSWORD)}"
    return (
        f"postgresql://{auth}@{app_settings.POSTGRES_DEV_HOST.strip()}:"
        f"{app_settings.POSTGRES_DEV_PORT}/{app_settings.POSTGRES_DEV_DB.strip()}"
    )


def can_connect_postgres(database_url: str) -> bool:
    probe_engine = None
    try:
        probe_engine = create_engine(
            database_url,
            pool_pre_ping=False,
            connect_args={"connect_timeout": 1},
        )
        with probe_engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
    finally:
        if probe_engine is not None:
            probe_engine.dispose()


def resolve_database_url(app_settings: AppSettings) -> tuple[str, str]:
    explicit_url = app_settings.DATABASE_URL.strip()
    if explicit_url:
        return explicit_url, "explicit"

    postgres_dev_url = build_postgres_dev_url(app_settings)
    if can_connect_postgres(postgres_dev_url):
        return postgres_dev_url, "postgres-dev"

    return f"sqlite:///{DEFAULT_DB_PATH}", "sqlite-fallback"


def create_database_runtime(app_settings: AppSettings) -> DatabaseRuntime:
    database_url, source = resolve_database_url(app_settings)
    return DatabaseRuntime(database_url=database_url, source=source)


_runtime_lock = Lock()
_database_runtime: DatabaseRuntime | None = None


def configure_database_runtime(runtime: DatabaseRuntime) -> DatabaseRuntime:
    global _database_runtime
    with _runtime_lock:
        previous = _database_runtime
        _database_runtime = runtime
    if previous is not None and previous is not runtime:
        previous.dispose()
    return runtime


def get_database_runtime() -> DatabaseRuntime:
    global _database_runtime
    runtime = _database_runtime
    if runtime is not None:
        return runtime
    with _runtime_lock:
        if _database_runtime is None:
            _database_runtime = create_database_runtime(settings)
        return _database_runtime


def current_database_url() -> str:
    return get_database_runtime().database_url


def get_session() -> Session:
    return get_database_runtime().get_session()


@contextmanager
def session_scope():
    with get_database_runtime().session_scope() as session:
        yield session

