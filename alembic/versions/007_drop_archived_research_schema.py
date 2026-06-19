"""drop archived research schema

Revision ID: 007_drop_archived_research_schema
Revises: 006_backtest_preview_artifacts
Create Date: 2026-06-19
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

from alembic_support import has_table


revision: str = "007_drop_archived_research_schema"
down_revision: Union[str, None] = "006_backtest_preview_artifacts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ARCHIVED_RESEARCH_TABLES: tuple[str, ...] = (
    "backtest_preview_artifacts",
    "factor_research_runs",
    "factor_dataset_rows",
    "factor_datasets",
    "backtest_equity_points",
    "backtest_trades",
    "backtest_signals",
    "backtest_runs",
    "strategy_versions",
    "strategy_definitions",
    "strategy_template_definitions",
    "indicator_definitions",
)


def upgrade() -> None:
    for table_name in ARCHIVED_RESEARCH_TABLES:
        if has_table(table_name):
            op.drop_table(table_name)


def downgrade() -> None:
    pass
