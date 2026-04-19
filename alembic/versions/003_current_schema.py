"""align alembic schema with current models

Revision ID: 003_current_schema
Revises: 002_widen_kline_symbol
Create Date: 2026-04-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "003_current_schema"
down_revision: Union[str, None] = "002_widen_kline_symbol"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _inspector() -> sa.Inspector:
    return sa.inspect(op.get_bind())


def _has_table(table: str) -> bool:
    return table in set(_inspector().get_table_names())


def _has_column(table: str, column: str) -> bool:
    if not _has_table(table):
        return False
    return column in {item["name"] for item in _inspector().get_columns(table)}


def _has_index(table: str, index: str) -> bool:
    if not _has_table(table):
        return False
    return index in {item["name"] for item in _inspector().get_indexes(table)}


def _create_index_if_missing(
    name: str, table: str, columns: list[str], *, unique: bool = False
) -> None:
    if not _has_index(table, name):
        op.create_index(name, table, columns, unique=unique)


def upgrade() -> None:
    if not _has_table("backtest_runs"):
        op.create_table(
            "backtest_runs",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("symbol", sa.String(20), nullable=False),
            sa.Column("timeframe", sa.String(10), nullable=False),
            sa.Column("start_date", sa.DateTime(), nullable=False),
            sa.Column("end_date", sa.DateTime(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("status", sa.String(20), nullable=True),
            sa.Column("execution_mode", sa.String(20), nullable=False),
            sa.Column("engine", sa.String(50), nullable=False),
            sa.Column("total_candles", sa.Integer(), nullable=True),
            sa.Column("total_signals", sa.Integer(), nullable=True),
            sa.Column("buy_signals", sa.Integer(), nullable=True),
            sa.Column("sell_signals", sa.Integer(), nullable=True),
            sa.Column("hold_signals", sa.Integer(), nullable=True),
            sa.Column("metadata", sa.JSON(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
    else:
        with op.batch_alter_table("backtest_runs") as batch_op:
            if not _has_column("backtest_runs", "execution_mode"):
                batch_op.add_column(
                    sa.Column(
                        "execution_mode",
                        sa.String(20),
                        nullable=False,
                        server_default="backtest",
                    )
                )
            if not _has_column("backtest_runs", "engine"):
                batch_op.add_column(
                    sa.Column(
                        "engine",
                        sa.String(50),
                        nullable=False,
                        server_default="Freqtrade",
                    )
                )
    _create_index_if_missing(
        "ix_backtest_runs_mode_created_at",
        "backtest_runs",
        ["execution_mode", "created_at"],
    )
    _create_index_if_missing(
        "ix_backtest_runs_mode_engine_status_created_at",
        "backtest_runs",
        ["execution_mode", "engine", "status", "created_at"],
    )

    if not _has_table("backtest_signals"):
        op.create_table(
            "backtest_signals",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("backtest_id", sa.Integer(), nullable=False),
            sa.Column("timestamp", sa.DateTime(), nullable=False),
            sa.Column("price", sa.Float(), nullable=False),
            sa.Column("signal", sa.String(10), nullable=False),
            sa.Column("confidence", sa.Float(), nullable=True),
            sa.Column("indicators", sa.JSON(), nullable=True),
            sa.Column("reasoning", sa.Text(), nullable=True),
            sa.ForeignKeyConstraint(["backtest_id"], ["backtest_runs.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
    _create_index_if_missing("ix_signal_backtest_id", "backtest_signals", ["backtest_id"])

    if not _has_table("klines"):
        op.create_table(
            "klines",
            sa.Column("symbol", sa.String(80), nullable=False),
            sa.Column("timeframe", sa.String(10), nullable=False),
            sa.Column("timestamp", sa.BigInteger(), nullable=False),
            sa.Column("open", sa.Float(), nullable=False),
            sa.Column("high", sa.Float(), nullable=False),
            sa.Column("low", sa.Float(), nullable=False),
            sa.Column("close", sa.Float(), nullable=False),
            sa.Column("volume", sa.Float(), nullable=False),
            sa.PrimaryKeyConstraint("symbol", "timeframe", "timestamp"),
        )
    else:
        symbol_column = next(
            (column for column in _inspector().get_columns("klines") if column["name"] == "symbol"),
            None,
        )
        timestamp_column = next(
            (column for column in _inspector().get_columns("klines") if column["name"] == "timestamp"),
            None,
        )
        symbol_length = getattr(symbol_column["type"], "length", None) if symbol_column else None
        timestamp_type = timestamp_column["type"] if timestamp_column else None
        with op.batch_alter_table("klines") as batch_op:
            if symbol_length is not None and symbol_length < 80:
                batch_op.alter_column(
                    "symbol",
                    existing_type=symbol_column["type"],
                    type_=sa.String(80),
                    existing_nullable=False,
                )
            if timestamp_type is not None and not isinstance(timestamp_type, sa.BigInteger):
                batch_op.alter_column(
                    "timestamp",
                    existing_type=timestamp_type,
                    type_=sa.BigInteger(),
                    existing_nullable=False,
                )
    _create_index_if_missing("ix_kline_sym_tf_ts", "klines", ["symbol", "timeframe", "timestamp"])

    if not _has_table("sentiment"):
        op.create_table(
            "sentiment",
            sa.Column("date", sa.DateTime(), nullable=False),
            sa.Column("value", sa.Integer(), nullable=False),
            sa.Column("classification", sa.String(20), nullable=True),
            sa.Column("timestamp", sa.BigInteger(), nullable=True),
            sa.PrimaryKeyConstraint("date"),
        )

    if not _has_table("market_indicator_meta"):
        op.create_table(
            "market_indicator_meta",
            sa.Column("id", sa.String(50), nullable=False),
            sa.Column("name", sa.String(100), nullable=False),
            sa.Column("category", sa.String(50), nullable=False),
            sa.Column("unit", sa.String(20), nullable=True),
            sa.Column("frequency", sa.String(20), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Integer(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _has_table("market_indicator_data"):
        op.create_table(
            "market_indicator_data",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("indicator_id", sa.String(50), nullable=False),
            sa.Column("timestamp", sa.DateTime(), nullable=False),
            sa.Column("value", sa.Float(), nullable=False),
            sa.ForeignKeyConstraint(["indicator_id"], ["market_indicator_meta.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
    _create_index_if_missing(
        "ix_indicator_data_id_ts",
        "market_indicator_data",
        ["indicator_id", "timestamp"],
    )

    if not _has_table("backtest_trades"):
        op.create_table(
            "backtest_trades",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("backtest_id", sa.Integer(), nullable=False),
            sa.Column("pair", sa.String(20), nullable=False),
            sa.Column("opened_at", sa.DateTime(), nullable=False),
            sa.Column("closed_at", sa.DateTime(), nullable=True),
            sa.Column("entry_price", sa.Float(), nullable=False),
            sa.Column("exit_price", sa.Float(), nullable=True),
            sa.Column("stake_amount", sa.Float(), nullable=False),
            sa.Column("amount", sa.Float(), nullable=False),
            sa.Column("profit_abs", sa.Float(), nullable=False),
            sa.Column("profit_pct", sa.Float(), nullable=False),
            sa.Column("max_drawdown_pct", sa.Float(), nullable=True),
            sa.Column("duration_minutes", sa.Integer(), nullable=True),
            sa.Column("entry_tag", sa.String(100), nullable=True),
            sa.Column("exit_reason", sa.String(100), nullable=True),
            sa.Column("leverage", sa.Float(), nullable=True),
            sa.ForeignKeyConstraint(["backtest_id"], ["backtest_runs.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
    _create_index_if_missing("ix_trade_backtest_id", "backtest_trades", ["backtest_id"])
    _create_index_if_missing(
        "ix_trade_backtest_opened_at", "backtest_trades", ["backtest_id", "opened_at"]
    )

    if not _has_table("backtest_equity_points"):
        op.create_table(
            "backtest_equity_points",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("backtest_id", sa.Integer(), nullable=False),
            sa.Column("timestamp", sa.DateTime(), nullable=False),
            sa.Column("equity", sa.Float(), nullable=False),
            sa.Column("pnl_abs", sa.Float(), nullable=False),
            sa.Column("drawdown_pct", sa.Float(), nullable=False),
            sa.ForeignKeyConstraint(["backtest_id"], ["backtest_runs.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
    _create_index_if_missing(
        "ix_equity_backtest_id", "backtest_equity_points", ["backtest_id"]
    )
    _create_index_if_missing(
        "ix_equity_backtest_timestamp",
        "backtest_equity_points",
        ["backtest_id", "timestamp"],
    )

    if not _has_table("strategy_definitions"):
        op.create_table(
            "strategy_definitions",
            sa.Column("key", sa.String(50), nullable=False),
            sa.Column("name", sa.String(100), nullable=False),
            sa.Column("template", sa.String(50), nullable=False),
            sa.Column("category", sa.String(50), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("key"),
        )

    if not _has_table("strategy_versions"):
        op.create_table(
            "strategy_versions",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("strategy_key", sa.String(50), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(100), nullable=False),
            sa.Column("config", sa.JSON(), nullable=False),
            sa.Column("parameter_space", sa.JSON(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("is_default", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["strategy_key"], ["strategy_definitions.key"]),
            sa.PrimaryKeyConstraint("id"),
        )
    _create_index_if_missing(
        "ix_strategy_version_key_version",
        "strategy_versions",
        ["strategy_key", "version"],
        unique=True,
    )
    _create_index_if_missing(
        "ix_strategy_version_default",
        "strategy_versions",
        ["strategy_key", "is_default"],
    )

    if not _has_table("indicator_definitions"):
        op.create_table(
            "indicator_definitions",
            sa.Column("key", sa.String(50), nullable=False),
            sa.Column("name", sa.String(100), nullable=False),
            sa.Column("engine", sa.String(50), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("outputs", sa.JSON(), nullable=False),
            sa.Column("params", sa.JSON(), nullable=False),
            sa.Column("is_builtin", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("key"),
        )

    if not _has_table("strategy_template_definitions"):
        op.create_table(
            "strategy_template_definitions",
            sa.Column("key", sa.String(50), nullable=False),
            sa.Column("name", sa.String(100), nullable=False),
            sa.Column("category", sa.String(50), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("indicator_keys", sa.JSON(), nullable=False),
            sa.Column("default_config", sa.JSON(), nullable=False),
            sa.Column("default_parameter_space", sa.JSON(), nullable=True),
            sa.Column("is_builtin", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("key"),
        )

    if not _has_table("funding_rates"):
        op.create_table(
            "funding_rates",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("exchange", sa.String(20), nullable=False),
            sa.Column("market_type", sa.String(20), nullable=False),
            sa.Column("symbol", sa.String(30), nullable=False),
            sa.Column("funding_time", sa.DateTime(), nullable=False),
            sa.Column("funding_rate", sa.Float(), nullable=False),
            sa.Column("mark_price", sa.Float(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
    _create_index_if_missing(
        "ix_funding_rate_symbol_time",
        "funding_rates",
        ["exchange", "market_type", "symbol", "funding_time"],
        unique=True,
    )
    _create_index_if_missing(
        "ix_funding_rate_symbol_lookup", "funding_rates", ["symbol", "funding_time"]
    )

    if not _has_table("factor_datasets"):
        op.create_table(
            "factor_datasets",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("signature", sa.String(128), nullable=False),
            sa.Column("symbol", sa.String(20), nullable=False),
            sa.Column("timeframe", sa.String(10), nullable=False),
            sa.Column("start_date", sa.DateTime(), nullable=False),
            sa.Column("end_date", sa.DateTime(), nullable=False),
            sa.Column("primary_horizon", sa.Integer(), nullable=False),
            sa.Column("forward_horizons", sa.JSON(), nullable=False),
            sa.Column("factor_ids", sa.JSON(), nullable=False),
            sa.Column("categories", sa.JSON(), nullable=False),
            sa.Column("cleaning", sa.JSON(), nullable=False),
            sa.Column("row_count", sa.Integer(), nullable=False),
            sa.Column("dataset_info", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("signature"),
        )
    _create_index_if_missing(
        "ix_factor_dataset_signature", "factor_datasets", ["signature"], unique=True
    )
    _create_index_if_missing(
        "ix_factor_dataset_symbol_tf", "factor_datasets", ["symbol", "timeframe"]
    )

    if not _has_table("factor_dataset_rows"):
        op.create_table(
            "factor_dataset_rows",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("dataset_id", sa.Integer(), nullable=False),
            sa.Column("timestamp", sa.DateTime(), nullable=False),
            sa.Column("close", sa.Float(), nullable=False),
            sa.Column("volume", sa.Float(), nullable=False),
            sa.Column("raw_values", sa.JSON(), nullable=False),
            sa.Column("feature_values", sa.JSON(), nullable=False),
            sa.Column("labels", sa.JSON(), nullable=False),
            sa.ForeignKeyConstraint(["dataset_id"], ["factor_datasets.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
    _create_index_if_missing(
        "ix_factor_dataset_row_dataset_ts",
        "factor_dataset_rows",
        ["dataset_id", "timestamp"],
        unique=True,
    )

    if not _has_table("factor_research_runs"):
        op.create_table(
            "factor_research_runs",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("dataset_id", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(20), nullable=False),
            sa.Column("request_payload", sa.JSON(), nullable=False),
            sa.Column("summary", sa.JSON(), nullable=False),
            sa.Column("ranking", sa.JSON(), nullable=False),
            sa.Column("details", sa.JSON(), nullable=False),
            sa.Column("blend", sa.JSON(), nullable=False),
            sa.Column("error", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["dataset_id"], ["factor_datasets.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
    _create_index_if_missing(
        "ix_factor_research_run_dataset_id", "factor_research_runs", ["dataset_id"]
    )
    _create_index_if_missing(
        "ix_factor_research_run_created_at", "factor_research_runs", ["created_at"]
    )


def downgrade() -> None:
    for table in [
        "factor_research_runs",
        "factor_dataset_rows",
        "factor_datasets",
        "funding_rates",
        "strategy_versions",
        "strategy_definitions",
        "strategy_template_definitions",
        "indicator_definitions",
        "backtest_equity_points",
        "backtest_trades",
    ]:
        if _has_table(table):
            op.drop_table(table)
    if _has_column("backtest_runs", "engine"):
        with op.batch_alter_table("backtest_runs") as batch_op:
            batch_op.drop_column("engine")
    if _has_column("backtest_runs", "execution_mode"):
        with op.batch_alter_table("backtest_runs") as batch_op:
            batch_op.drop_column("execution_mode")
