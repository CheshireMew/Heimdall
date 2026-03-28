from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from app.infra.db.database import session_scope
from app.infra.db.schema import BacktestEquityPoint, BacktestRun
from app.services.backtest.contracts import PaperStartCommand
from app.services.backtest.freqtrade_report_builder import FreqtradeReportBuilder
from app.services.backtest.models import BacktestEquityPointRecord, BacktestSignalRecord, BacktestTradeRecord
from app.services.backtest.paper_persistence_service import PaperPersistenceService
from app.services.backtest.run_repository import BacktestRunRepository
from app.services.backtest.paper_position_service import PaperPosition, PaperPositionService
from app.services.backtest.paper_runtime_service import PaperRuntimeService
from app.services.backtest.run_contract import PAPER_LIVE_ENGINE, PAPER_LIVE_EXECUTION_MODE, build_paper_metadata, update_paper_metadata
from app.services.backtest.strategy_query_service import StrategyQueryService
from app.services.backtest.strategy_runtime import StrategyRuntime
from app.services.market.market_data_service import MarketDataService
from config import settings
from utils.logger import logger


def utc_now_naive() -> datetime:
    return datetime.now(datetime.UTC).replace(tzinfo=None)


class PaperRunManager:
    def __init__(
        self,
        *,
        market_data_service: MarketDataService,
        strategy_query_service: StrategyQueryService | None = None,
        runtime: StrategyRuntime | None = None,
        report_builder: FreqtradeReportBuilder | None = None,
        position_service: PaperPositionService | None = None,
        persistence_service: PaperPersistenceService | None = None,
        runtime_service: PaperRuntimeService | None = None,
        run_repository: BacktestRunRepository,
    ) -> None:
        self.market_data_service = market_data_service
        self.strategy_query_service = strategy_query_service or StrategyQueryService()
        self.runtime = runtime or StrategyRuntime()
        self.report_builder = report_builder or FreqtradeReportBuilder()
        self.position_service = position_service or PaperPositionService()
        self.runtime_service = runtime_service or PaperRuntimeService(self.market_data_service, self.runtime)
        self.persistence_service = persistence_service or PaperPersistenceService(
            report_builder=self.report_builder,
            position_service=self.position_service,
        )
        self.run_repository = run_repository
        self._tasks: dict[int, asyncio.Task[Any]] = {}

    async def restore_active_runs(self) -> None:
        loop = asyncio.get_running_loop()
        run_ids = await loop.run_in_executor(None, self._list_active_run_ids)
        for run_id in run_ids:
            self._ensure_task(run_id)

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

    def _ensure_task(self, run_id: int) -> None:
        task = self._tasks.get(run_id)
        if task and not task.done():
            return
        self._tasks[run_id] = asyncio.create_task(self._run_loop(run_id))

    async def _run_loop(self, run_id: int) -> None:
        try:
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

            strategy = self.strategy_query_service.get_strategy_version(metadata["strategy_key"], metadata.get("strategy_version"))
            runtime_state = self.runtime_service.load_runtime_state(metadata)
            symbols = list(metadata.get("symbols") or [])
            now = utc_now_naive()
            fee_ratio = float(metadata.get("fee_rate", 0.0)) / 100.0
            pending = self.runtime_service.build_pending_snapshots(
                strategy=strategy,
                symbols=symbols,
                timeframe=run.timeframe,
                runtime_state=runtime_state,
                now=now,
                warmup_bars=self.runtime.warmup_bars(strategy.template, strategy.config),
            )
            if not pending:
                return True

            new_signals: list[BacktestSignalRecord] = []
            new_trades: list[BacktestTradeRecord] = []
            new_equity_points: list[BacktestEquityPointRecord] = []
            positions = self.position_service.deserialize_positions(runtime_state.get("positions") or {})
            cash_balance = float(runtime_state.get("cash_balance", metadata.get("initial_cash", 0.0)))
            portfolio = metadata.get("portfolio") or {}
            risk = strategy.config.get("risk") or {}
            initial_cash = float(metadata.get("initial_cash", 0.0))

            for symbol, snapshot in pending:
                run.total_candles += 1
                position = positions.get(symbol)
                if position:
                    signals, trades = self.position_service.process_open_position(
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
                if symbol not in positions and snapshot.entry_signal and len(positions) < int(portfolio.get("max_open_trades", 1)):
                    created_position, entry_signal, cash_spent = self.position_service.try_open_position(
                        symbol=symbol,
                        snapshot=snapshot,
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
                equity = self.position_service.current_equity(cash_balance, positions, snapshot.price, symbol, fee_ratio)
                new_equity_points.append(
                    BacktestEquityPointRecord(
                        timestamp=snapshot.timestamp,
                        equity=equity,
                        pnl_abs=equity - initial_cash,
                        drawdown_pct=0.0,
                    )
                )

            self.persistence_service.persist_increment(
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
        strategy = self.strategy_query_service.get_strategy_version(command.strategy_key, command.strategy_version)
        now = utc_now_naive()
        symbols = list(command.portfolio.symbols)
        timeframe_delta = self.runtime_service.timeframe_delta(command.timeframe)
        baseline_last_processed = {
            symbol: self.runtime_service.latest_closed_timestamp(symbol, command.timeframe, now, timeframe_delta)
            for symbol in symbols
        }
        initial_report = self.report_builder.build_report(
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
            "stake_currency": self.report_builder.quote_currency(symbols[0]),
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
