from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from app.infra.db.database import session_scope
from app.infra.db.schema import BacktestEquityPoint, BacktestRun
from app.services.backtest.contracts import PaperStartCommand
from app.services.backtest.models import BacktestEquityPointRecord, BacktestSignalRecord, BacktestTradeRecord
from app.services.backtest.run_repository import BacktestRunRepository
from app.services.backtest.run_contract import PAPER_LIVE_ENGINE, PAPER_LIVE_EXECUTION_MODE, build_paper_metadata, update_paper_metadata
from config import settings
from utils.time_utils import utc_now_naive
from utils.logger import logger

if TYPE_CHECKING:
    from app.services.backtest.freqtrade_report_builder import FreqtradeReportBuilder
    from app.services.backtest.paper_persistence_service import PaperPersistenceService
    from app.services.backtest.paper_position_service import PaperPosition, PaperPositionService
    from app.services.backtest.paper_runtime_service import PaperRuntimeService
    from app.services.backtest.strategy_query_service import StrategyQueryService
    from app.services.backtest.strategy_runtime import StrategyRuntime


class PaperRunManager:
    def __init__(
        self,
        *,
        strategy_query_service: StrategyQueryService | None = None,
        runtime: StrategyRuntime | None = None,
        report_builder: FreqtradeReportBuilder | None = None,
        position_service: PaperPositionService | None = None,
        persistence_service: PaperPersistenceService | None = None,
        runtime_service: PaperRuntimeService | None = None,
        run_repository: BacktestRunRepository,
    ) -> None:
        self.strategy_query_service = strategy_query_service
        self.runtime = runtime
        self.report_builder = report_builder
        self.position_service = position_service
        self.runtime_service = runtime_service
        self.persistence_service = persistence_service
        self.run_repository = run_repository
        self._tasks: dict[int, asyncio.Task[Any]] = {}

    async def restore_active_runs(self) -> None:
        loop = asyncio.get_running_loop()
        run_ids = await loop.run_in_executor(None, self._list_active_run_ids)
        for run_id in run_ids:
            self._ensure_task(run_id, initial_delay=float(settings.WS_UPDATE_INTERVAL))

    async def shutdown(self) -> None:
        tasks = list(self._tasks.values())
        self._tasks.clear()
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def start_run(self, command: PaperStartCommand) -> dict[str, Any]:
        loop = asyncio.get_running_loop()
        run_id = await loop.run_in_executor(None, lambda: self._create_run(command))
        self._ensure_task(run_id)
        return {"success": True, "run_id": run_id, "message": "模拟盘已启动"}

    async def stop_run(self, run_id: int) -> dict[str, Any]:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, lambda: self._mark_stopped(run_id, "stopped", "manual_stop"))
        task = self._tasks.pop(run_id, None)
        if task:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        return {"success": True, "run_id": run_id, "message": "模拟盘已停止"}

    async def delete_run(self, run_id: int) -> dict[str, Any]:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, lambda: self._mark_stopped(run_id, "stopped", "manual_delete"))
        task = self._tasks.pop(run_id, None)
        if task:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)

        deleted = await loop.run_in_executor(
            None,
            lambda: self.run_repository.delete_run(run_id, "paper_live"),
        )
        if not deleted:
            raise ValueError(f"模拟盘记录不存在: {run_id}")
        return {"success": True, "run_id": run_id, "message": "模拟盘记录已删除"}

    def _ensure_task(self, run_id: int, *, initial_delay: float = 0.0) -> None:
        task = self._tasks.get(run_id)
        if task and not task.done():
            return
        self._tasks[run_id] = asyncio.create_task(self._run_loop(run_id, initial_delay=initial_delay))

    async def _run_loop(self, run_id: int, *, initial_delay: float = 0.0) -> None:
        try:
            if initial_delay > 0:
                await asyncio.sleep(initial_delay)
            while True:
                loop = asyncio.get_running_loop()
                should_continue = await loop.run_in_executor(None, lambda: self._tick(run_id))
                if not should_continue:
                    self._tasks.pop(run_id, None)
                    return
                await asyncio.sleep(settings.WS_UPDATE_INTERVAL)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.error(f"模拟盘运行失败 run_id={run_id}: {exc}", exc_info=True)
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, lambda: self._mark_stopped(run_id, "failed", str(exc)))
            self._tasks.pop(run_id, None)

    def _tick(self, run_id: int) -> bool:
        with session_scope() as session:
            run = session.query(BacktestRun).filter(BacktestRun.id == run_id).first()
            if not run:
                return False
            metadata = dict(run.metadata_info or {})
            if run.execution_mode != PAPER_LIVE_EXECUTION_MODE or run.engine != PAPER_LIVE_ENGINE or run.status != "running":
                return False

            strategy = self._get_strategy_query_service().get_strategy_version(metadata["strategy_key"], metadata.get("strategy_version"))
            runtime_service = self._get_runtime_service()
            runtime_state = runtime_service.load_runtime_state(metadata)
            symbols = list(metadata.get("symbols") or [])
            now = utc_now_naive()
            fee_ratio = float(metadata.get("fee_rate", 0.0)) / 100.0
            runtime = self._get_runtime()
            pending = runtime_service.build_pending_snapshots(
                strategy=strategy,
                symbols=symbols,
                timeframe=run.timeframe,
                runtime_state=runtime_state,
                now=now,
                warmup_bars=runtime.warmup_bars(strategy.template, strategy.config, run.timeframe),
            )
            if not pending:
                return True

            new_signals: list[BacktestSignalRecord] = []
            new_trades: list[BacktestTradeRecord] = []
            new_equity_points: list[BacktestEquityPointRecord] = []
            position_service = self._get_position_service()
            positions = position_service.deserialize_positions(runtime_state.get("positions") or {})
            cash_balance = float(runtime_state.get("cash_balance", metadata.get("initial_cash", 0.0)))
            portfolio = metadata.get("portfolio") or {}
            risk = strategy.config.get("risk") or {}
            initial_cash = float(metadata.get("initial_cash", 0.0))

            for symbol, snapshot in pending:
                run.total_candles += 1
                position = positions.get(symbol)
                if position:
                    signals, trades = position_service.process_open_position(
                        position=position,
                        snapshot=snapshot,
                        fee_ratio=fee_ratio,
                        risk=risk,
                    )
                    new_signals.extend(signals)
                    new_trades.extend(trades)
                    for trade in trades:
                        cash_balance += trade.stake_amount + trade.profit_abs
                    if position.remaining_amount <= 1e-12 or position.remaining_cost <= 1e-8:
                        positions.pop(symbol, None)
                entry_side = position_service.entry_side(snapshot)
                if symbol not in positions and entry_side and len(positions) < int(portfolio.get("max_open_trades", 1)):
                    created_position, entry_signal, cash_spent = position_service.try_open_position(
                        symbol=symbol,
                        snapshot=snapshot,
                        side=entry_side,
                        cash_balance=cash_balance,
                        fee_ratio=fee_ratio,
                        portfolio=portfolio,
                        initial_cash=initial_cash,
                    )
                    if created_position:
                        positions[symbol] = created_position
                        new_signals.append(entry_signal)
                        cash_balance -= cash_spent

                runtime_state.setdefault("last_processed", {})[symbol] = int(snapshot.timestamp.timestamp() * 1000)
                equity = position_service.current_equity(cash_balance, positions, snapshot.price, symbol, fee_ratio)
                new_equity_points.append(
                    BacktestEquityPointRecord(
                        timestamp=snapshot.timestamp,
                        equity=equity,
                        pnl_abs=equity - initial_cash,
                        drawdown_pct=0.0,
                    )
                )

            self._get_persistence_service().persist_increment(
                session=session,
                run=run,
                metadata=metadata,
                runtime_state=runtime_state,
                positions=positions,
                cash_balance=cash_balance,
                new_signals=new_signals,
                new_trades=new_trades,
                new_equity_points=new_equity_points,
                now=now,
            )
            return True

    def _create_run(self, command: PaperStartCommand) -> int:
        strategy = self._get_strategy_query_service().get_strategy_version(command.strategy_key, command.strategy_version)
        now = utc_now_naive()
        symbols = list(command.portfolio.symbols)
        runtime_service = self._get_runtime_service()
        timeframe_delta = runtime_service.timeframe_delta(command.timeframe)
        baseline_last_processed = {
            symbol: runtime_service.latest_closed_timestamp(symbol, command.timeframe, now, timeframe_delta)
            for symbol in symbols
        }
        report_builder = self._get_report_builder()
        initial_report = report_builder.build_report(
            trades=[],
            equity_curve=[BacktestEquityPointRecord(timestamp=now, equity=command.initial_cash, pnl_abs=0.0, drawdown_pct=0.0)],
            initial_cash=command.initial_cash,
            start_date=now,
            end_date=now,
        )
        initial_report["strategy"] = {
            "key": strategy.strategy_key,
            "name": strategy.strategy_name,
            "version": strategy.version,
            "template": strategy.template,
        }
        initial_report["portfolio"] = {
            "symbols": symbols,
            "max_open_trades": command.portfolio.max_open_trades,
            "position_size_pct": command.portfolio.position_size_pct,
            "stake_mode": command.portfolio.stake_mode,
            "stake_currency": report_builder.quote_currency(symbols[0]),
        }
        with session_scope() as session:
            run = BacktestRun(
                symbol=symbols[0] if len(symbols) == 1 else "PORTFOLIO",
                timeframe=command.timeframe,
                start_date=now,
                end_date=now,
                status="running",
                execution_mode=PAPER_LIVE_EXECUTION_MODE,
                engine=PAPER_LIVE_ENGINE,
                metadata_info=build_paper_metadata(
                    strategy=strategy,
                    symbols=symbols,
                    initial_cash=command.initial_cash,
                    fee_rate=command.fee_rate,
                    portfolio=command.portfolio,
                    runtime_state={"cash_balance": command.initial_cash, "last_processed": baseline_last_processed, "positions": {}},
                    paper_live={"cash_balance": command.initial_cash, "open_positions": 0, "positions": [], "last_updated": now.isoformat()},
                    report=initial_report,
                ),
            )
            session.add(run)
            session.flush()
            session.add(BacktestEquityPoint(backtest_id=run.id, timestamp=now, equity=command.initial_cash, pnl_abs=0.0, drawdown_pct=0.0))
            session.flush()
            return run.id

    def _mark_stopped(self, run_id: int, status: str, reason: str) -> None:
        with session_scope() as session:
            run = session.query(BacktestRun).filter(BacktestRun.id == run_id).first()
            if not run:
                return
            metadata = dict(run.metadata_info or {})
            if run.execution_mode != PAPER_LIVE_EXECUTION_MODE or run.engine != PAPER_LIVE_ENGINE:
                return
            run.status = status
            run.metadata_info = update_paper_metadata(
                metadata,
                runtime_state=dict(metadata.get("runtime_state") or {}),
                last_updated=utc_now_naive().isoformat(),
                stop_reason=reason,
            )
            session.flush()

    def _list_active_run_ids(self) -> list[int]:
        return self.run_repository.list_active_run_ids(
            execution_mode=PAPER_LIVE_EXECUTION_MODE,
            engine=PAPER_LIVE_ENGINE,
        )

    def _get_strategy_query_service(self) -> StrategyQueryService:
        if self.strategy_query_service is None:
            from app.dependencies import get_strategy_query_service

            self.strategy_query_service = get_strategy_query_service()
        return self.strategy_query_service

    def _get_runtime(self) -> StrategyRuntime:
        if self.runtime is None:
            from app.dependencies import get_strategy_runtime

            self.runtime = get_strategy_runtime()
        return self.runtime

    def _get_report_builder(self) -> FreqtradeReportBuilder:
        if self.report_builder is None:
            from app.dependencies import get_freqtrade_report_builder

            self.report_builder = get_freqtrade_report_builder()
        return self.report_builder

    def _get_position_service(self) -> PaperPositionService:
        if self.position_service is None:
            from app.dependencies import get_paper_position_service

            self.position_service = get_paper_position_service()
        return self.position_service

    def _get_runtime_service(self) -> PaperRuntimeService:
        if self.runtime_service is None:
            from app.dependencies import get_paper_runtime_service

            self.runtime_service = get_paper_runtime_service()
        return self.runtime_service

    def _get_persistence_service(self) -> PaperPersistenceService:
        if self.persistence_service is None:
            from app.dependencies import get_paper_persistence_service

            self.persistence_service = get_paper_persistence_service()
        return self.persistence_service
