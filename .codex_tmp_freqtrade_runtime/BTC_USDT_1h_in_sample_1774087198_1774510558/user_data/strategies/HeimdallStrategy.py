import pandas as pd
import talib.abstract as ta
from pandas import DataFrame
from freqtrade.strategy import IStrategy


class HeimdallStrategy(IStrategy):
    INTERFACE_VERSION = 3
    can_short = False
    timeframe = "1h"
    process_only_new_candles = True
    startup_candle_count = 40
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    minimal_roi = {'180': 0.04, '0': 0.09}
    stoploss = -0.12
    trailing_stop = True
    trailing_stop_positive = 0.02
    trailing_stop_positive_offset = 0.04
    trailing_only_offset_is_reached = True
    position_adjustment_enable = True
    order_types = {'entry': 'market', 'exit': 'market', 'stoploss': 'market', 'stoploss_on_exchange': False}

    def _resample_ohlcv(self, dataframe: DataFrame, timeframe: str) -> DataFrame:
        rule_map = {"1m": "1min", "5m": "5min", "15m": "15min", "1h": "1h", "4h": "4h", "1d": "1D"}
        if timeframe not in rule_map:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        indexed = dataframe[["date", "open", "high", "low", "close", "volume"]].copy().set_index("date")
        resampled = (
            indexed.resample(rule_map[timeframe], label="right", closed="right")
            .agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
            .dropna()
            .reset_index()
        )
        return resampled

    def _merge_indicator_frame(self, dataframe: DataFrame, informative: DataFrame, columns: list[str]) -> DataFrame:
        if not columns:
            return dataframe
        return pd.merge_asof(
            dataframe.sort_values("date"),
            informative[["date", *columns]].sort_values("date"),
            on="date",
            direction="backward",
        )

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe = dataframe.sort_values("date").copy()
        dataframe["ema__value"] = ta.EMA(dataframe, timeperiod=20)
        dataframe["rsi__value"] = ta.RSI(dataframe, timeperiod=14)
        macd_macd = ta.MACD(dataframe, fastperiod=12, slowperiod=26, signalperiod=9)
        dataframe["macd__macd"] = macd_macd["macd"]
        dataframe["macd__signal"] = macd_macd["macdsignal"]
        dataframe["macd__hist"] = macd_macd["macdhist"]
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = None
        dataframe["enter_short"] = 0
        dataframe["enter_short_tag"] = None
        dataframe.loc[(((((dataframe["volume"] >= 0)) & ((dataframe["volume"] >= 0)))) & (((dataframe["close"] > dataframe["ema__value"]) & (dataframe["rsi__value"] < 68.0) & (dataframe["macd__macd"] > dataframe["macd__signal"])))), ["enter_long", "enter_tag"]] = (1, "trend_long_entry")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        dataframe["exit_tag"] = None
        dataframe["exit_short"] = 0
        dataframe["exit_short_tag"] = None
        dataframe.loc[(((((dataframe["volume"] >= 0)) & ((dataframe["volume"] >= 0)))) & (((dataframe["close"] < dataframe["ema__value"]) | (dataframe["rsi__value"] > 32.0)))), ["exit_long", "exit_tag"]] = (1, "trend_long_exit")
        return dataframe

    def adjust_trade_position(self, trade, current_time, current_rate, current_profit, min_stake, max_stake, current_entry_rate, current_exit_rate, current_entry_profit, current_exit_profit, **kwargs):
        partial_steps = [{'profit': 0.05, 'size_pct': 35.0}, {'profit': 0.09, 'size_pct': 25.0}]
        if trade.nr_of_successful_exits >= len(partial_steps):
            return None
        step = partial_steps[trade.nr_of_successful_exits]
        if current_profit < step["profit"]:
            return None
        reduction = trade.stake_amount * (step["size_pct"] / 100.0)
        if min_stake and reduction < min_stake:
            return None
        return -reduction, f"partial_{trade.nr_of_successful_exits + 1}"

