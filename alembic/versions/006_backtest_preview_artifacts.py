"""Persist backtest preview artifacts.

Revision ID: 006_backtest_preview_artifacts
Revises: 005_backtest_trade_side
Create Date: 2026-05-14
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

from alembic_support import create_index_if_missing, has_table


revision = "006_backtest_preview_artifacts"
down_revision = "005_backtest_trade_side"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if not has_table("backtest_preview_artifacts"):
        op.create_table(
            "backtest_preview_artifacts",
            sa.Column("preview_id", sa.String(length=64), nullable=False),
            sa.Column("fingerprint", sa.String(length=128), nullable=False),
            sa.Column("command_payload", sa.JSON(), nullable=False),
            sa.Column("artifact", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("preview_id"),
        )
    create_index_if_missing(
        "ix_backtest_preview_created_at",
        "backtest_preview_artifacts",
        ["created_at"],
    )


def downgrade() -> None:
    if has_table("backtest_preview_artifacts"):
        op.drop_table("backtest_preview_artifacts")
