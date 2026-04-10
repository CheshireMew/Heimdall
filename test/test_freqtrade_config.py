from __future__ import annotations

from pathlib import Path

from app.services.backtest.freqtrade_execution import FreqtradeIterationExecutor
from app.services.backtest.freqtrade_strategy_builder import FreqtradeStrategyBuilder
from app.services.backtest.models import PortfolioConfigRecord, ResearchConfigRecord, StrategyVersionRecord


class _DummyStrategyBuilder:
    def warmup_bars(self, template, config, timeframe):
        return 0

    def build_code(self, template, timeframe, config):
        return ""


class _DummyResultBuilder:
    pass


def _make_executor() -> FreqtradeIterationExecutor:
    return FreqtradeIterationExecutor(
        workspace_root=Path("E:/Work/Code/Heimdall/.codex_tmp_freqtrade"),
        strategy_class_name="HeimdallStrategy",
        market_data_service=object(),
        strategy_builder=_DummyStrategyBuilder(),
        result_builder=_DummyResultBuilder(),
    )


def test_freqtrade_config_uses_same_side_pricing_for_spot_and_futures():
    executor = _make_executor()
    strategy_builder = FreqtradeStrategyBuilder("HeimdallStrategy")
    portfolio = PortfolioConfigRecord(
        symbols=["BTC/USDT"],
        max_open_trades=2,
        position_size_pct=25,
        stake_mode="fixed",
    )
    trade_settings = strategy_builder.trade_settings("ema_rsi_macd", {})

    spot_config = executor._build_config(
        symbols=["BTC/USDT"],
        timeframe="1h",
        initial_cash=10000,
        portfolio=portfolio,
        stake_currency="USDT",
        market_type="spot",
        trade_settings=trade_settings,
    )
    futures_config = executor._build_config(
        symbols=["BTC/USDT:USDT"],
        timeframe="1h",
        initial_cash=10000,
        portfolio=portfolio,
        stake_currency="USDT",
        market_type="futures",
        trade_settings=trade_settings,
    )

    assert spot_config["order_types"]["entry"] == "market"
    assert spot_config["order_types"]["exit"] == "market"
    assert spot_config["entry_pricing"]["price_side"] == "other"
    assert spot_config["exit_pricing"]["price_side"] == "other"
    assert spot_config["entry_pricing"]["use_order_book"] is True
    assert spot_config["exit_pricing"]["use_order_book"] is True
    assert futures_config["entry_pricing"]["price_side"] == "other"
    assert futures_config["exit_pricing"]["price_side"] == "other"
    assert futures_config["entry_pricing"]["use_order_book"] is True
    assert futures_config["exit_pricing"]["use_order_book"] is True
    assert futures_config["trading_mode"] == "futures"
    assert futures_config["margin_mode"] == "isolated"
