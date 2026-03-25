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
    symbols: list[str]


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

    def run_iteration(
        self,
        *,
        label: str,
        context: FreqtradeExecutionContext,
        strategy_config: dict[str, Any],
        start_date: datetime,
        end_date: datetime,
    ) -> IterationResult:
        run_key = self._build_run_key(context.symbols, context.timeframe, start_date, end_date, label)
        run_root = self.workspace_root / run_key
        user_data_dir = run_root / "user_data"
        data_dir = user_data_dir / "data" / settings.EXCHANGE_ID
        strategies_dir = user_data_dir / "strategies"
        results_dir = user_data_dir / "backtest_results"
        config_path = run_root / "config.json"
        strategy_path = strategies_dir / self.strategy_file_name

        if run_root.exists():
            shutil.rmtree(run_root)
        results_dir.mkdir(parents=True, exist_ok=True)
        strategies_dir.mkdir(parents=True, exist_ok=True)
        data_dir.mkdir(parents=True, exist_ok=True)

        total_candles = self._export_history(
            symbols=context.symbols,
            timeframe=context.timeframe,
            start_date=start_date,
            end_date=end_date,
            data_dir=data_dir,
            warmup_bars=self.strategy_builder.warmup_bars(context.strategy.template, strategy_config),
        )
        strategy_path.write_text(
            self.strategy_builder.build_code(context.strategy.template, context.timeframe, strategy_config),
            encoding="utf-8",
        )
        config_path.write_text(
            json.dumps(
                self._build_config(
                    symbols=context.symbols,
                    timeframe=context.timeframe,
                    initial_cash=context.initial_cash,
                    portfolio=context.portfolio,
                    stake_currency=context.stake_currency,
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
            str(data_dir),
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
            *context.symbols,
            "--no-color",
        ]
        logger.info(
            f"启动 Freqtrade 回测: label={label}, pairs={','.join(context.symbols)}, tf={context.timeframe}, "
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
            symbols=context.symbols,
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
        symbols: list[str],
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
        data_dir: Path,
        warmup_bars: int,
    ) -> int:
        total_candles = 0
        handler = JsonDataHandler(data_dir)
        warmup_start = start_date - (self._timeframe_delta(timeframe) * warmup_bars)
        start_ms = int(start_date.timestamp() * 1000)
        end_ms = int(end_date.timestamp() * 1000)
        for symbol in symbols:
            rows = self.market_data_service.fetch_ohlcv_range(symbol, timeframe, warmup_start, end_date)
            if not rows:
                raise RuntimeError(f"没有可用于 Freqtrade 回测的历史数据: {symbol} {timeframe}")
            frame = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
            frame["date"] = pd.to_datetime(frame["timestamp"], unit="ms", utc=True)
            frame = frame.loc[:, ["date", "open", "high", "low", "close", "volume"]]
            handler.ohlcv_store(symbol, timeframe, frame, CandleType.SPOT)
            total_candles += int(frame["date"].astype("int64").floordiv(1_000_000).between(start_ms, end_ms).sum())
        return total_candles

    def _build_config(
        self,
        *,
        symbols: list[str],
        timeframe: str,
        initial_cash: float,
        portfolio: PortfolioConfigRecord,
        stake_currency: str,
    ) -> dict[str, Any]:
        if portfolio.stake_mode == "fixed":
            stake_amount: str | float = round(initial_cash * portfolio.position_size_pct / 100.0, 8)
            tradable_balance_ratio = min((portfolio.max_open_trades * portfolio.position_size_pct) / 100.0, 1.0)
        else:
            stake_amount = "unlimited"
            tradable_balance_ratio = min((portfolio.max_open_trades * portfolio.position_size_pct) / 100.0, 0.99)
        return {
            "$schema": "https://schema.freqtrade.io/schema.json",
            "max_open_trades": portfolio.max_open_trades,
            "stake_currency": stake_currency,
            "stake_amount": stake_amount,
            "tradable_balance_ratio": max(tradable_balance_ratio, 0.01),
            "dry_run": True,
            "dry_run_wallet": initial_cash,
            "cancel_open_orders_on_exit": False,
            "trading_mode": "spot",
            "timeframe": timeframe,
            "dataformat_ohlcv": "json",
            "dataformat_trades": "json",
            "entry_pricing": {
                "price_side": "other",
                "use_order_book": False,
                "order_book_top": 1,
                "price_last_balance": 0.0,
                "check_depth_of_market": {"enabled": False, "bids_to_ask_delta": 1},
            },
            "exit_pricing": {
                "price_side": "other",
                "use_order_book": False,
                "order_book_top": 1,
            },
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
