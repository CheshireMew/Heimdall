"""initial schema - all existing tables

Revision ID: 001_initial
Revises: None
Create Date: 2026-02-28
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # BacktestRun
    op.create_table(
        'backtest_runs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('symbol', sa.String(20), nullable=False),
        sa.Column('timeframe', sa.String(10), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(20), nullable=True),
        sa.Column('total_candles', sa.Integer(), nullable=True),
        sa.Column('total_signals', sa.Integer(), nullable=True),
        sa.Column('buy_signals', sa.Integer(), nullable=True),
        sa.Column('sell_signals', sa.Integer(), nullable=True),
        sa.Column('hold_signals', sa.Integer(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    # BacktestSignal
    op.create_table(
        'backtest_signals',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('backtest_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('signal', sa.String(10), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('indicators', sa.JSON(), nullable=True),
        sa.Column('reasoning', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['backtest_id'], ['backtest_runs.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_signal_backtest_id', 'backtest_signals', ['backtest_id'])

    # Kline
    op.create_table(
        'klines',
        sa.Column('symbol', sa.String(80), nullable=False),
        sa.Column('timeframe', sa.String(10), nullable=False),
        sa.Column('timestamp', sa.BigInteger(), nullable=False),
        sa.Column('open', sa.Float(), nullable=False),
        sa.Column('high', sa.Float(), nullable=False),
        sa.Column('low', sa.Float(), nullable=False),
        sa.Column('close', sa.Float(), nullable=False),
        sa.Column('volume', sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint('symbol', 'timeframe', 'timestamp'),
    )
    op.create_index('ix_kline_sym_tf_ts', 'klines', ['symbol', 'timeframe', 'timestamp'])

    # Sentiment
    op.create_table(
        'sentiment',
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('value', sa.Integer(), nullable=False),
        sa.Column('classification', sa.String(20), nullable=True),
        sa.Column('timestamp', sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint('date'),
    )

    # MarketIndicatorMeta
    op.create_table(
        'market_indicator_meta',
        sa.Column('id', sa.String(50), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('unit', sa.String(20), nullable=True),
        sa.Column('frequency', sa.String(20), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    # MarketIndicatorData
    op.create_table(
        'market_indicator_data',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('indicator_id', sa.String(50), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['indicator_id'], ['market_indicator_meta.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_indicator_data_id_ts', 'market_indicator_data', ['indicator_id', 'timestamp'])


def downgrade() -> None:
    op.drop_table('market_indicator_data')
    op.drop_table('market_indicator_meta')
    op.drop_table('sentiment')
    op.drop_table('klines')
    op.drop_table('backtest_signals')
    op.drop_table('backtest_runs')
