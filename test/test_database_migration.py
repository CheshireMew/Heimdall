from __future__ import annotations

import sqlite3

import pytest
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect

import app.infra.db.database as db_module
import app.infra.db.schema_runtime as schema_runtime
from app.infra.db.schema import Base
from config.settings import AppSettings


@pytest.fixture
def isolated_db(monkeypatch, tmp_path):
    engines = []
    original_runtime = db_module.get_database_runtime()

    def activate(name: str):
        path = tmp_path / name
        url = f"sqlite:///{path.as_posix()}"
        engine = create_engine(url, connect_args={"check_same_thread": False})
        engines.append(engine)
        runtime = db_module.create_database_runtime(AppSettings(DATABASE_URL=url))
        runtime.dispose()
        runtime.engine = engine
        runtime.session_factory.configure(bind=engine)
        db_module.configure_database_runtime(runtime)
        schema_runtime._prepared_urls.clear()
        return path, engine

    yield activate

    db_module.configure_database_runtime(original_runtime)
    schema_runtime._prepared_urls.clear()
    for engine in engines:
        engine.dispose()


def _create_partial_legacy_sqlite(path) -> None:
    connection = sqlite3.connect(path)
    try:
        connection.execute(
            """
            CREATE TABLE backtest_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol VARCHAR(20) NOT NULL,
                timeframe VARCHAR(10) NOT NULL,
                start_date DATETIME NOT NULL,
                end_date DATETIME NOT NULL,
                created_at DATETIME,
                status VARCHAR(20),
                total_candles INTEGER,
                total_signals INTEGER,
                buy_signals INTEGER,
                sell_signals INTEGER,
                hold_signals INTEGER,
                metadata JSON
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE backtest_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                backtest_id INTEGER NOT NULL,
                timestamp DATETIME NOT NULL,
                price FLOAT NOT NULL,
                signal VARCHAR(10) NOT NULL,
                confidence FLOAT,
                indicators JSON,
                reasoning TEXT,
                FOREIGN KEY(backtest_id) REFERENCES backtest_runs (id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE klines (
                symbol VARCHAR(20) NOT NULL,
                timeframe VARCHAR(10) NOT NULL,
                timestamp INTEGER NOT NULL,
                open FLOAT NOT NULL,
                high FLOAT NOT NULL,
                low FLOAT NOT NULL,
                close FLOAT NOT NULL,
                volume FLOAT NOT NULL,
                PRIMARY KEY (symbol, timeframe, timestamp)
            )
            """
        )
        connection.commit()
    finally:
        connection.close()


def test_prepare_db_migrates_partial_legacy_sqlite(isolated_db):
    path, engine = isolated_db("partial_legacy.db")
    _create_partial_legacy_sqlite(path)

    schema_runtime.prepare_db()

    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    assert {table.name for table in Base.metadata.sorted_tables}.issubset(table_names)
    assert {"execution_mode", "engine"}.issubset(
        {column["name"] for column in inspector.get_columns("backtest_runs")}
    )
    assert "ix_signal_backtest_id" in {
        index["name"] for index in inspector.get_indexes("backtest_signals")
    }

    with engine.connect() as connection:
        current = MigrationContext.configure(connection).get_current_revision()
    expected = ScriptDirectory.from_config(schema_runtime._alembic_config()).get_current_head()
    assert current == expected
    schema_runtime.verify_database_schema()


def test_verify_database_schema_rejects_stamped_but_incomplete_schema(isolated_db):
    _, engine = isolated_db("bad_stamp.db")
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"
        )
        connection.exec_driver_sql(
            "INSERT INTO alembic_version VALUES ('003_current_schema')"
        )
        for table in Base.metadata.sorted_tables:
            connection.exec_driver_sql(f"CREATE TABLE {table.name} (id INTEGER)")

    with pytest.raises(RuntimeError, match="数据库结构与当前模型不一致"):
        schema_runtime.verify_database_schema()
