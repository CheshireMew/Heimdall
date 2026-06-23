"""drop funding rates cache

Revision ID: 008_drop_funding_rates
Revises: 007_drop_research_schema
Create Date: 2026-06-23
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

from alembic_support import has_table


revision: str = "008_drop_funding_rates"
down_revision: Union[str, None] = "007_drop_research_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if has_table("funding_rates"):
        op.drop_table("funding_rates")


def downgrade() -> None:
    pass
