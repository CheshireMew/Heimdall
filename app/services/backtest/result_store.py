from __future__ import annotations

from datetime import datetime

import pandas as pd

from app.infra.db.schema import BacktestEquityPoint, BacktestSignal, BacktestTrade


def replace_run_rows(*, session, run_id: int, result, default_pair: str, clear_existing: bool) -> None:
    if clear_existing:
        session.query(BacktestSignal).filter(BacktestSignal.backtest_id == run_id).delete(synchronize_session=False)
        session.query(BacktestTrade).filter(BacktestTrade.backtest_id == run_id).delete(synchronize_session=False)
        session.query(BacktestEquityPoint).filter(BacktestEquityPoint.backtest_id == run_id).delete(synchronize_session=False)

    signal_rows = [
        BacktestSignal(
            backtest_id=run_id,
            timestamp=normalize_timestamp(item.timestamp),
            price=item.price,
            signal=item.signal,
            confidence=item.confidence,
            indicators=item.indicators,
            reasoning=item.reasoning,
        )
        for item in result.signals
    ]
    trade_rows = [
        BacktestTrade(
            backtest_id=run_id,
            pair=item.pair or default_pair,
            opened_at=normalize_timestamp(item.opened_at),
            closed_at=normalize_timestamp(item.closed_at),
            entry_price=item.entry_price,
            exit_price=item.exit_price,
            stake_amount=item.stake_amount,
            amount=item.amount,
            profit_abs=item.profit_abs,
            profit_pct=item.profit_pct,
            max_drawdown_pct=item.max_drawdown_pct,
            duration_minutes=item.duration_minutes,
            entry_tag=item.entry_tag,
            exit_reason=item.exit_reason,
            leverage=item.leverage,
        )
        for item in result.trades
    ]
    equity_rows = [
        BacktestEquityPoint(
            backtest_id=run_id,
            timestamp=normalize_timestamp(item.timestamp),
            equity=item.equity,
            pnl_abs=item.pnl_abs,
            drawdown_pct=item.drawdown_pct,
        )
        for item in result.equity_curve
    ]

    if signal_rows:
        session.bulk_save_objects(signal_rows)
    if trade_rows:
        session.bulk_save_objects(trade_rows)
    if equity_rows:
        session.bulk_save_objects(equity_rows)
    session.flush()


def result_signal_counts(result) -> tuple[int, int, int]:
    buy_count = sum(1 for item in result.signals if item.signal == "BUY")
    sell_count = sum(1 for item in result.signals if item.signal == "SELL")
    hold_count = max(int(result.total_candles) - len(result.signals), 0)
    return buy_count, sell_count, hold_count


def normalize_timestamp(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.to_pydatetime().replace(tzinfo=None)
    return timestamp.tz_convert("UTC").to_pydatetime().replace(tzinfo=None)
