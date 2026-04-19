from __future__ import annotations

import asyncio
from datetime import datetime
from typing import TYPE_CHECKING, Any

from app.infra.db.database import session_scope
from app.infra.db.schema import BacktestEquityPoint, BacktestRun
from app.contracts.backtest import BacktestEquityPointRecord, PortfolioConfigRecord, StrategyVersionRecord
from app.services.backtest.run_contract import (
    FACTOR_BLEND_PAPER_ENGINE,
    PAPER_LIVE_EXECUTION_MODE,
    build_paper_metadata,
    ensure_paper_runtime_state,
    parse_run_metadata,
    update_paper_metadata,
)
from app.services.backtest.run_repository import BacktestRunRepository
from app.services.backtest.strategy_support import blank_strategy_version_config_model
from app.services.run_task_manager import RunTaskManager
from app.services.factors.signal_execution_core import FactorSignalContext, FactorSignalExecutionCore
from config import settings
from utils.time_utils import utc_now_naive

if TYPE_CHECKING:
    from app.services.backtest.freqtrade_report_builder import FreqtradeReportBuilder
    from app.services.factors.paper_persistence_service import FactorPaperPersistenceService
    from app.services.factors.service import FactorResearchService

class FactorPaperRunManager:
    def __init__(
        self,
        *,
        factor_service: FactorResearchService,
        run_repository: BacktestRunRepository,
        report_builder: FreqtradeReportBuilder,
        execution_core: FactorSignalExecutionCore,
        persistence_service: FactorPaperPersistenceService,
    ) -> None:
        self.factor_service = factor_service
        self.run_repository = run_repository
        self.report_builder = report_builder
        self.execution_core = execution_core
        self.persistence_service = persistence_service
        self._task_manager = RunTaskManager(
            list_active_run_ids=self._list_active_run_ids,
            tick=self._tick,
            mark_failed=lambda run_id, reason: self._mark_stopped(run_id, "failed", reason),
            interval_seconds=lambda: float(settings.WS_UPDATE_INTERVAL),
            error_label="因子模拟盘运行失败",
        )

    async def restore_active_runs(self) -> None:
        await self._task_manager.restore_active_runs()

    async def shutdown(self) -> None:
        await self._task_manager.shutdown()

    async def start_run(
        self,
        *,
        research_run_id: int,
        initial_cash: float,
        fee_rate: float,
        position_size_pct: float,
        stake_mode: str = "fixed",
        entry_threshold: float | None = None,
        exit_threshold: float | None = None,
        stoploss_pct: float = -0.08,
        takeprofit_pct: float = 0.16,
        max_hold_bars: int = 20,
    ) -> dict[str, Any]:
        loop = asyncio.get_running_loop()
        run_id = await loop.run_in_executor(
            None,
            lambda: self._create_run(
                research_run_id=research_run_id,
                initial_cash=initial_cash,
                fee_rate=fee_rate,
                position_size_pct=position_size_pct,
                stake_mode=stake_mode,
                entry_threshold=entry_threshold,
                exit_threshold=exit_threshold,
                stoploss_pct=stoploss_pct,
                takeprofit_pct=takeprofit_pct,
                max_hold_bars=max_hold_bars,
            ),
        )
        self._task_manager.ensure_task(run_id)
        return {"success": True, "run_id": run_id, "message": "因子模拟盘已启动"}

    def _tick(self, run_id: int) -> bool:
        with session_scope() as session:
            run = session.query(BacktestRun).filter(BacktestRun.id == run_id).first()
            if not run:
                return False
            metadata = parse_run_metadata(run.metadata_info)
            if run.execution_mode != PAPER_LIVE_EXECUTION_MODE or run.engine != FACTOR_BLEND_PAPER_ENGINE:
                return False
            if run.status != "running":
                return False

            research_meta = metadata.factor_research
            factor_service = self.factor_service
            research_run, frame = factor_service.build_live_blend_frame(research_meta["run_id"])
            if frame.empty:
                return True

            timeframe_delta = factor_service.timeframe_delta(run.timeframe)
            now = utc_now_naive()
            symbol = str((metadata.symbols or [run.symbol])[0])
            runtime_state = ensure_paper_runtime_state(metadata.runtime_state.model_dump() if metadata.runtime_state else {}, symbols=[symbol])
            last_processed = int((runtime_state.get("last_processed") or {}).get(symbol, 0) or 0)
            closed = frame.loc[frame["timestamp"].apply(lambda ts: ts + timeframe_delta <= now)].copy()
            if last_processed:
                last_processed_dt = datetime.utcfromtimestamp(last_processed / 1000.0)
                closed = closed.loc[closed["timestamp"] > last_processed_dt]
            if closed.empty:
                return True

            execution_core = self.execution_core
            batch = execution_core.run_batch(
                rows=closed.to_dict("records"),
                state=execution_core.create_state(
                    float(runtime_state.get("cash_balance", metadata.initial_cash or 0.0)),
                    position=execution_core.deserialize_position((runtime_state.get("positions") or {}).get(symbol)),
                    held_bars=int(runtime_state.get("held_bars", 0) or 0),
                ),
                context=FactorSignalContext(
                    symbol=symbol,
                    research_run_id=int(research_meta["run_id"]),
                    initial_cash=float(metadata.initial_cash or 0.0),
                    fee_rate=float(metadata.fee_rate or 0.0),
                    position_size_pct=float(research_meta["position_size_pct"]),
                    stake_mode=str(research_meta.get("stake_mode") or "fixed"),
                    entry_threshold=float(research_meta["entry_threshold"]),
                    exit_threshold=float(research_meta["exit_threshold"]),
                    stoploss_pct=float(research_meta["stoploss_pct"]),
                    takeprofit_pct=float(research_meta["takeprofit_pct"]),
                    max_hold_bars=int(research_meta["max_hold_bars"]),
                ),
            )

            position = batch.state.position
            cash_balance = batch.state.cash_balance
            signals = batch.signals
            trades = batch.trades
            equity_points = batch.equity_points
            runtime_state["held_bars"] = batch.state.held_bars
            for row in closed.to_dict("records"):
                runtime_state.setdefault("last_processed", {})[symbol] = int(row["timestamp"].timestamp() * 1000)

            self.persistence_service.persist_increment(
                session=session,
                run=run,
                metadata=metadata,
                runtime_state=runtime_state,
                position=position,
                cash_balance=cash_balance,
                new_signals=signals,
                new_trades=trades,
                new_equity_points=equity_points,
                now=now,
            )
            return True

    def _create_run(
        self,
        *,
        research_run_id: int,
        initial_cash: float,
        fee_rate: float,
        position_size_pct: float,
        stake_mode: str,
        entry_threshold: float | None,
        exit_threshold: float | None,
        stoploss_pct: float,
        takeprofit_pct: float,
        max_hold_bars: int,
    ) -> int:
        factor_service = self.factor_service
        research_run = factor_service.get_run(research_run_id)
        if not research_run:
            raise ValueError("因子研究记录不存在。")
        request_payload = dict(research_run.get("request") or {})
        blend = dict(research_run.get("blend") or {})
        now = utc_now_naive()
        _, live_frame = factor_service.build_live_blend_frame(research_run_id, end_date=now)
        timeframe_delta = factor_service.timeframe_delta(request_payload["timeframe"])
        closed_frame = live_frame.loc[live_frame["timestamp"].apply(lambda ts: ts + timeframe_delta <= now)] if not live_frame.empty else live_frame
        last_processed = None if closed_frame.empty else int(closed_frame["timestamp"].iloc[-1].timestamp() * 1000)
        strategy = StrategyVersionRecord(
            strategy_key="factor_blend",
            strategy_name="Factor Blend",
            version=research_run_id,
            template="factor_blend",
            config=blank_strategy_version_config_model(),
        )
        portfolio = PortfolioConfigRecord(
            symbols=[request_payload["symbol"]],
            max_open_trades=1,
            position_size_pct=position_size_pct,
            stake_mode=stake_mode,
        )
        report = self.report_builder.build_report(
            trades=[],
            equity_curve=[BacktestEquityPointRecord(timestamp=now, equity=initial_cash, pnl_abs=0.0, drawdown_pct=0.0)],
            initial_cash=initial_cash,
            start_date=now,
            end_date=now,
        )
        metadata = parse_run_metadata(
            build_paper_metadata(
                strategy=strategy,
                symbols=[request_payload["symbol"]],
                initial_cash=initial_cash,
                fee_rate=fee_rate,
                portfolio=portfolio,
                runtime_state={
                    "cash_balance": initial_cash,
                    "last_processed": {request_payload["symbol"]: last_processed},
                    "positions": {},
                    "held_bars": 0,
                },
                paper_live={"cash_balance": initial_cash, "open_positions": 0, "positions": [], "last_updated": now.isoformat()},
                report=report,
            )
        ).model_copy(
            update={
                "factor_research": {
                    "run_id": research_run_id,
                    "dataset_id": research_run["dataset_id"],
                    "entry_threshold": float(blend.get("entry_threshold", 0.0) if entry_threshold is None else entry_threshold),
                    "exit_threshold": float(blend.get("exit_threshold", 0.0) if exit_threshold is None else exit_threshold),
                    "stoploss_pct": stoploss_pct,
                    "takeprofit_pct": takeprofit_pct,
                    "max_hold_bars": max_hold_bars,
                    "position_size_pct": position_size_pct,
                    "stake_mode": stake_mode,
                    "blend": blend,
                },
            }
        ).model_dump()
        with session_scope() as session:
            run = BacktestRun(
                symbol=request_payload["symbol"],
                timeframe=request_payload["timeframe"],
                start_date=now,
                end_date=now,
                status="running",
                execution_mode=PAPER_LIVE_EXECUTION_MODE,
                engine=FACTOR_BLEND_PAPER_ENGINE,
                metadata_info=metadata,
            )
            session.add(run)
            session.flush()
            session.add(
                BacktestEquityPoint(
                    backtest_id=run.id,
                    timestamp=now,
                    equity=initial_cash,
                    pnl_abs=0.0,
                    drawdown_pct=0.0,
                )
            )
            session.flush()
            return run.id

    def _list_active_run_ids(self) -> list[int]:
        return self.run_repository.list_active_run_ids(
            execution_mode=PAPER_LIVE_EXECUTION_MODE,
            engine=FACTOR_BLEND_PAPER_ENGINE,
        )

    def _mark_stopped(self, run_id: int, status: str, reason: str) -> None:
        with session_scope() as session:
            run = session.query(BacktestRun).filter(BacktestRun.id == run_id).first()
            if not run:
                return
            if run.execution_mode != PAPER_LIVE_EXECUTION_MODE or run.engine != FACTOR_BLEND_PAPER_ENGINE:
                return
            metadata = parse_run_metadata(run.metadata_info)
            run.status = status
            symbol = str((metadata.symbols or [run.symbol])[0])
            run.metadata_info = update_paper_metadata(
                metadata,
                runtime_state=ensure_paper_runtime_state(metadata.runtime_state.model_dump() if metadata.runtime_state else {}, symbols=[symbol]),
                last_updated=utc_now_naive().isoformat(),
                stop_reason=reason,
            )
            session.flush()
