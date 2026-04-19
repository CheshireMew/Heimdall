from __future__ import annotations

from datetime import datetime

from app.services.backtest.freqtrade_service import FreqtradeBacktestService
from app.contracts.backtest import PortfolioConfigRecord, ResearchConfigRecord, StrategyVersionRecord
from app.services.backtest.result_store import replace_run_rows, result_signal_counts
from app.services.backtest.run_contract import (
    BACKTEST_EXECUTION_MODE,
    FREQTRADE_ENGINE,
    build_completed_run_metadata,
    build_backtest_metadata,
    build_failed_run_metadata,
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
        backtest_id = self._create_run_record(
            strategy=strategy,
            portfolio=portfolio,
            research=research,
            start_date=start_date,
            end_date=end_date,
            timeframe=timeframe,
            initial_cash=initial_cash,
            fee_rate=fee_rate,
            display_symbol=display_symbol,
            symbols=symbols,
        )
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
        except Exception as exc:
            logger.error(f"{FREQTRADE_ENGINE} 回测执行失败: {exc}", exc_info=True)
            self._mark_run_failed(backtest_id=backtest_id, error=str(exc))
            return None
        self._store_completed_run(
            backtest_id=backtest_id,
            result=result,
            default_pair=display_symbol,
        )
        return backtest_id

    def _create_run_record(
        self,
        *,
        strategy: StrategyVersionRecord,
        portfolio: PortfolioConfigRecord,
        research: ResearchConfigRecord,
        start_date: datetime,
        end_date: datetime,
        timeframe: str,
        initial_cash: float,
        fee_rate: float,
        display_symbol: str,
        symbols: list[str],
    ) -> int:
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
            return int(backtest_run.id)

    def _store_completed_run(self, *, backtest_id: int, result, default_pair: str) -> None:
        with session_scope() as session:
            backtest_run = session.query(BacktestRun).filter(BacktestRun.id == backtest_id).first()
            if not backtest_run:
                raise ValueError(f"回测记录不存在: {backtest_id}")

            replace_run_rows(
                session=session,
                run_id=backtest_id,
                result=result,
                default_pair=default_pair,
                clear_existing=False,
            )

            buy_count, sell_count, hold_count = result_signal_counts(result)
            merged_metadata = build_completed_run_metadata(
                backtest_run.metadata_info,
                result_metadata=result.metadata,
                report=result.report,
            )
            displayed_start, displayed_end = self._resolve_displayed_range(
                metadata=result.metadata,
                fallback_start=backtest_run.start_date,
                fallback_end=backtest_run.end_date,
            )

            backtest_run.status = "completed"
            backtest_run.start_date = displayed_start
            backtest_run.end_date = displayed_end
            backtest_run.metadata_info = merged_metadata
            backtest_run.total_candles = result.total_candles
            backtest_run.total_signals = len(result.signals)
            backtest_run.buy_signals = buy_count
            backtest_run.sell_signals = sell_count
            backtest_run.hold_signals = hold_count

            logger.info(
                f"{FREQTRADE_ENGINE} 回测完成: ID={backtest_id}, candles={result.total_candles}, "
                f"signals={len(result.signals)}, buy={buy_count}, sell={sell_count}"
            )

    def _mark_run_failed(self, *, backtest_id: int, error: str) -> None:
        with session_scope() as session:
            backtest_run = session.query(BacktestRun).filter(BacktestRun.id == backtest_id).first()
            if not backtest_run:
                logger.error(f"无法写入失败状态，回测记录不存在: ID={backtest_id}")
                return
            backtest_run.status = "failed"
            backtest_run.metadata_info = build_failed_run_metadata(
                backtest_run.metadata_info,
                error=error,
            )

    def _resolve_displayed_range(
        self,
        *,
        metadata: dict,
        fallback_start: datetime,
        fallback_end: datetime,
    ) -> tuple[datetime, datetime]:
        sample_ranges = dict((metadata or {}).get("sample_ranges") or {})
        displayed = dict(sample_ranges.get("displayed") or {})
        start_text = displayed.get("start")
        end_text = displayed.get("end")
        if not start_text or not end_text:
            return fallback_start, fallback_end
        return datetime.fromisoformat(start_text), datetime.fromisoformat(end_text)
