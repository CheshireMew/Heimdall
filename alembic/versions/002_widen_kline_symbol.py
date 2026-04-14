"""widen kline symbol

Revision ID: 002_widen_kline_symbol
Revises: 001_initial
Create Date: 2026-04-13 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "002_widen_kline_symbol"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("klines") as batch_op:
        batch_op.alter_column(
            "symbol",
            existing_type=sa.String(length=20),
            type_=sa.String(length=80),
            existing_nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("klines") as batch_op:
        batch_op.alter_column(
            "symbol",
            existing_type=sa.String(length=80),
            type_=sa.String(length=20),
            existing_nullable=False,
        )
