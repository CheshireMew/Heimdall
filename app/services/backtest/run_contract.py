from __future__ import annotations

from typing import Any

from app.services.backtest.models import PortfolioConfigRecord, ResearchConfigRecord, StrategyVersionRecord


CURRENT_BACKTEST_RUN_SCHEMA_VERSION = 2
LEGACY_BACKTEST_RUN_SCHEMA_VERSION = 1

BACKTEST_EXECUTION_MODE = "backtest"
PAPER_LIVE_EXECUTION_MODE = "paper_live"
LEGACY_BACKTEST_EXECUTION_MODE = "legacy_backtest"


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
    execution_mode: str,
    engine: str,
    strategy: StrategyVersionRecord,
    symbols: list[str],
    initial_cash: float,
    fee_rate: float,
    portfolio_label: str,
    portfolio: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": CURRENT_BACKTEST_RUN_SCHEMA_VERSION,
        "execution_mode": execution_mode,
        "engine": engine,
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
    engine: str = "Freqtrade",
) -> dict[str, Any]:
    return {
        **build_base_metadata(
            execution_mode=BACKTEST_EXECUTION_MODE,
            engine=engine,
            strategy=strategy,
            symbols=symbols,
            initial_cash=initial_cash,
            fee_rate=fee_rate,
            portfolio_label=symbols[0] if len(symbols) == 1 else f"{len(symbols)} symbols",
            portfolio=build_portfolio_payload(portfolio),
        ),
        "research": build_research_payload(research),
    }


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
    engine: str = "PaperLive",
) -> dict[str, Any]:
    return {
        **build_base_metadata(
            execution_mode=PAPER_LIVE_EXECUTION_MODE,
            engine=engine,
            strategy=strategy,
            symbols=symbols,
            initial_cash=initial_cash,
            fee_rate=fee_rate,
            portfolio_label=symbols[0] if len(symbols) == 1 else f"{len(symbols)} symbols",
            portfolio=build_portfolio_payload(portfolio),
        ),
        "runtime_state": runtime_state,
        "paper_live": paper_live,
        "report": report,
    }


def is_current_backtest_metadata(metadata: dict[str, Any] | None) -> bool:
    return _has_required_keys(
        metadata,
        BACKTEST_EXECUTION_MODE,
        required_keys=("strategy_key", "strategy_name", "strategy_version", "strategy_template", "symbols", "portfolio", "research"),
    )


def is_current_paper_metadata(metadata: dict[str, Any] | None) -> bool:
    return _has_required_keys(
        metadata,
        PAPER_LIVE_EXECUTION_MODE,
        required_keys=("strategy_key", "strategy_name", "strategy_version", "strategy_template", "symbols", "portfolio", "runtime_state", "paper_live", "report"),
    )


def normalize_run_metadata(metadata: dict[str, Any] | None) -> tuple[dict[str, Any], bool]:
    payload = dict(metadata or {})

    if is_current_paper_metadata(payload):
        return payload, False

    if _matches_shape(payload, required_keys=("strategy_key", "strategy_name", "strategy_version", "strategy_template", "symbols", "portfolio", "runtime_state", "paper_live", "report")):
        changed = False
        if payload.get("schema_version") != CURRENT_BACKTEST_RUN_SCHEMA_VERSION:
            payload["schema_version"] = CURRENT_BACKTEST_RUN_SCHEMA_VERSION
            changed = True
        if payload.get("execution_mode") != PAPER_LIVE_EXECUTION_MODE:
            payload["execution_mode"] = PAPER_LIVE_EXECUTION_MODE
            changed = True
        return payload, changed

    if is_current_backtest_metadata(payload):
        return payload, False

    if _matches_shape(payload, required_keys=("strategy_key", "strategy_name", "strategy_version", "strategy_template", "symbols", "portfolio", "research")):
        changed = False
        if payload.get("schema_version") != CURRENT_BACKTEST_RUN_SCHEMA_VERSION:
            payload["schema_version"] = CURRENT_BACKTEST_RUN_SCHEMA_VERSION
            changed = True
        if payload.get("execution_mode") != BACKTEST_EXECUTION_MODE:
            payload["execution_mode"] = BACKTEST_EXECUTION_MODE
            changed = True
        return payload, changed

    changed = (
        payload.get("schema_version") != LEGACY_BACKTEST_RUN_SCHEMA_VERSION
        or payload.get("execution_mode") != LEGACY_BACKTEST_EXECUTION_MODE
        or payload.get("legacy_reason") != "incomplete_backtest_contract"
    )
    payload["schema_version"] = LEGACY_BACKTEST_RUN_SCHEMA_VERSION
    payload["execution_mode"] = LEGACY_BACKTEST_EXECUTION_MODE
    payload["legacy_reason"] = "incomplete_backtest_contract"
    return payload, changed


def _has_required_keys(
    metadata: dict[str, Any] | None,
    execution_mode: str,
    *,
    required_keys: tuple[str, ...],
) -> bool:
    if not isinstance(metadata, dict):
        return False
    if metadata.get("schema_version") != CURRENT_BACKTEST_RUN_SCHEMA_VERSION:
        return False
    if metadata.get("execution_mode") != execution_mode:
        return False
    return _matches_shape(metadata, required_keys=required_keys)


def _matches_shape(metadata: dict[str, Any], *, required_keys: tuple[str, ...]) -> bool:
    return all(metadata.get(key) is not None for key in required_keys)
