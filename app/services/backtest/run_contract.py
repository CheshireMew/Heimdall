from __future__ import annotations

import math
from typing import Any

from app.services.backtest.models import PortfolioConfigRecord, ResearchConfigRecord, StrategyVersionRecord


CURRENT_BACKTEST_RUN_SCHEMA_VERSION = 3

BACKTEST_EXECUTION_MODE = "backtest"
PAPER_LIVE_EXECUTION_MODE = "paper_live"
FREQTRADE_ENGINE = "Freqtrade"
PAPER_LIVE_ENGINE = "PaperLive"
FACTOR_BLEND_ENGINE = "FactorBlend"
FACTOR_BLEND_PAPER_ENGINE = "FactorBlendPaper"

_MISSING = object()


def build_portfolio_payload(portfolio: PortfolioConfigRecord) -> dict[str, Any]:
    return {
        "symbols": list(portfolio.symbols),
        "max_open_trades": portfolio.max_open_trades,
        "position_size_pct": portfolio.position_size_pct,
        "stake_mode": portfolio.stake_mode,
    }


def build_research_payload(research: ResearchConfigRecord) -> dict[str, Any]:
    return {
        "slippage_bps": research.slippage_bps,
        "funding_rate_daily": research.funding_rate_daily,
        "in_sample_ratio": research.in_sample_ratio,
        "optimize_metric": research.optimize_metric,
        "optimize_trials": research.optimize_trials,
        "rolling_windows": research.rolling_windows,
    }


def build_base_metadata(
    *,
    strategy: StrategyVersionRecord,
    symbols: list[str],
    initial_cash: float,
    fee_rate: float,
    portfolio_label: str,
    portfolio: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": CURRENT_BACKTEST_RUN_SCHEMA_VERSION,
        "strategy_key": strategy.strategy_key,
        "strategy_name": strategy.strategy_name,
        "strategy_version": strategy.version,
        "strategy_template": strategy.template,
        "symbols": symbols,
        "portfolio_label": portfolio_label,
        "initial_cash": initial_cash,
        "fee_rate": fee_rate,
        "portfolio": portfolio,
    }


def build_backtest_metadata(
    *,
    strategy: StrategyVersionRecord,
    symbols: list[str],
    initial_cash: float,
    fee_rate: float,
    portfolio: PortfolioConfigRecord,
    research: ResearchConfigRecord,
) -> dict[str, Any]:
    return make_json_safe(
        {
            **build_base_metadata(
                strategy=strategy,
                symbols=symbols,
                initial_cash=initial_cash,
                fee_rate=fee_rate,
                portfolio_label=symbols[0] if len(symbols) == 1 else f"{len(symbols)} symbols",
                portfolio=build_portfolio_payload(portfolio),
            ),
            "research": build_research_payload(research),
        }
    )


def build_paper_metadata(
    *,
    strategy: StrategyVersionRecord,
    symbols: list[str],
    initial_cash: float,
    fee_rate: float,
    portfolio: PortfolioConfigRecord,
    runtime_state: dict[str, Any],
    paper_live: dict[str, Any],
    report: dict[str, Any],
) -> dict[str, Any]:
    last_updated = (paper_live or {}).get("last_updated")
    if not last_updated:
        raise ValueError("paper_live.last_updated 不能为空")

    metadata = {
        **build_base_metadata(
            strategy=strategy,
            symbols=symbols,
            initial_cash=initial_cash,
            fee_rate=fee_rate,
            portfolio_label=symbols[0] if len(symbols) == 1 else f"{len(symbols)} symbols",
            portfolio=build_portfolio_payload(portfolio),
        ),
    }
    stop_reason = paper_live["stop_reason"] if isinstance(paper_live, dict) and "stop_reason" in paper_live else _MISSING
    return update_paper_metadata(
        metadata,
        runtime_state=runtime_state,
        last_updated=last_updated,
        report=report,
        stop_reason=stop_reason,
    )


def ensure_paper_runtime_state(runtime_state: dict[str, Any], *, symbols: list[str]) -> dict[str, Any]:
    if not isinstance(runtime_state, dict):
        raise ValueError("paper runtime_state 必须是字典")

    normalized = {
        key: value
        for key, value in runtime_state.items()
        if key not in {"cash_balance", "last_processed", "positions"}
    }

    normalized["cash_balance"] = float(runtime_state.get("cash_balance", 0.0) or 0.0)
    normalized["last_processed"] = _normalize_last_processed_map(runtime_state.get("last_processed"), symbols=symbols)
    normalized["positions"] = _normalize_paper_positions(runtime_state.get("positions"), symbols=symbols)
    return normalized


def update_paper_metadata(
    metadata: dict[str, Any] | None,
    *,
    runtime_state: dict[str, Any],
    last_updated: str,
    report: dict[str, Any] | object = _MISSING,
    stop_reason: str | None | object = _MISSING,
) -> dict[str, Any]:
    payload = dict(metadata or {})
    symbols = [str(symbol) for symbol in (payload.get("symbols") or []) if symbol]
    normalized_runtime_state = ensure_paper_runtime_state(runtime_state, symbols=symbols)
    existing_paper_live = dict(payload.get("paper_live") or {}) if isinstance(payload.get("paper_live"), dict) else {}

    payload["schema_version"] = CURRENT_BACKTEST_RUN_SCHEMA_VERSION
    payload["runtime_state"] = normalized_runtime_state
    payload["paper_live"] = _build_paper_live_state(
        existing_paper_live,
        runtime_state=normalized_runtime_state,
        last_updated=last_updated,
        stop_reason=stop_reason,
    )
    if report is not _MISSING:
        payload["report"] = report
    return make_json_safe(payload)


def _build_paper_live_state(
    current_paper_live: dict[str, Any],
    *,
    runtime_state: dict[str, Any],
    last_updated: str,
    stop_reason: str | None | object,
) -> dict[str, Any]:
    positions = list((runtime_state.get("positions") or {}).values())
    paper_live = {
        key: value
        for key, value in current_paper_live.items()
        if key not in {"cash_balance", "open_positions", "positions", "last_updated", "stop_reason"}
    }
    paper_live["cash_balance"] = float(runtime_state.get("cash_balance", 0.0) or 0.0)
    paper_live["open_positions"] = len(positions)
    paper_live["positions"] = positions
    paper_live["last_updated"] = last_updated
    if stop_reason is not _MISSING:
        paper_live["stop_reason"] = stop_reason
    elif "stop_reason" in current_paper_live:
        paper_live["stop_reason"] = current_paper_live["stop_reason"]
    return paper_live


def _normalize_last_processed_map(value: Any, *, symbols: list[str]) -> dict[str, int | None]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError("paper runtime_state.last_processed 必须是按 symbol 存储的字典")

    normalized: dict[str, int | None] = {}
    known_symbols = {str(symbol) for symbol in symbols if symbol}
    for symbol, timestamp in value.items():
        symbol_key = str(symbol).strip()
        if not symbol_key:
            continue
        if known_symbols and symbol_key not in known_symbols:
            raise ValueError(f"paper runtime_state.last_processed 存在未知 symbol: {symbol_key}")
        normalized[symbol_key] = _normalize_optional_timestamp_ms(timestamp)
    return normalized


def _normalize_paper_positions(value: Any, *, symbols: list[str]) -> dict[str, dict[str, Any]]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError("paper runtime_state.positions 必须是按 symbol 存储的字典")

    normalized: dict[str, dict[str, Any]] = {}
    known_symbols = {str(symbol) for symbol in symbols if symbol}
    for symbol, payload in value.items():
        symbol_key = str(symbol).strip()
        if not symbol_key:
            continue
        if known_symbols and symbol_key not in known_symbols:
            raise ValueError(f"paper runtime_state.positions 存在未知 symbol: {symbol_key}")
        normalized[symbol_key] = _normalize_paper_position_payload(payload, symbol_hint=symbol_key)
    return normalized


def _normalize_paper_position_payload(payload: Any, *, symbol_hint: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError(f"paper position {symbol_hint} 必须是字典")

    missing_keys = [key for key in ("opened_at", "entry_price", "remaining_amount", "remaining_cost") if payload.get(key) is None]
    if missing_keys:
        raise ValueError(f"paper position {symbol_hint} 缺少字段: {', '.join(missing_keys)}")

    entry_price = float(payload.get("entry_price", 0.0) or 0.0)
    side = str(payload.get("side") or "long").strip().lower()
    if side not in {"long", "short"}:
        side = "long"
    normalized = {
        "symbol": str(payload.get("symbol") or symbol_hint),
        "side": side,
        "opened_at": payload["opened_at"],
        "entry_price": entry_price,
        "remaining_amount": float(payload["remaining_amount"]),
        "remaining_cost": float(payload["remaining_cost"]),
        "highest_price": float(payload.get("highest_price", entry_price) or entry_price),
        "lowest_price": float(payload.get("lowest_price", entry_price) or entry_price),
        "last_price": float(payload.get("last_price", entry_price) or entry_price),
        "taken_partial_ids": list(payload.get("taken_partial_ids") or []),
    }
    if "entry_score" in payload:
        normalized["entry_score"] = float(payload.get("entry_score", 0.0) or 0.0)
    return normalized


def _normalize_optional_timestamp_ms(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"paper last_processed 无法转换为毫秒时间戳: {value}") from exc


def make_json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: make_json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [make_json_safe(item) for item in value]
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    return value
