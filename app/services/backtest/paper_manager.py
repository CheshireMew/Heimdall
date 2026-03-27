from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from app.infra.db.database import init_db, session_scope
from app.infra.db.schema import BacktestEquityPoint, BacktestRun, BacktestSignal, BacktestTrade
from app.services.backtest.contracts import PaperStartCommand
from app.services.backtest.freqtrade_report_builder import FreqtradeReportBuilder
from app.services.backtest.models import BacktestEquityPointRecord, BacktestSignalRecord, BacktestTradeRecord
from app.services.backtest.run_contract import build_paper_metadata
from app.services.backtest.strategy_library import StrategyLibraryService
from app.services.backtest.strategy_runtime import StrategyRuntime
from app.services.market.market_data_service import MarketDataService
from config import settings
from utils.logger import logger


@dataclass(slots=True)
class PaperPosition:
    symbol: str
    opened_at: datetime
    entry_price: float
    remaining_amount: float
    remaining_cost: float
    highest_price: float
    last_price: float
    taken_partial_ids: list[str] = field(default_factory=list)


class PaperRunManager:
    def __init__(
        self,
        *,
        market_data_service: MarketDataService,
        strategy_library: StrategyLibraryService | None = None,
        runtime: StrategyRuntime | None = None,
        report_builder: FreqtradeReportBuilder | None = None,
    ) -> None:
        self.market_data_service = market_data_service
        self.strategy_library = strategy_library or StrategyLibraryService()
        self.runtime = runtime or StrategyRuntime()
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
            if metadata.get("execution_mode") != "paper_live" or metadata.get("engine") != "PaperLive":
                return False
            if run.status != "running":
                return False

            strategy = self.strategy_library.get_strategy_version(
                metadata["strategy_key"],
                metadata.get("strategy_version"),
            )
            runtime_state = self._load_runtime_state(metadata)
            portfolio = metadata.get("portfolio") or {}
            symbols = list(metadata.get("symbols") or [])
            timeframe = run.timeframe
            now = datetime.utcnow()
            fee_ratio = float(metadata.get("fee_rate", 0.0)) / 100.0
            warmup_bars = self.runtime.warmup_bars(strategy.template, strategy.config)

            pending = self._build_pending_snapshots(
                strategy=strategy,
                symbols=symbols,
                timeframe=timeframe,
                runtime_state=runtime_state,
                now=now,
                warmup_bars=warmup_bars,
            )
            if not pending:
                return True

            new_signals: list[BacktestSignalRecord] = []
            new_trades: list[BacktestTradeRecord] = []
            new_equity_points: list[BacktestEquityPointRecord] = []
            positions = self._deserialize_positions(runtime_state.get("positions") or {})
            cash_balance = float(runtime_state.get("cash_balance", metadata.get("initial_cash", 0.0)))

            for symbol, snapshot in pending:
                run.total_candles += 1
                position = positions.get(symbol)
                if position:
                    generated_signals, generated_trades = self._process_open_position(
                        position=position,
                        snapshot=snapshot,
                        fee_ratio=fee_ratio,
                        risk=(strategy.config.get("risk") or {}),
                    )
                    new_signals.extend(generated_signals)
                    new_trades.extend(generated_trades)
                    for trade in generated_trades:
                        cash_balance += trade.stake_amount + trade.profit_abs
                    if position.remaining_amount <= 1e-12 or position.remaining_cost <= 1e-8:
                        positions.pop(symbol, None)
                if symbol not in positions and snapshot.entry_signal:
                    if len(positions) < int(portfolio.get("max_open_trades", 1)):
                        created_position, entry_signal, cash_spent = self._try_open_position(
                            symbol=symbol,
                            snapshot=snapshot,
                            cash_balance=cash_balance,
                            fee_ratio=fee_ratio,
                            portfolio=portfolio,
                            initial_cash=float(metadata.get("initial_cash", 0.0)),
                        )
                        if created_position:
                            positions[symbol] = created_position
                            new_signals.append(entry_signal)
                            cash_balance -= cash_spent

                runtime_state.setdefault("last_processed", {})[symbol] = int(snapshot.timestamp.timestamp() * 1000)
                equity = self._current_equity(cash_balance, positions, snapshot.price, symbol, fee_ratio)
                new_equity_points.append(
                    BacktestEquityPointRecord(
                        timestamp=snapshot.timestamp,
                        equity=equity,
                        pnl_abs=equity - float(metadata.get("initial_cash", 0.0)),
                        drawdown_pct=0.0,
                    )
                )

            self._persist_increment(
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

    def _build_pending_snapshots(
        self,
        *,
        strategy,
        symbols: list[str],
        timeframe: str,
        runtime_state: dict[str, Any],
        now: datetime,
        warmup_bars: int,
    ) -> list[tuple[str, Any]]:
        pending: list[tuple[str, Any]] = []
        timeframe_delta = self._timeframe_delta(timeframe)
        timeframe_ms = int(timeframe_delta.total_seconds() * 1000)
        last_processed = runtime_state.get("last_processed") or {}
        for symbol in symbols:
            last_processed_ms = last_processed.get(symbol)
            if last_processed_ms:
                start_at = datetime.utcfromtimestamp(last_processed_ms / 1000.0) - (timeframe_delta * warmup_bars)
            else:
                start_at = now - (timeframe_delta * (warmup_bars + 2))
            candles = self.market_data_service.fetch_live_ohlcv_range(symbol, timeframe, start_at, now)
            closed_candles = [row for row in candles if row[0] + timeframe_ms <= int(now.timestamp() * 1000)]
            snapshots = self.runtime.build_signal_snapshots(
                strategy.template,
                strategy.config,
                closed_candles,
                after_timestamp_ms=last_processed_ms,
            )
            for snapshot in snapshots:
                pending.append((symbol, snapshot))
        pending.sort(key=lambda item: (item[1].timestamp, item[0]))
        return pending

    def _try_open_position(
        self,
        *,
        symbol: str,
        snapshot,
        cash_balance: float,
        fee_ratio: float,
        portfolio: dict[str, Any],
        initial_cash: float,
    ) -> tuple[PaperPosition | None, BacktestSignalRecord | None, float]:
        if cash_balance <= 0:
            return None, None, 0.0
        position_size_pct = float(portfolio.get("position_size_pct", 0.0)) / 100.0
        stake_mode = portfolio.get("stake_mode") or "fixed"
        if stake_mode == "fixed":
            intended_stake = initial_cash * position_size_pct
        else:
            intended_stake = cash_balance * position_size_pct
        stake = min(max(intended_stake, 0.0), cash_balance)
        if stake <= 0:
            return None, None, 0.0
        notional = stake / (1.0 + fee_ratio) if fee_ratio < 1.0 else 0.0
        if notional <= 0:
            return None, None, 0.0
        amount = notional / snapshot.price if snapshot.price > 0 else 0.0
        if amount <= 0:
            return None, None, 0.0
        position = PaperPosition(
            symbol=symbol,
            opened_at=snapshot.timestamp,
            entry_price=snapshot.price,
            remaining_amount=amount,
            remaining_cost=stake,
            highest_price=snapshot.price,
            last_price=snapshot.price,
        )
        signal = BacktestSignalRecord(
            timestamp=snapshot.timestamp,
            price=snapshot.price,
            signal="BUY",
            confidence=100.0,
            indicators={"pair": symbol, **snapshot.indicators},
            reasoning="Paper entry: entry_signal",
        )
        return position, signal, stake

    def _process_open_position(
        self,
        *,
        position: PaperPosition,
        snapshot,
        fee_ratio: float,
        risk: dict[str, Any],
    ) -> tuple[list[BacktestSignalRecord], list[BacktestTradeRecord]]:
        position.last_price = snapshot.price
        position.highest_price = max(position.highest_price, snapshot.price)
        signals: list[BacktestSignalRecord] = []
        trades: list[BacktestTradeRecord] = []

        partial_exits = [item for item in risk.get("partial_exits") or [] if item.get("enabled", True)]
        partial_exits.sort(key=lambda item: float(item.get("profit", 0)))
        for item in partial_exits:
            partial_id = item.get("id") or ""
            if partial_id in position.taken_partial_ids:
                continue
            current_profit_ratio = self._profit_ratio(position, snapshot.price, fee_ratio)
            if current_profit_ratio < float(item.get("profit", 0)):
                continue
            sold_amount = position.remaining_amount * (float(item.get("size_pct", 0)) / 100.0)
            trade = self._close_trade_slice(position, sold_amount, snapshot.price, snapshot.timestamp, partial_id, fee_ratio)
            if not trade:
                continue
            position.taken_partial_ids.append(partial_id)
            trades.append(trade)
            signals.append(
                BacktestSignalRecord(
                    timestamp=snapshot.timestamp,
                    price=snapshot.price,
                    signal="SELL",
                    confidence=100.0,
                    indicators={"pair": position.symbol, "profit_ratio": trade.profit_pct / 100.0, **snapshot.indicators},
                    reasoning=f"Paper exit: {partial_id}",
                )
            )

        if position.remaining_amount <= 1e-12:
            return signals, trades

        exit_reason = self._resolve_exit_reason(position, snapshot.price, snapshot.timestamp, snapshot.exit_signal, risk, fee_ratio)
        if not exit_reason:
            return signals, trades

        trade = self._close_trade_slice(
            position,
            position.remaining_amount,
            snapshot.price,
            snapshot.timestamp,
            exit_reason,
            fee_ratio,
        )
        if not trade:
            return signals, trades
        trades.append(trade)
        signals.append(
            BacktestSignalRecord(
                timestamp=snapshot.timestamp,
                price=snapshot.price,
                signal="SELL",
                confidence=100.0,
                indicators={"pair": position.symbol, "profit_ratio": trade.profit_pct / 100.0, **snapshot.indicators},
                reasoning=f"Paper exit: {exit_reason}",
            )
        )
        return signals, trades

    def _resolve_exit_reason(
        self,
        position: PaperPosition,
        price: float,
        current_time: datetime,
        exit_signal: bool,
        risk: dict[str, Any],
        fee_ratio: float,
    ) -> str | None:
        profit_ratio = self._profit_ratio(position, price, fee_ratio)
        stoploss = float((risk.get("stoploss") if risk else -0.1) or -0.1)
        if profit_ratio <= stoploss:
            return "stoploss"

        trailing = risk.get("trailing") or {}
        trailing_reason = self._trailing_exit_reason(position, price, fee_ratio, trailing)
        if trailing_reason:
            return trailing_reason

        if exit_signal:
            return "exit_signal"

        enabled_partials = [item for item in risk.get("partial_exits") or [] if item.get("enabled", True)]
        if len(position.taken_partial_ids) >= len(enabled_partials):
            required_roi = self._required_roi(position, current_time, risk)
            if required_roi is not None and profit_ratio >= required_roi:
                return "roi_target"
        return None

    def _trailing_exit_reason(
        self,
        position: PaperPosition,
        price: float,
        fee_ratio: float,
        trailing: dict[str, Any],
    ) -> str | None:
        if not trailing.get("enabled"):
            return None
        positive = float(trailing.get("positive", 0.0))
        offset = float(trailing.get("offset", positive))
        max_profit_ratio = self._profit_ratio(position, position.highest_price, fee_ratio)
        current_profit_ratio = self._profit_ratio(position, price, fee_ratio)
        threshold = offset if trailing.get("only_offset_reached", True) else positive
        if max_profit_ratio < threshold:
            return None
        if current_profit_ratio <= max(max_profit_ratio - positive, 0.0):
            return "trailing_stop"
        return None

    def _required_roi(self, position: PaperPosition, current_time: datetime, risk: dict[str, Any]) -> float | None:
        targets = [item for item in risk.get("roi_targets") or [] if item.get("enabled", True)]
        if not targets:
            return None
        held_minutes = max(int((current_time - position.opened_at).total_seconds() // 60), 0)
        eligible = sorted((int(item.get("minutes", 0)), float(item.get("profit", 0))) for item in targets)
        selected = eligible[0][1]
        for minutes, profit in eligible:
            if held_minutes >= minutes:
                selected = profit
        return selected

    def _close_trade_slice(
        self,
        position: PaperPosition,
        sold_amount: float,
        price: float,
        closed_at: datetime,
        exit_reason: str,
        fee_ratio: float,
    ) -> BacktestTradeRecord | None:
        if sold_amount <= 0 or position.remaining_amount <= 0:
            return None
        sold_amount = min(sold_amount, position.remaining_amount)
        cost_share = position.remaining_cost * (sold_amount / position.remaining_amount)
        gross_proceeds = sold_amount * price
        exit_fee = gross_proceeds * fee_ratio
        net_proceeds = gross_proceeds - exit_fee
        profit_abs = net_proceeds - cost_share
        position.remaining_amount -= sold_amount
        position.remaining_cost -= cost_share
        duration_minutes = max(int((closed_at - position.opened_at).total_seconds() // 60), 0)
        return BacktestTradeRecord(
            opened_at=position.opened_at,
            closed_at=closed_at,
            entry_price=position.entry_price,
            exit_price=price,
            stake_amount=cost_share,
            amount=sold_amount,
            profit_abs=profit_abs,
            profit_pct=(profit_abs / cost_share * 100.0) if cost_share else 0.0,
            max_drawdown_pct=None,
            duration_minutes=duration_minutes,
            entry_tag="entry_signal",
            exit_reason=exit_reason,
            leverage=1.0,
            pair=position.symbol,
        )

    def _persist_increment(
        self,
        *,
        session,
        run: BacktestRun,
        metadata: dict[str, Any],
        runtime_state: dict[str, Any],
        positions: dict[str, PaperPosition],
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

        all_equity_rows = (
            session.query(BacktestEquityPoint)
            .filter(BacktestEquityPoint.backtest_id == run.id)
            .order_by(BacktestEquityPoint.timestamp.asc())
            .all()
        )
        highest_equity = max([point.equity for point in all_equity_rows], default=float(metadata.get("initial_cash", 0.0)))
        persisted_equity_points: list[BacktestEquityPoint] = []
        for item in new_equity_points:
            highest_equity = max(highest_equity, item.equity)
            drawdown_pct = ((highest_equity - item.equity) / highest_equity * 100.0) if highest_equity else 0.0
            persisted_equity_points.append(
                BacktestEquityPoint(
                    backtest_id=run.id,
                    timestamp=item.timestamp,
                    equity=item.equity,
                    pnl_abs=item.pnl_abs,
                    drawdown_pct=drawdown_pct,
                )
            )
        if persisted_equity_points:
            session.bulk_save_objects(persisted_equity_points)
        session.flush()

        run.total_signals += len(new_signals)
        run.buy_signals += sum(1 for item in new_signals if item.signal == "BUY")
        run.sell_signals += sum(1 for item in new_signals if item.signal == "SELL")
        run.hold_signals = max(run.total_candles - run.total_signals, 0)
        run.end_date = max((item.timestamp for item in new_equity_points), default=run.end_date or now)

        all_trades = (
            session.query(BacktestTrade)
            .filter(BacktestTrade.backtest_id == run.id)
            .order_by(BacktestTrade.opened_at.asc())
            .all()
        )
        all_equity = (
            session.query(BacktestEquityPoint)
            .filter(BacktestEquityPoint.backtest_id == run.id)
            .order_by(BacktestEquityPoint.timestamp.asc())
            .all()
        )
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
            for item in all_trades
        ]
        equity_records = [
            BacktestEquityPointRecord(
                timestamp=item.timestamp,
                equity=item.equity,
                pnl_abs=item.pnl_abs,
                drawdown_pct=item.drawdown_pct,
            )
            for item in all_equity
        ]
        report = self.report_builder.build_report(
            trades=trade_records,
            equity_curve=equity_records,
            initial_cash=float(metadata.get("initial_cash", 0.0)),
            start_date=run.start_date,
            end_date=run.end_date or now,
        )
        report["strategy"] = {
            "key": metadata.get("strategy_key"),
            "name": metadata.get("strategy_name"),
            "version": metadata.get("strategy_version"),
            "template": metadata.get("strategy_template"),
        }
        report["portfolio"] = {
            **(metadata.get("portfolio") or {}),
            "stake_currency": self.report_builder.quote_currency((metadata.get("symbols") or [run.symbol])[0]),
        }
        serialized_positions = self._serialize_positions(positions)
        metadata["runtime_state"] = {
            "cash_balance": cash_balance,
            "last_processed": runtime_state.get("last_processed") or {},
            "positions": serialized_positions,
        }
        metadata["paper_live"] = {
            "cash_balance": cash_balance,
            "open_positions": len(positions),
            "positions": list(serialized_positions.values()),
            "last_updated": now.isoformat(),
        }
        metadata["report"] = report
        run.metadata_info = metadata
        session.flush()

    def _create_run(self, command: PaperStartCommand) -> int:
        strategy = self.strategy_library.get_strategy_version(command.strategy_key, command.strategy_version)
        now = datetime.utcnow()
        symbols = list(command.portfolio.symbols)
        timeframe_delta = self._timeframe_delta(command.timeframe)
        baseline_last_processed = {
            symbol: self._latest_closed_timestamp(symbol, command.timeframe, now, timeframe_delta)
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
                metadata_info=build_paper_metadata(
                    strategy=strategy,
                    symbols=symbols,
                    initial_cash=command.initial_cash,
                    fee_rate=command.fee_rate,
                    portfolio=command.portfolio,
                    runtime_state={
                        "cash_balance": command.initial_cash,
                        "last_processed": baseline_last_processed,
                        "positions": {},
                    },
                    paper_live={
                        "cash_balance": command.initial_cash,
                        "open_positions": 0,
                        "positions": [],
                        "last_updated": now.isoformat(),
                    },
                    report=initial_report,
                ),
            )
            session.add(run)
            session.flush()
            session.add(
                BacktestEquityPoint(
                    backtest_id=run.id,
                    timestamp=now,
                    equity=command.initial_cash,
                    pnl_abs=0.0,
                    drawdown_pct=0.0,
                )
            )
            session.flush()
            return run.id

    def _mark_stopped(self, run_id: int, status: str, reason: str) -> None:
        with session_scope() as session:
            run = session.query(BacktestRun).filter(BacktestRun.id == run_id).first()
            if not run:
                return
            metadata = dict(run.metadata_info or {})
            if metadata.get("execution_mode") != "paper_live":
                return
            run.status = status
            metadata["paper_live"] = {
                **(metadata.get("paper_live") or {}),
                "last_updated": datetime.utcnow().isoformat(),
                "stop_reason": reason,
            }
            run.metadata_info = metadata
            session.flush()

    def _list_active_run_ids(self) -> list[int]:
        with session_scope() as session:
            runs = session.query(BacktestRun).order_by(BacktestRun.created_at.asc()).all()
            return [
                run.id
                for run in runs
                if run.status == "running"
                and (run.metadata_info or {}).get("execution_mode") == "paper_live"
                and (run.metadata_info or {}).get("engine") == "PaperLive"
            ]

    def _latest_closed_timestamp(
        self,
        symbol: str,
        timeframe: str,
        now: datetime,
        timeframe_delta: timedelta,
    ) -> int | None:
        candles = self.market_data_service.fetch_live_ohlcv_range(symbol, timeframe, now - (timeframe_delta * 3), now)
        if not candles:
            return None
        cutoff_ms = int(now.timestamp() * 1000)
        timeframe_ms = int(timeframe_delta.total_seconds() * 1000)
        closed = [row[0] for row in candles if row[0] + timeframe_ms <= cutoff_ms]
        return closed[-1] if closed else None

    def _load_runtime_state(self, metadata: dict[str, Any]) -> dict[str, Any]:
        runtime_state = dict(metadata.get("runtime_state") or {})
        runtime_state.setdefault("cash_balance", float(metadata.get("initial_cash", 0.0)))
        runtime_state.setdefault("last_processed", {})
        runtime_state.setdefault("positions", {})
        return runtime_state

    def _serialize_positions(self, positions: dict[str, PaperPosition]) -> dict[str, dict[str, Any]]:
        return {
            symbol: {
                "symbol": item.symbol,
                "opened_at": item.opened_at.isoformat(),
                "entry_price": item.entry_price,
                "remaining_amount": item.remaining_amount,
                "remaining_cost": item.remaining_cost,
                "highest_price": item.highest_price,
                "last_price": item.last_price,
                "taken_partial_ids": list(item.taken_partial_ids),
            }
            for symbol, item in positions.items()
        }

    def _deserialize_positions(self, payload: dict[str, Any]) -> dict[str, PaperPosition]:
        result: dict[str, PaperPosition] = {}
        for symbol, item in (payload or {}).items():
            result[symbol] = PaperPosition(
                symbol=item.get("symbol") or symbol,
                opened_at=datetime.fromisoformat(item["opened_at"]),
                entry_price=float(item.get("entry_price", 0.0)),
                remaining_amount=float(item.get("remaining_amount", 0.0)),
                remaining_cost=float(item.get("remaining_cost", 0.0)),
                highest_price=float(item.get("highest_price", item.get("entry_price", 0.0))),
                last_price=float(item.get("last_price", item.get("entry_price", 0.0))),
                taken_partial_ids=list(item.get("taken_partial_ids") or []),
            )
        return result

    def _profit_ratio(self, position: PaperPosition, price: float, fee_ratio: float) -> float:
        if position.remaining_cost <= 0:
            return 0.0
        liquidation_value = position.remaining_amount * price * (1.0 - fee_ratio)
        return (liquidation_value - position.remaining_cost) / position.remaining_cost

    def _current_equity(
        self,
        cash_balance: float,
        positions: dict[str, PaperPosition],
        current_price: float,
        current_symbol: str,
        fee_ratio: float,
    ) -> float:
        equity = cash_balance
        for symbol, position in positions.items():
            mark_price = current_price if symbol == current_symbol else position.last_price
            equity += position.remaining_amount * mark_price * (1.0 - fee_ratio)
        return equity

    def _timeframe_delta(self, timeframe: str) -> timedelta:
        value = int(timeframe[:-1])
        unit = timeframe[-1]
        if unit == "m":
            return timedelta(minutes=value)
        if unit == "h":
            return timedelta(hours=value)
        if unit == "d":
            return timedelta(days=value)
        if unit == "w":
            return timedelta(weeks=value)
        raise ValueError(f"暂不支持的时间周期: {timeframe}")
