from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.services.backtest.models import BacktestSignalRecord, BacktestTradeRecord


@dataclass(slots=True)
class PaperPosition:
    symbol: str
    side: str
    opened_at: datetime
    entry_price: float
    remaining_amount: float
    remaining_cost: float
    highest_price: float
    lowest_price: float
    last_price: float
    taken_partial_ids: list[str] = field(default_factory=list)


class PaperPositionService:
    def try_open_position(
        self,
        *,
        symbol: str,
        snapshot,
        side: str,
        cash_balance: float,
        fee_ratio: float,
        portfolio: dict[str, Any],
        initial_cash: float,
    ) -> tuple[PaperPosition | None, BacktestSignalRecord | None, float]:
        if cash_balance <= 0:
            return None, None, 0.0
        position_size_pct = float(portfolio.get("position_size_pct", 0.0)) / 100.0
        intended_stake = initial_cash * position_size_pct if (portfolio.get("stake_mode") or "fixed") == "fixed" else cash_balance * position_size_pct
        stake = min(max(intended_stake, 0.0), cash_balance)
        if stake <= 0:
            return None, None, 0.0
        notional = stake / (1.0 + fee_ratio) if fee_ratio < 1.0 else 0.0
        amount = notional / snapshot.price if snapshot.price > 0 else 0.0
        if amount <= 0:
            return None, None, 0.0
        side = side if side in {"long", "short"} else "long"
        signal = "BUY" if side == "long" else "SELL"
        reason = "long_entry_signal" if side == "long" else "short_entry_signal"
        return (
            PaperPosition(
                symbol=symbol,
                side=side,
                opened_at=snapshot.timestamp,
                entry_price=snapshot.price,
                remaining_amount=amount,
                remaining_cost=stake,
                highest_price=snapshot.price,
                lowest_price=snapshot.price,
                last_price=snapshot.price,
            ),
            BacktestSignalRecord(
                timestamp=snapshot.timestamp,
                price=snapshot.price,
                signal=signal,
                confidence=100.0,
                indicators={"pair": symbol, "side": side, **snapshot.indicators},
                reasoning=f"Paper entry: {reason}",
            ),
            stake,
        )

    def process_open_position(
        self,
        *,
        position: PaperPosition,
        snapshot,
        fee_ratio: float,
        risk: dict[str, Any],
    ) -> tuple[list[BacktestSignalRecord], list[BacktestTradeRecord]]:
        position.last_price = snapshot.price
        position.highest_price = max(position.highest_price, snapshot.price)
        position.lowest_price = min(position.lowest_price, snapshot.price)
        signals: list[BacktestSignalRecord] = []
        trades: list[BacktestTradeRecord] = []

        partial_exits = sorted(
            [item for item in risk.get("partial_exits") or [] if item.get("enabled", True)],
            key=lambda item: float(item.get("profit", 0)),
        )
        for item in partial_exits:
            partial_id = item.get("id") or ""
            if partial_id in position.taken_partial_ids:
                continue
            if self.profit_ratio(position, snapshot.price, fee_ratio) < float(item.get("profit", 0)):
                continue
            sold_amount = position.remaining_amount * (float(item.get("size_pct", 0)) / 100.0)
            trade = self.close_trade_slice(position, sold_amount, snapshot.price, snapshot.timestamp, partial_id, fee_ratio)
            if not trade:
                continue
            position.taken_partial_ids.append(partial_id)
            trades.append(trade)
            signals.append(
                BacktestSignalRecord(
                    timestamp=snapshot.timestamp,
                    price=snapshot.price,
                    signal=self.close_signal(position.side),
                    confidence=100.0,
                    indicators={"pair": position.symbol, "side": position.side, "profit_ratio": trade.profit_pct / 100.0, **snapshot.indicators},
                    reasoning=f"Paper exit: {partial_id}",
                )
            )

        if position.remaining_amount <= 1e-12:
            return signals, trades

        exit_reason = self.resolve_exit_reason(position, snapshot.price, snapshot.timestamp, self.exit_signal_for_position(position, snapshot), risk, fee_ratio)
        if not exit_reason:
            return signals, trades
        trade = self.close_trade_slice(position, position.remaining_amount, snapshot.price, snapshot.timestamp, exit_reason, fee_ratio)
        if not trade:
            return signals, trades
        trades.append(trade)
        signals.append(
            BacktestSignalRecord(
                timestamp=snapshot.timestamp,
                price=snapshot.price,
                signal=self.close_signal(position.side),
                confidence=100.0,
                indicators={"pair": position.symbol, "side": position.side, "profit_ratio": trade.profit_pct / 100.0, **snapshot.indicators},
                reasoning=f"Paper exit: {exit_reason}",
            )
        )
        return signals, trades

    def resolve_exit_reason(
        self,
        position: PaperPosition,
        price: float,
        current_time: datetime,
        exit_signal: bool,
        risk: dict[str, Any],
        fee_ratio: float,
    ) -> str | None:
        if self.profit_ratio(position, price, fee_ratio) <= float((risk.get("stoploss") if risk else -0.1) or -0.1):
            return "stoploss"
        trailing_reason = self.trailing_exit_reason(position, price, fee_ratio, risk.get("trailing") or {})
        if trailing_reason:
            return trailing_reason
        if exit_signal:
            return "exit_signal"
        enabled_partials = [item for item in risk.get("partial_exits") or [] if item.get("enabled", True)]
        if len(position.taken_partial_ids) >= len(enabled_partials):
            required_roi = self.required_roi(position, current_time, risk)
            if required_roi is not None and self.profit_ratio(position, price, fee_ratio) >= required_roi:
                return "roi_target"
        return None

    def trailing_exit_reason(self, position: PaperPosition, price: float, fee_ratio: float, trailing: dict[str, Any]) -> str | None:
        if not trailing.get("enabled"):
            return None
        positive = float(trailing.get("positive", 0.0))
        offset = float(trailing.get("offset", positive))
        best_price = position.highest_price if position.side == "long" else position.lowest_price
        max_profit_ratio = self.profit_ratio(position, best_price, fee_ratio)
        current_profit_ratio = self.profit_ratio(position, price, fee_ratio)
        threshold = offset if trailing.get("only_offset_reached", True) else positive
        if max_profit_ratio < threshold:
            return None
        return "trailing_stop" if current_profit_ratio <= max(max_profit_ratio - positive, 0.0) else None

    def required_roi(self, position: PaperPosition, current_time: datetime, risk: dict[str, Any]) -> float | None:
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

    def close_trade_slice(
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
        if position.side == "long":
            exit_value = (sold_amount * price) * (1.0 - fee_ratio)
            profit_abs = exit_value - cost_share
        else:
            entry_notional = cost_share / (1.0 + fee_ratio) if fee_ratio < 1.0 else 0.0
            open_fee = cost_share - entry_notional
            buyback_cost = (sold_amount * price) * (1.0 + fee_ratio)
            profit_abs = entry_notional - buyback_cost - open_fee
        position.remaining_amount -= sold_amount
        position.remaining_cost -= cost_share
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
            duration_minutes=max(int((closed_at - position.opened_at).total_seconds() // 60), 0),
            entry_tag="long_entry_signal" if position.side == "long" else "short_entry_signal",
            exit_reason=exit_reason,
            leverage=1.0,
            pair=position.symbol,
            side=position.side,
        )

    def serialize_positions(self, positions: dict[str, PaperPosition]) -> dict[str, dict[str, Any]]:
        return {
            symbol: {
                "symbol": item.symbol,
                "side": item.side,
                "opened_at": item.opened_at.isoformat(),
                "entry_price": item.entry_price,
                "remaining_amount": item.remaining_amount,
                "remaining_cost": item.remaining_cost,
                "highest_price": item.highest_price,
                "lowest_price": item.lowest_price,
                "last_price": item.last_price,
                "taken_partial_ids": list(item.taken_partial_ids),
            }
            for symbol, item in positions.items()
        }

    def deserialize_positions(self, payload: dict[str, Any]) -> dict[str, PaperPosition]:
        return {
            symbol: PaperPosition(
                symbol=item.get("symbol") or symbol,
                side=str(item.get("side") or "long"),
                opened_at=datetime.fromisoformat(item["opened_at"]),
                entry_price=float(item.get("entry_price", 0.0)),
                remaining_amount=float(item.get("remaining_amount", 0.0)),
                remaining_cost=float(item.get("remaining_cost", 0.0)),
                highest_price=float(item.get("highest_price", item.get("entry_price", 0.0))),
                lowest_price=float(item.get("lowest_price", item.get("entry_price", 0.0))),
                last_price=float(item.get("last_price", item.get("entry_price", 0.0))),
                taken_partial_ids=list(item.get("taken_partial_ids") or []),
            )
            for symbol, item in (payload or {}).items()
        }

    def profit_ratio(self, position: PaperPosition, price: float, fee_ratio: float) -> float:
        if position.remaining_cost <= 0:
            return 0.0
        if position.side == "long":
            liquidation_value = position.remaining_amount * price * (1.0 - fee_ratio)
            return (liquidation_value - position.remaining_cost) / position.remaining_cost
        entry_notional = position.remaining_cost / (1.0 + fee_ratio) if fee_ratio < 1.0 else 0.0
        open_fee = position.remaining_cost - entry_notional
        buyback_cost = position.remaining_amount * price * (1.0 + fee_ratio)
        return (entry_notional - buyback_cost - open_fee) / position.remaining_cost

    def current_equity(
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
            if position.side == "long":
                equity += position.remaining_amount * mark_price * (1.0 - fee_ratio)
            else:
                equity += position.remaining_cost + (self.profit_ratio(position, mark_price, fee_ratio) * position.remaining_cost)
        return equity

    def entry_side(self, snapshot) -> str | None:
        if snapshot.long_entry_signal and not snapshot.short_entry_signal:
            return "long"
        if snapshot.short_entry_signal and not snapshot.long_entry_signal:
            return "short"
        return None

    def exit_signal_for_position(self, position: PaperPosition, snapshot) -> bool:
        return bool(snapshot.long_exit_signal) if position.side == "long" else bool(snapshot.short_exit_signal)

    def close_signal(self, side: str) -> str:
        return "SELL" if side == "long" else "BUY"
