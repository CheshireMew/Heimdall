from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from freqtrade.data.history.datahandlers.jsondatahandler import JsonDataHandler
from freqtrade.enums import CandleType

from app.services.backtest.models import (
    BacktestExecutionResult,
    PortfolioConfigRecord,
    ResearchConfigRecord,
    StrategyVersionRecord,
)
from app.services.market.market_data_service import MarketDataService
from config import settings
from utils.logger import logger


@dataclass(slots=True)
class FreqtradeExecutionContext:
    strategy: StrategyVersionRecord
    portfolio: PortfolioConfigRecord
    research: ResearchConfigRecord
    timeframe: str
    initial_cash: float
    fee_rate: float
    fee_ratio: float
    stake_currency: str
    data_symbols: list[str]
    execution_symbols: list[str]
    market_type: str
    direction: str


@dataclass(slots=True)
class IterationResult:
    label: str
    start_date: datetime
    end_date: datetime
    config: dict[str, Any]
    execution: BacktestExecutionResult


class FreqtradeIterationExecutor:
    def __init__(
        self,
        *,
        workspace_root: Path,
        strategy_class_name: str,
        market_data_service: MarketDataService,
        strategy_builder: Any,
        result_builder: Any,
    ) -> None:
        self.workspace_root = workspace_root
        self.strategy_class_name = strategy_class_name
        self.strategy_file_name = f"{strategy_class_name}.py"
        self.market_data_service = market_data_service
        self.strategy_builder = strategy_builder
        self.result_builder = result_builder
        self.shared_data_dir = self.workspace_root / "_shared_data" / settings.EXCHANGE_ID
        self.shared_manifest_path = self.workspace_root / "_shared_data" / "coverage.json"

    def run_iteration(
        self,
        *,
        label: str,
        context: FreqtradeExecutionContext,
        strategy_config: dict[str, Any],
        start_date: datetime,
        end_date: datetime,
    ) -> IterationResult:
        run_key = self._build_run_key(context.execution_symbols, context.timeframe, start_date, end_date, label)
        run_root = self.workspace_root / run_key
        user_data_dir = run_root / "user_data"
        strategies_dir = user_data_dir / "strategies"
        results_dir = user_data_dir / "backtest_results"
        config_path = run_root / "config.json"
        strategy_path = strategies_dir / self.strategy_file_name

        if run_root.exists():
            shutil.rmtree(run_root)
        results_dir.mkdir(parents=True, exist_ok=True)
        strategies_dir.mkdir(parents=True, exist_ok=True)
        self.shared_data_dir.mkdir(parents=True, exist_ok=True)

        total_candles = self._export_history(
            data_symbols=context.data_symbols,
            execution_symbols=context.execution_symbols,
            timeframe=context.timeframe,
            start_date=start_date,
            end_date=end_date,
            warmup_bars=self.strategy_builder.warmup_bars(context.strategy.template, strategy_config, context.timeframe),
            market_type=context.market_type,
        )
        strategy_path.write_text(
            self.strategy_builder.build_code(context.strategy.template, context.timeframe, strategy_config),
            encoding="utf-8",
        )
        config_path.write_text(
            json.dumps(
                self._build_config(
                    symbols=context.execution_symbols,
                    timeframe=context.timeframe,
                    initial_cash=context.initial_cash,
                    portfolio=context.portfolio,
                    stake_currency=context.stake_currency,
                    market_type=context.market_type,
                    trade_settings=self.strategy_builder.trade_settings(context.strategy.template, strategy_config),
                ),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        command = [
            sys.executable,
            "-m",
            "freqtrade",
            "backtesting",
            "--config",
            str(config_path),
            "--userdir",
            str(user_data_dir),
            "--strategy-path",
            str(strategies_dir),
            "--strategy",
            self.strategy_class_name,
            "--datadir",
            str(self.shared_data_dir),
            "--timeframe",
            context.timeframe,
            "--timerange",
            self._build_timerange(start_date, end_date),
            "--data-format-ohlcv",
            "json",
            "--cache",
            "none",
            "--export",
            "trades",
            "--backtest-directory",
            str(results_dir),
            "--fee",
            str(context.fee_ratio),
            "--pairs",
            *context.execution_symbols,
            "--no-color",
        ]
        logger.info(
            f"启动 Freqtrade 回测: label={label}, pairs={','.join(context.execution_symbols)}, tf={context.timeframe}, "
            f"range={start_date.isoformat()}->{end_date.isoformat()}"
        )
        try:
            completed = subprocess.run(
                command,
                cwd=run_root,
                capture_output=True,
                text=True,
                timeout=settings.FREQTRADE_BACKTEST_TIMEOUT_SECONDS,
                check=True,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                f"Freqtrade 回测超时，当前超时阈值为 {settings.FREQTRADE_BACKTEST_TIMEOUT_SECONDS} 秒。"
            ) from exc
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(self._format_process_error(exc.stdout, exc.stderr)) from exc

        if completed.stdout:
            logger.debug(completed.stdout.strip())
        if completed.stderr:
            logger.debug(completed.stderr.strip())

        execution = self.result_builder.build_execution_result(
            results_dir=results_dir,
            data_symbols=context.data_symbols,
            execution_symbols=context.execution_symbols,
            timeframe=context.timeframe,
            start_date=start_date,
            end_date=end_date,
            total_candles=total_candles,
            initial_cash=context.initial_cash,
            fee_rate=context.fee_rate,
            fee_ratio=context.fee_ratio,
            research=context.research,
        )
        return IterationResult(
            label=label,
            start_date=start_date,
            end_date=end_date,
            config=dict(strategy_config),
            execution=execution,
        )

    def _export_history(
        self,
        *,
        data_symbols: list[str],
        execution_symbols: list[str],
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
        warmup_bars: int,
        market_type: str,
    ) -> int:
        total_candles = 0
        handler = JsonDataHandler(self.shared_data_dir)
        manifest = self._load_shared_coverage()
        manifest_changed = False
        warmup_start = start_date - (self._timeframe_delta(timeframe) * warmup_bars)
        start_ms = int(start_date.timestamp() * 1000)
        end_ms = int(end_date.timestamp() * 1000)
        request_start_ms = int(warmup_start.timestamp() * 1000)
        for data_symbol, execution_symbol in zip(data_symbols, execution_symbols, strict=True):
            # Data and execution are intentionally decoupled here:
            # - data_symbol is the only source we query from our own database/cache
            # - execution_symbol is the pair name Freqtrade expects under the selected trading_mode
            # This lets futures backtests reuse spot OHLCV as synthetic mark/last prices
            # without maintaining a second futures kline dataset.
            candle_type = CandleType.FUTURES if market_type == "futures" else CandleType.SPOT
            manifest_key = self._shared_coverage_key(
                execution_symbol=execution_symbol,
                timeframe=timeframe,
                candle_type=candle_type,
            )
            coverage = manifest.get(manifest_key) or {}
            if self._needs_history_refresh(
                coverage=coverage,
                data_symbol=data_symbol,
                start_ms=request_start_ms,
                end_ms=end_ms,
            ):
                rows = self.market_data_service.fetch_ohlcv_range(data_symbol, timeframe, warmup_start, end_date)
                if not rows:
                    raise RuntimeError(f"没有可用于 Freqtrade 回测的历史数据: {data_symbol} {timeframe}")
                frame = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
                frame["date"] = pd.to_datetime(frame["timestamp"], unit="ms", utc=True)
                frame = frame.loc[:, ["date", "open", "high", "low", "close", "volume"]]
                handler.ohlcv_store(execution_symbol, timeframe, frame, candle_type)
                manifest[manifest_key] = {
                    "data_symbol": data_symbol,
                    "start_ms": int(frame["date"].iloc[0].value // 1_000_000),
                    "end_ms": int(frame["date"].iloc[-1].value // 1_000_000),
                }
                manifest_changed = True
            frame = handler._ohlcv_load(execution_symbol, timeframe, None, candle_type)
            if frame.empty:
                raise RuntimeError(f"共享回测数据不可用: {execution_symbol} {timeframe}")
            total_candles += int(frame["date"].astype("int64").floordiv(1_000_000).between(start_ms, end_ms).sum())
        if manifest_changed:
            self._save_shared_coverage(manifest)
        return total_candles

    def _shared_coverage_key(
        self,
        *,
        execution_symbol: str,
        timeframe: str,
        candle_type: CandleType,
    ) -> str:
        return f"{execution_symbol}|{timeframe}|{candle_type.value}"

    def _needs_history_refresh(
        self,
        *,
        coverage: dict[str, Any],
        data_symbol: str,
        start_ms: int,
        end_ms: int,
    ) -> bool:
        if not coverage:
            return True
        if str(coverage.get("data_symbol") or "") != data_symbol:
            return True
        if int(coverage.get("start_ms") or start_ms + 1) > start_ms:
            return True
        if int(coverage.get("end_ms") or end_ms - 1) < end_ms:
            return True
        return False

    def _load_shared_coverage(self) -> dict[str, dict[str, Any]]:
        if not self.shared_manifest_path.exists():
            return {}
        try:
            payload = json.loads(self.shared_manifest_path.read_text(encoding="utf-8"))
        except Exception:
            return {}
        if not isinstance(payload, dict):
            return {}
        return {
            str(key): value
            for key, value in payload.items()
            if isinstance(value, dict)
        }

    def _save_shared_coverage(self, coverage: dict[str, dict[str, Any]]) -> None:
        self.shared_manifest_path.parent.mkdir(parents=True, exist_ok=True)
        self.shared_manifest_path.write_text(
            json.dumps(coverage, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _build_config(
        self,
        *,
        symbols: list[str],
        timeframe: str,
        initial_cash: float,
        portfolio: PortfolioConfigRecord,
        stake_currency: str,
        market_type: str,
        trade_settings: dict[str, Any],
    ) -> dict[str, Any]:
        if portfolio.stake_mode == "fixed":
            stake_amount: str | float = round(initial_cash * portfolio.position_size_pct / 100.0, 8)
            tradable_balance_ratio = 0.99
        else:
            stake_amount = "unlimited"
            tradable_balance_ratio = min((portfolio.max_open_trades * portfolio.position_size_pct) / 100.0, 0.99)
        config = {
            "$schema": "https://schema.freqtrade.io/schema.json",
            "max_open_trades": portfolio.max_open_trades,
            "stake_currency": stake_currency,
            "stake_amount": stake_amount,
            "tradable_balance_ratio": max(tradable_balance_ratio, 0.01),
            "dry_run": True,
            "dry_run_wallet": initial_cash,
            "cancel_open_orders_on_exit": False,
            "trading_mode": "futures" if market_type == "futures" else "spot",
            "timeframe": timeframe,
            "dataformat_ohlcv": "json",
            "dataformat_trades": "json",
            "order_types": dict(trade_settings["order_types"]),
            "entry_pricing": dict(trade_settings["entry_pricing"]),
            "exit_pricing": dict(trade_settings["exit_pricing"]),
            "exchange": {
                "name": settings.EXCHANGE_ID,
                "key": "",
                "secret": "",
                "password": "",
                "ccxt_config": {},
                "ccxt_async_config": {},
                "pair_whitelist": symbols,
                "pair_blacklist": [],
            },
            "pairlists": [{"method": "StaticPairList"}],
            "bot_name": "heimdall-backtest",
            "internals": {"process_throttle_secs": 5},
        }
        if market_type == "futures":
            config["margin_mode"] = "isolated"
        return config

    def _build_run_key(
        self,
        symbols: list[str],
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
        label: str,
    ) -> str:
        return f"{self._sanitize_symbol_fragment(symbols)}_{timeframe}_{label}_{int(start_date.timestamp())}_{int(end_date.timestamp())}"

    def _sanitize_symbol_fragment(self, symbols: list[str]) -> str:
        base = symbols[0] if len(symbols) == 1 else f"portfolio_{len(symbols)}_{symbols[0]}"
        return base.replace("/", "_").replace(":", "_")

    def _build_timerange(self, start_date: datetime, end_date: datetime) -> str:
        return f"{int(start_date.timestamp() * 1000)}-{int(end_date.timestamp() * 1000)}"

    def _timeframe_delta(self, timeframe: str) -> pd.Timedelta:
        value = int(timeframe[:-1])
        unit = timeframe[-1]
        if unit == "m":
            return pd.Timedelta(minutes=value)
        if unit == "h":
            return pd.Timedelta(hours=value)
        if unit == "d":
            return pd.Timedelta(days=value)
        raise ValueError(f"暂不支持的时间周期: {timeframe}")

    def _format_process_error(self, stdout: str, stderr: str) -> str:
        output = (stderr or stdout or "").strip()
        if not output:
            return "Freqtrade 回测执行失败"
        return "Freqtrade 回测执行失败。\n" + "\n".join(output.splitlines()[-20:])
