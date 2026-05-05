"""persist Binance market research series

Revision ID: 004_market_research_series
Revises: 003_current_schema
Create Date: 2026-05-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from alembic_support import create_index_if_missing, has_table

revision: str = "004_market_research_series"
down_revision: Union[str, None] = "003_current_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if not has_table("binance_market_research_series"):
        op.create_table(
            "binance_market_research_series",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("market", sa.String(20), nullable=False),
            sa.Column("series", sa.String(60), nullable=False),
            sa.Column("symbol", sa.String(40), nullable=False),
            sa.Column("period", sa.String(20), nullable=False, server_default=""),
            sa.Column("contract_type", sa.String(30), nullable=False, server_default=""),
            sa.Column("item_key", sa.String(80), nullable=False),
            sa.Column("timestamp", sa.BigInteger(), nullable=False),
            sa.Column("payload", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
    create_index_if_missing(
        "ix_binance_market_research_unique",
        "binance_market_research_series",
        ["market", "series", "symbol", "period", "contract_type", "item_key"],
        unique=True,
    )
    create_index_if_missing(
        "ix_binance_market_research_lookup",
        "binance_market_research_series",
        ["market", "series", "symbol", "period", "contract_type", "timestamp"],
    )


def downgrade() -> None:
    if has_table("binance_market_research_series"):
        op.drop_index("ix_binance_market_research_lookup", table_name="binance_market_research_series")
        op.drop_index("ix_binance_market_research_unique", table_name="binance_market_research_series")
        op.drop_table("binance_market_research_series")
