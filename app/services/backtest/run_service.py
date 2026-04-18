from __future__ import annotations

from datetime import datetime

from app.services.backtest.freqtrade_service import FreqtradeBacktestService
from app.services.backtest.models import PortfolioConfigRecord, ResearchConfigRecord, StrategyVersionRecord
from app.services.backtest.result_store import replace_run_rows, result_signal_counts
from app.services.backtest.run_contract import (
    BACKTEST_EXECUTION_MODE,
    FREQTRADE_ENGINE,
    build_backtest_metadata,
    make_json_safe,
)
from config import settings
from app.infra.db.database import session_scope
from app.infra.db.schema import BacktestRun
from utils.logger import logger


class BacktestRunService:
    def __init__(self, *, execution_engine: FreqtradeBacktestService) -> None:
        self.execution_engine = execution_engine

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
            f"开始回测: engine={FREQTRADE_ENGINE}, strategy={strategy.strategy_key} v{strategy.version}, "
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
                result = self.execution_engine.execute(
                    strategy=strategy,
                    portfolio=portfolio,
                    research=research,
                    start_date=start_date,
                    end_date=end_date,
                    timeframe=timeframe,
                    initial_cash=initial_cash,
                    fee_rate=fee_rate,
                )

                replace_run_rows(
                    session=session,
                    run_id=backtest_id,
                    result=result,
                    default_pair=display_symbol,
                    clear_existing=False,
                )

                buy_count, sell_count, hold_count = result_signal_counts(result)

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
                    f"{FREQTRADE_ENGINE} 回测完成: ID={backtest_id}, candles={result.total_candles}, "
                    f"signals={len(result.signals)}, buy={buy_count}, sell={sell_count}"
                )
                return backtest_id
            except Exception as exc:
                logger.error(f"{FREQTRADE_ENGINE} 回测执行失败: {exc}", exc_info=True)
                session.rollback()
                backtest_run.status = "failed"
                backtest_run.metadata_info = make_json_safe({
                    **(backtest_run.metadata_info or {}),
                    "error": str(exc),
                })
                session.commit()
                return None
