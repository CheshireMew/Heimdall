from __future__ import annotations

from alembic import op
import sqlalchemy as sa


def inspector() -> sa.Inspector:
    return sa.inspect(op.get_bind())


def has_table(table: str) -> bool:
    return table in set(inspector().get_table_names())


def has_column(table: str, column: str) -> bool:
    if not has_table(table):
        return False
    return column in {item["name"] for item in inspector().get_columns(table)}


def has_index(table: str, index: str) -> bool:
    if not has_table(table):
        return False
    return index in {item["name"] for item in inspector().get_indexes(table)}


def create_index_if_missing(
    name: str,
    table: str,
    columns: list[str],
    *,
    unique: bool = False,
) -> None:
    if not has_index(table, name):
        op.create_index(name, table, columns, unique=unique)
