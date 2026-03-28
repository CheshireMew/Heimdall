from __future__ import annotations

from datetime import datetime, timezone

from app.services.backtest import FreqtradeBacktestService
from app.services.backtest.models import PortfolioConfigRecord, ResearchConfigRecord, StrategyVersionRecord
from app.services.backtest.run_contract import BACKTEST_EXECUTION_MODE, FREQTRADE_ENGINE, build_backtest_metadata, make_json_safe
from config import settings
from app.infra.db.database import session_scope
from app.infra.db.schema import BacktestEquityPoint, BacktestRun, BacktestSignal, BacktestTrade
from utils.logger import logger


class BacktestRunService:
    def __init__(self, engine: FreqtradeBacktestService) -> None:
        self.engine = engine

    def run_backtest(
        self,
        *,
        strategy: StrategyVersionRecord,
        portfolio: PortfolioConfigRecord,
        research: ResearchConfigRecord,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = settings.TIMEFRAME,
        initial_cash: float = settings.BACKTEST_INITIAL_CASH,
        fee_rate: float = settings.BACKTEST_DEFAULT_FEE_RATE,
    ) -> int | None:
        symbols = list(portfolio.symbols)
        display_symbol = symbols[0] if len(symbols) == 1 else "PORTFOLIO"
        logger.info(
            f"开始 Freqtrade 回测: strategy={strategy.strategy_key} v{strategy.version}, "
            f"symbols={','.join(symbols)}, range=({start_date} - {end_date})"
        )

        with session_scope() as session:
            backtest_run = BacktestRun(
                symbol=display_symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date,
                status="running",
                execution_mode=BACKTEST_EXECUTION_MODE,
                engine=FREQTRADE_ENGINE,
                metadata_info=build_backtest_metadata(
                    strategy=strategy,
                    symbols=symbols,
                    initial_cash=initial_cash,
                    fee_rate=fee_rate,
                    portfolio=portfolio,
                    research=research,
                ),
            )
            session.add(backtest_run)
            session.flush()
            backtest_id = backtest_run.id

            try:
                result = self.engine.execute(
                    strategy=strategy,
                    portfolio=portfolio,
                    research=research,
                    start_date=start_date,
                    end_date=end_date,
                    timeframe=timeframe,
                    initial_cash=initial_cash,
                    fee_rate=fee_rate,
                )

                signal_records = [
                    BacktestSignal(
                        backtest_id=backtest_id,
                        timestamp=signal.timestamp.astimezone(timezone.utc)
                        if signal.timestamp.tzinfo
                        else signal.timestamp.replace(tzinfo=timezone.utc),
                        price=signal.price,
                        signal=signal.signal,
                        confidence=signal.confidence,
                        indicators=signal.indicators,
                        reasoning=signal.reasoning,
                    )
                    for signal in result.signals
                ]
                trade_records = [
                    BacktestTrade(
                        backtest_id=backtest_id,
                        pair=trade.pair or display_symbol,
                        opened_at=trade.opened_at.astimezone(timezone.utc)
                        if trade.opened_at.tzinfo
                        else trade.opened_at.replace(tzinfo=timezone.utc),
                        closed_at=trade.closed_at.astimezone(timezone.utc)
                        if trade.closed_at and trade.closed_at.tzinfo
                        else (trade.closed_at.replace(tzinfo=timezone.utc) if trade.closed_at else None),
                        entry_price=trade.entry_price,
                        exit_price=trade.exit_price,
                        stake_amount=trade.stake_amount,
                        amount=trade.amount,
                        profit_abs=trade.profit_abs,
                        profit_pct=trade.profit_pct,
                        max_drawdown_pct=trade.max_drawdown_pct,
                        duration_minutes=trade.duration_minutes,
                        entry_tag=trade.entry_tag,
                        exit_reason=trade.exit_reason,
                        leverage=trade.leverage,
                    )
                    for trade in result.trades
                ]
                equity_points = [
                    BacktestEquityPoint(
                        backtest_id=backtest_id,
                        timestamp=point.timestamp.astimezone(timezone.utc)
                        if point.timestamp.tzinfo
                        else point.timestamp.replace(tzinfo=timezone.utc),
                        equity=point.equity,
                        pnl_abs=point.pnl_abs,
                        drawdown_pct=point.drawdown_pct,
                    )
                    for point in result.equity_curve
                ]

                if signal_records:
                    session.bulk_save_objects(signal_records)
                if trade_records:
                    session.bulk_save_objects(trade_records)
                if equity_points:
                    session.bulk_save_objects(equity_points)

                buy_count = sum(1 for signal in result.signals if signal.signal == "BUY")
                sell_count = sum(1 for signal in result.signals if signal.signal == "SELL")
                hold_count = max(result.total_candles - len(result.signals), 0)

                merged_metadata = dict(backtest_run.metadata_info or {})
                merged_metadata.update(result.metadata)
                merged_metadata["report"] = result.report

                backtest_run.status = "completed"
                backtest_run.metadata_info = make_json_safe(merged_metadata)
                backtest_run.total_candles = result.total_candles
                backtest_run.total_signals = len(result.signals)
                backtest_run.buy_signals = buy_count
                backtest_run.sell_signals = sell_count
                backtest_run.hold_signals = hold_count
                session.commit()

                logger.info(
                    f"Freqtrade 回测完成: ID={backtest_id}, candles={result.total_candles}, "
                    f"signals={len(result.signals)}, buy={buy_count}, sell={sell_count}"
                )
                return backtest_id
            except Exception as exc:
                logger.error(f"Freqtrade 回测执行失败: {exc}", exc_info=True)
                session.rollback()
                backtest_run.status = "failed"
                backtest_run.metadata_info = make_json_safe({
                    **(backtest_run.metadata_info or {}),
                    "error": str(exc),
                })
                session.commit()
                return None
