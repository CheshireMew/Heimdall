from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from app.services.market.market_data_service import MarketDataService
from app.services.backtest.run_contract import ensure_paper_runtime_state


class PaperRuntimeService:
    def __init__(self, market_data_service: MarketDataService, runtime: Any) -> None:
        self.market_data_service = market_data_service
        self.runtime = runtime

    def build_pending_snapshots(
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
        timeframe_delta = self.timeframe_delta(timeframe)
        timeframe_ms = int(timeframe_delta.total_seconds() * 1000)
        for symbol in symbols:
            last_processed_ms = (runtime_state.get("last_processed") or {}).get(symbol)
            start_at = datetime.utcfromtimestamp(last_processed_ms / 1000.0) - (timeframe_delta * warmup_bars) if last_processed_ms else now - (timeframe_delta * (warmup_bars + 2))
            candles = self.market_data_service.fetch_live_ohlcv_range(symbol, timeframe, start_at, now)
            closed_candles = [row for row in candles if row[0] + timeframe_ms <= int(now.timestamp() * 1000)]
            snapshots = self.runtime.build_signal_snapshots(strategy.template, strategy.config, closed_candles, timeframe, after_timestamp_ms=last_processed_ms)
            pending.extend((symbol, snapshot) for snapshot in snapshots)
        pending.sort(key=lambda item: (item[1].timestamp, item[0]))
        return pending

    def latest_closed_timestamp(
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

    def load_runtime_state(self, metadata: dict[str, Any]) -> dict[str, Any]:
        runtime_state = dict(metadata.get("runtime_state") or {})
        if "cash_balance" not in runtime_state:
            runtime_state["cash_balance"] = float(metadata.get("initial_cash", 0.0))
        return ensure_paper_runtime_state(runtime_state, symbols=list(metadata.get("symbols") or []))

    def timeframe_delta(self, timeframe: str) -> timedelta:
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
