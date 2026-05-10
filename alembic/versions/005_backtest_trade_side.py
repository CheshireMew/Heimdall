"""Persist backtest trade side.

Revision ID: 005_backtest_trade_side
Revises: 004_market_research_series
Create Date: 2026-05-09
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect


revision = "005_backtest_trade_side"
down_revision = "004_market_research_series"
branch_labels = None
depends_on = None


def has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    inspector = inspect(bind)
    if table not in inspector.get_table_names():
        return False
    return column in {item["name"] for item in inspector.get_columns(table)}


def upgrade() -> None:
    if not has_column("backtest_trades", "side"):
        with op.batch_alter_table("backtest_trades") as batch_op:
            batch_op.add_column(
                sa.Column("side", sa.String(length=10), nullable=False, server_default="long")
            )
    with op.batch_alter_table("backtest_trades") as batch_op:
        batch_op.alter_column("side", server_default=None)


def downgrade() -> None:
    if has_column("backtest_trades", "side"):
        with op.batch_alter_table("backtest_trades") as batch_op:
            batch_op.drop_column("side")
