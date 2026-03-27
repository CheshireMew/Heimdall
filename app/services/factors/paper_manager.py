from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.infra.db.database import init_db, session_scope
from app.infra.db.schema import BacktestEquityPoint, BacktestRun, BacktestSignal, BacktestTrade
from app.services.backtest.freqtrade_report_builder import FreqtradeReportBuilder
from app.services.backtest.models import BacktestEquityPointRecord, BacktestSignalRecord, BacktestTradeRecord, PortfolioConfigRecord, StrategyVersionRecord
from app.services.backtest.run_contract import build_paper_metadata
from app.services.factors.service import FactorResearchService
from utils.logger import logger


@dataclass(slots=True)
class FactorPaperPosition:
    opened_at: datetime
    entry_price: float
    amount: float
    stake_amount: float
    entry_score: float


class FactorPaperRunManager:
    def __init__(
        self,
        *,
        factor_service: FactorResearchService,
        report_builder: FreqtradeReportBuilder | None = None,
    ) -> None:
        self.factor_service = factor_service
        self.report_builder = report_builder or FreqtradeReportBuilder()
        self._tasks: dict[int, asyncio.Task[Any]] = {}
        init_db()

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
        self._ensure_task(run_id)
        return {"success": True, "run_id": run_id, "message": "因子模拟盘已启动"}

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
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.error(f"因子模拟盘运行失败 run_id={run_id}: {exc}", exc_info=True)
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, lambda: self._mark_stopped(run_id, "failed", str(exc)))
            self._tasks.pop(run_id, None)

    def _tick(self, run_id: int) -> bool:
        with session_scope() as session:
            run = session.query(BacktestRun).filter(BacktestRun.id == run_id).first()
            if not run:
                return False
            metadata = dict(run.metadata_info or {})
            if metadata.get("execution_mode") != "paper_live" or metadata.get("engine") != "FactorBlendPaper":
                return False
            if run.status != "running":
                return False

            research_meta = dict(metadata.get("factor_research") or {})
            research_run, frame = self.factor_service.build_live_blend_frame(research_meta["run_id"])
            if frame.empty:
                return True

            timeframe_delta = self.factor_service._timeframe_delta(run.timeframe)
            now = datetime.utcnow()
            last_processed = int((metadata.get("runtime_state") or {}).get("last_processed", 0) or 0)
            closed = frame.loc[frame["timestamp"].apply(lambda ts: ts + timeframe_delta <= now)].copy()
            if last_processed:
                last_processed_dt = datetime.utcfromtimestamp(last_processed / 1000.0)
                closed = closed.loc[closed["timestamp"] > last_processed_dt]
            if closed.empty:
                return True

            runtime_state = dict(metadata.get("runtime_state") or {})
            position = self._deserialize_position(runtime_state.get("position"))
            cash_balance = float(runtime_state.get("cash_balance", metadata.get("initial_cash", 0.0)))
            fee_ratio = float(metadata.get("fee_rate", 0.0)) / 100.0
            signals: list[BacktestSignalRecord] = []
            trades: list[BacktestTradeRecord] = []
            equity_points: list[BacktestEquityPointRecord] = []

            for bar_index, row in enumerate(closed.to_dict("records"), start=1):
                price = float(row["close"])
                score = float(row.get("composite_score") or 0.0)
                timestamp = row["timestamp"]
                if position:
                    held_bars = max(int(runtime_state.get("held_bars", 0)) + 1, 1)
                    runtime_state["held_bars"] = held_bars
                    profit_ratio = self._profit_ratio(position, price, fee_ratio)
                    if (
                        profit_ratio <= float(research_meta["stoploss_pct"])
                        or profit_ratio >= float(research_meta["takeprofit_pct"])
                        or score <= float(research_meta["exit_threshold"])
                        or held_bars >= int(research_meta["max_hold_bars"])
                    ):
                        trade = self._close_position(position, price, timestamp, fee_ratio, run.symbol)
                        cash_balance += trade.stake_amount + trade.profit_abs
                        trades.append(trade)
                        signals.append(
                            BacktestSignalRecord(
                                timestamp=timestamp,
                                price=price,
                                signal="SELL",
                                confidence=100.0,
                                indicators={"composite_score": score, "research_run_id": research_meta["run_id"]},
                                reasoning="Factor paper exit",
                            )
                        )
                        position = None
                        runtime_state["held_bars"] = 0

                if position is None and score >= float(research_meta["entry_threshold"]):
                    stake_amount = min(
                        cash_balance,
                        float(metadata.get("initial_cash", 0.0)) * (float(research_meta["position_size_pct"]) / 100.0)
                        if research_meta.get("stake_mode") == "fixed"
                        else cash_balance * (float(research_meta["position_size_pct"]) / 100.0),
                    )
                    if stake_amount > 0:
                        notional = stake_amount / (1.0 + fee_ratio) if fee_ratio < 1 else 0.0
                        amount = notional / price if price > 0 else 0.0
                        if amount > 0:
                            cash_balance -= stake_amount
                            position = FactorPaperPosition(
                                opened_at=timestamp,
                                entry_price=price,
                                amount=amount,
                                stake_amount=stake_amount,
                                entry_score=score,
                            )
                            runtime_state["held_bars"] = 0
                            signals.append(
                                BacktestSignalRecord(
                                    timestamp=timestamp,
                                    price=price,
                                    signal="BUY",
                                    confidence=100.0,
                                    indicators={"composite_score": score, "research_run_id": research_meta["run_id"]},
                                    reasoning="Factor paper entry",
                                )
                            )

                equity = cash_balance
                if position:
                    equity += position.amount * price * (1.0 - fee_ratio)
                equity_points.append(
                    BacktestEquityPointRecord(
                        timestamp=timestamp,
                        equity=equity,
                        pnl_abs=equity - float(metadata.get("initial_cash", 0.0)),
                        drawdown_pct=0.0,
                    )
                )
                runtime_state["last_processed"] = int(timestamp.timestamp() * 1000)

            self._persist_increment(
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

    def _persist_increment(
        self,
        *,
        session,
        run: BacktestRun,
        metadata: dict[str, Any],
        runtime_state: dict[str, Any],
        position: FactorPaperPosition | None,
        cash_balance: float,
        new_signals: list[BacktestSignalRecord],
        new_trades: list[BacktestTradeRecord],
        new_equity_points: list[BacktestEquityPointRecord],
        now: datetime,
    ) -> None:
        if new_signals:
            session.bulk_save_objects(
                [
                    BacktestSignal(
                        backtest_id=run.id,
                        timestamp=item.timestamp,
                        price=item.price,
                        signal=item.signal,
                        confidence=item.confidence,
                        indicators=item.indicators,
                        reasoning=item.reasoning,
                    )
                    for item in new_signals
                ]
            )
        if new_trades:
            session.bulk_save_objects(
                [
                    BacktestTrade(
                        backtest_id=run.id,
                        pair=item.pair or run.symbol,
                        opened_at=item.opened_at,
                        closed_at=item.closed_at,
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
                    for item in new_trades
                ]
            )
        if new_equity_points:
            peak = max([point.equity for point in session.query(BacktestEquityPoint).filter(BacktestEquityPoint.backtest_id == run.id).all()], default=float(metadata.get("initial_cash", 0.0)))
            persisted = []
            for item in new_equity_points:
                peak = max(peak, item.equity)
                drawdown = ((peak - item.equity) / peak * 100.0) if peak else 0.0
                persisted.append(
                    BacktestEquityPoint(
                        backtest_id=run.id,
                        timestamp=item.timestamp,
                        equity=item.equity,
                        pnl_abs=item.pnl_abs,
                        drawdown_pct=drawdown,
                    )
                )
            session.bulk_save_objects(persisted)
        session.flush()

        run.total_candles += len(new_equity_points)
        run.total_signals += len(new_signals)
        run.buy_signals += sum(1 for item in new_signals if item.signal == "BUY")
        run.sell_signals += sum(1 for item in new_signals if item.signal == "SELL")
        run.hold_signals = max(run.total_candles - run.total_signals, 0)
        run.end_date = max((item.timestamp for item in new_equity_points), default=run.end_date or now)

        trades = session.query(BacktestTrade).filter(BacktestTrade.backtest_id == run.id).order_by(BacktestTrade.opened_at.asc()).all()
        equity = session.query(BacktestEquityPoint).filter(BacktestEquityPoint.backtest_id == run.id).order_by(BacktestEquityPoint.timestamp.asc()).all()
        trade_records = [
            BacktestTradeRecord(
                opened_at=item.opened_at,
                closed_at=item.closed_at,
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
                pair=item.pair,
            )
            for item in trades
        ]
        equity_records = [
            BacktestEquityPointRecord(
                timestamp=item.timestamp,
                equity=item.equity,
                pnl_abs=item.pnl_abs,
                drawdown_pct=item.drawdown_pct,
            )
            for item in equity
        ]
        report = self.report_builder.build_report(
            trades=trade_records,
            equity_curve=equity_records,
            initial_cash=float(metadata.get("initial_cash", 0.0)),
            start_date=run.start_date,
            end_date=run.end_date or now,
        )
        metadata["runtime_state"] = {
            "cash_balance": cash_balance,
            "position": self._serialize_position(position),
            "last_processed": runtime_state.get("last_processed"),
            "held_bars": runtime_state.get("held_bars", 0),
        }
        metadata["paper_live"] = {
            "cash_balance": cash_balance,
            "open_positions": 1 if position else 0,
            "positions": [self._serialize_position(position)] if position else [],
            "last_updated": now.isoformat(),
        }
        metadata["report"] = report
        run.metadata_info = metadata
        session.flush()

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
        research_run = self.factor_service.get_run(research_run_id)
        if not research_run:
            raise ValueError("因子研究记录不存在。")
        request_payload = dict(research_run.get("request") or {})
        blend = dict(research_run.get("blend") or {})
        now = datetime.utcnow()
        _, live_frame = self.factor_service.build_live_blend_frame(research_run_id, end_date=now)
        timeframe_delta = self.factor_service._timeframe_delta(request_payload["timeframe"])
        closed_frame = live_frame.loc[live_frame["timestamp"].apply(lambda ts: ts + timeframe_delta <= now)] if not live_frame.empty else live_frame
        last_processed = None if closed_frame.empty else int(closed_frame["timestamp"].iloc[-1].timestamp() * 1000)
        strategy = StrategyVersionRecord(
            strategy_key="factor_blend",
            strategy_name="Factor Blend",
            version=research_run_id,
            template="factor_blend",
            config={"research_run_id": research_run_id},
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
        metadata = build_paper_metadata(
            strategy=strategy,
            symbols=[request_payload["symbol"]],
            initial_cash=initial_cash,
            fee_rate=fee_rate,
            portfolio=portfolio,
            runtime_state={"cash_balance": initial_cash, "position": None, "last_processed": last_processed, "held_bars": 0},
            paper_live={"cash_balance": initial_cash, "open_positions": 0, "positions": [], "last_updated": now.isoformat()},
            report=report,
            engine="FactorBlendPaper",
        )
        metadata["factor_research"] = {
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
        }
        with session_scope() as session:
            run = BacktestRun(
                symbol=request_payload["symbol"],
                timeframe=request_payload["timeframe"],
                start_date=now,
                end_date=now,
                status="running",
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
        with session_scope() as session:
            runs = session.query(BacktestRun).order_by(BacktestRun.created_at.asc()).all()
            return [
                run.id
                for run in runs
                if run.status == "running"
                and (run.metadata_info or {}).get("execution_mode") == "paper_live"
                and (run.metadata_info or {}).get("engine") == "FactorBlendPaper"
            ]

    def _mark_stopped(self, run_id: int, status: str, reason: str) -> None:
        with session_scope() as session:
            run = session.query(BacktestRun).filter(BacktestRun.id == run_id).first()
            if not run:
                return
            metadata = dict(run.metadata_info or {})
            run.status = status
            metadata["paper_live"] = {
                **(metadata.get("paper_live") or {}),
                "last_updated": datetime.utcnow().isoformat(),
                "stop_reason": reason,
            }
            run.metadata_info = metadata
            session.flush()

    def _serialize_position(self, position: FactorPaperPosition | None) -> dict[str, Any] | None:
        if not position:
            return None
        return {
            "opened_at": position.opened_at.isoformat(),
            "entry_price": position.entry_price,
            "amount": position.amount,
            "stake_amount": position.stake_amount,
            "entry_score": position.entry_score,
        }

    def _deserialize_position(self, payload: dict[str, Any] | None) -> FactorPaperPosition | None:
        if not payload:
            return None
        return FactorPaperPosition(
            opened_at=datetime.fromisoformat(payload["opened_at"]),
            entry_price=float(payload["entry_price"]),
            amount=float(payload["amount"]),
            stake_amount=float(payload["stake_amount"]),
            entry_score=float(payload.get("entry_score", 0.0)),
        )

    def _profit_ratio(self, position: FactorPaperPosition, price: float, fee_ratio: float) -> float:
        net_value = position.amount * price * (1.0 - fee_ratio)
        if position.stake_amount <= 0:
            return 0.0
        return (net_value - position.stake_amount) / position.stake_amount

    def _close_position(
        self,
        position: FactorPaperPosition,
        price: float,
        timestamp: datetime,
        fee_ratio: float,
        symbol: str,
        exit_reason: str = "factor_paper_exit",
    ) -> BacktestTradeRecord:
        gross = position.amount * price
        net = gross * (1.0 - fee_ratio)
        profit_abs = net - position.stake_amount
        duration_minutes = max(int((timestamp - position.opened_at).total_seconds() // 60), 0)
        return BacktestTradeRecord(
            opened_at=position.opened_at,
            closed_at=timestamp,
            entry_price=position.entry_price,
            exit_price=price,
            stake_amount=position.stake_amount,
            amount=position.amount,
            profit_abs=profit_abs,
            profit_pct=(profit_abs / position.stake_amount * 100.0) if position.stake_amount else 0.0,
            duration_minutes=duration_minutes,
            entry_tag="factor_entry",
            exit_reason=exit_reason,
            leverage=1.0,
            pair=symbol,
        )
