from __future__ import annotations

import logging

from sqlalchemy import inspect

from app.infra.db.database import DatabaseRuntime, build_database_runtime
from app.infra.db.schema import Base
from config.settings import BASE_DIR

db_logger = logging.getLogger(__name__)
_prepared_urls: set[str] = set()


def init_db(database_runtime: DatabaseRuntime) -> None:
    prepare_db(database_runtime)


def prepare_db(database_runtime: DatabaseRuntime) -> None:
    """显式执行数据库迁移，仅供启动脚本/部署脚本调用。"""
    database_url = database_runtime.database_url
    if database_url in _prepared_urls:
        return
    from alembic import command

    alembic_config = _alembic_config(database_url)
    _version_unmanaged_database(alembic_config, database_runtime)
    command.upgrade(alembic_config, "head")
    _prepared_urls.add(database_url)
    db_logger.info(f"数据库迁移完成: {database_url}")


def verify_database_schema(database_runtime: DatabaseRuntime) -> None:
    """应用启动只检查迁移状态，不隐式 create_all/ALTER。"""
    from alembic.autogenerate import compare_metadata
    from alembic.runtime.migration import MigrationContext
    from alembic.script import ScriptDirectory

    alembic_config = _alembic_config(database_runtime.database_url)
    script = ScriptDirectory.from_config(alembic_config)
    expected = script.get_current_head()
    with database_runtime.engine.connect() as connection:
        migration_context = MigrationContext.configure(
            connection,
            opts={"compare_type": True},
        )
        current = migration_context.get_current_revision()
        diffs = _relevant_schema_diffs(
            compare_metadata(migration_context, Base.metadata),
            database_runtime,
        )
    if current != expected:
        raise RuntimeError(
            f"数据库迁移未就绪: current={current or 'none'}, head={expected}. "
            "请先运行 python scripts/prepare_db.py"
        )
    if diffs:
        raise RuntimeError(
            "数据库结构与当前模型不一致，请先运行 python scripts/prepare_db.py"
        )
    _assert_model_tables_present(database_runtime)


def _relevant_schema_diffs(diffs: list[object], database_runtime: DatabaseRuntime) -> list[object]:
    return [
        diff
        for diff in _flatten_schema_diffs(diffs)
        if not _is_ignored_schema_diff(diff, database_runtime)
    ]


def _flatten_schema_diffs(diffs: list[object]):
    for diff in diffs:
        if isinstance(diff, list):
            yield from _flatten_schema_diffs(diff)
        else:
            yield diff


def _is_ignored_schema_diff(diff: object, database_runtime: DatabaseRuntime) -> bool:
    if not isinstance(diff, tuple) or not diff:
        return False
    if database_runtime.engine.dialect.name != "sqlite" or diff[0] != "modify_nullable":
        return False
    table_name = str(diff[2])
    column_name = str(diff[3])
    current_nullable = diff[5]
    model_nullable = diff[6]
    table = Base.metadata.tables.get(table_name)
    column = table.columns.get(column_name) if table is not None else None
    return bool(
        column is not None
        and column.primary_key
        and current_nullable is True
        and model_nullable is False
    )


def _alembic_config(database_url: str):
    from alembic.config import Config

    config = Config(str(BASE_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BASE_DIR / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url)
    config.attributes["use_configured_database_url"] = True
    return config


def _version_unmanaged_database(alembic_config, database_runtime: DatabaseRuntime) -> None:
    from alembic import command

    inspector = inspect(database_runtime.engine)
    tables = set(inspector.get_table_names())
    if "alembic_version" in tables:
        return
    app_tables = tables - {"sqlite_sequence"}
    if not app_tables:
        return
    if _schema_has_current_model_columns(inspector):
        command.stamp(alembic_config, "head")
        return
    model_tables = {table.name for table in Base.metadata.sorted_tables}
    if app_tables.issubset(model_tables):
        # 历史版本曾由 create_all 和手写 ALTER 共同改表；003 是当前结构补齐迁移，
        # 因此只要库里全是已知模型表，就交给 003 统一补齐缺表、缺列和索引。
        command.stamp(alembic_config, "002_widen_kline_symbol")
        return
    raise RuntimeError("数据库存在未纳入 Alembic 管理的旧结构，请备份后手动迁移")


def _schema_has_current_model_columns(inspector) -> bool:
    table_names = set(inspector.get_table_names())
    for table in Base.metadata.sorted_tables:
        if table.name not in table_names:
            return False
        columns = {column["name"] for column in inspector.get_columns(table.name)}
        if any(column.name not in columns for column in table.columns):
            return False
    return True


def _assert_model_tables_present(database_runtime: DatabaseRuntime) -> None:
    inspector = inspect(database_runtime.engine)
    missing = [
        table.name
        for table in Base.metadata.sorted_tables
        if table.name not in inspector.get_table_names()
    ]
    if missing:
        raise RuntimeError(
            f"数据库表缺失: {', '.join(missing)}. 请先运行 python scripts/prepare_db.py"
        )


if __name__ == "__main__":
    from config.settings import settings

    runtime = build_database_runtime(settings)
    prepare_db(runtime)
    runtime.dispose()
