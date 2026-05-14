from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import talib.abstract as ta

from app.domain.backtest.freqtrade_exit_codegen import render_threshold_custom_exit
from app.domain.backtest.freqtrade_strategy_runtime import (
    render_freqtrade_strategy_runtime,
    resolve_freqtrade_strategy_runtime,
)

TEMPLATE_KEY = "btc_regime_pulse_supertrend"
RUNTIME_CONTRACT: dict[str, Any] = {
    "builder_kind": "scripted",
    "capabilities": {
        "paper": True,
        "version_editing": False,
    },
}
WARMUP_BARS = 220


def build_signal_frame(candles: list[list[float]], timeframe: str) -> pd.DataFrame:
    return _build_btc_regime_pulse_supertrend_frame(candles, timeframe)


def build_strategy_code(*, strategy_class_name: str, timeframe: str) -> str:
    return _build_btc_regime_pulse_supertrend(strategy_class_name, timeframe)


def warmup_bars(_config: dict[str, Any], _timeframe: str) -> int:
    return WARMUP_BARS


def trade_settings(_config: dict[str, Any]) -> dict[str, Any]:
    order_types = {
        "entry": "market",
        "exit": "market",
        "stoploss": "market",
        "stoploss_on_exchange": False,
    }
    return {
        "order_types": order_types,
        "position_adjustment_enable": False,
        "entry_pricing": {
            "price_side": "other",
            "use_order_book": True,
            "order_book_top": 1,
            "price_last_balance": 0.0,
            "check_depth_of_market": {"enabled": False, "bids_to_ask_delta": 1},
        },
        "exit_pricing": {
            "price_side": "other",
            "use_order_book": True,
            "order_book_top": 1,
        },
    }


def _build_btc_regime_pulse_supertrend(strategy_class_name: str, timeframe: str) -> str:
    runtime_block = render_freqtrade_strategy_runtime(
        resolve_freqtrade_strategy_runtime(
            can_short=True,
            timeframe=timeframe,
            startup_candle_count=WARMUP_BARS,
            risk={
                "stoploss": -0.99,
                "trailing": {"enabled": False, "positive": 0.0, "offset": 0.0, "only_offset_reached": True},
            },
            roi_targets={"0": 99.0},
            order_types={"entry": "market", "exit": "market", "stoploss": "market", "stoploss_on_exchange": False},
            has_exit_signals=False,
            has_custom_exit=True,
            position_adjustment_enable=False,
        )
    )
    return f"""import numpy as np
import pandas as pd
import talib.abstract as ta
from pandas import DataFrame
from freqtrade.strategy import IStrategy


class {strategy_class_name}(IStrategy):
{runtime_block}

    atr_length = 10
    base_multiplier = 3.0
    regime_lookback = 40
    adx_length = 14
    adx_threshold = 20
    trend_ema_length = 50
    volume_ma_length = 20
    min_signal_score = 65
    cooldown_bars = 5
    stoploss_atr_multiplier = 6.0
    takeprofit_rr = 2.5

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe = dataframe.sort_values("date").copy()
        dataframe["hl2"] = (dataframe["high"] + dataframe["low"]) / 2.0
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=self.atr_length)
        dataframe["atr_safe"] = dataframe["atr"].fillna(0.001).clip(lower=0.001)
        dataframe["atr_ma"] = dataframe["atr"].rolling(self.regime_lookback).mean()
        dataframe["atr_ratio"] = np.where(dataframe["atr_ma"] > 0, dataframe["atr"] / dataframe["atr_ma"], 1.0)
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=self.adx_length)
        dataframe["regime"] = np.select(
            [
                dataframe["atr_ratio"] > 1.4,
                (dataframe["adx"] < self.adx_threshold) & (dataframe["atr_ratio"] < 0.9),
            ],
            [2, 0],
            default=1,
        ).astype(int)
        dataframe["adapt_mult"] = np.where(
            dataframe["regime"] == 2,
            self.base_multiplier * (1.0 + (dataframe["atr_ratio"] - 1.0).clip(lower=0.0) * 0.4),
            np.where(dataframe["regime"] == 0, self.base_multiplier * 0.85, self.base_multiplier),
        )
        dataframe["adapt_mult"] = dataframe["adapt_mult"].clip(lower=self.base_multiplier * 0.5, upper=self.base_multiplier * 2.0)
        dataframe["upper_base"] = dataframe["hl2"] + dataframe["adapt_mult"] * dataframe["atr"]
        dataframe["lower_base"] = dataframe["hl2"] - dataframe["adapt_mult"] * dataframe["atr"]

        st_band: list[float] = []
        st_dir: list[int] = []
        prev_dir = 1
        prev_band = np.nan
        for row in dataframe.itertuples():
            upper_base = float(row.upper_base) if pd.notna(row.upper_base) else float(row.hl2)
            lower_base = float(row.lower_base) if pd.notna(row.lower_base) else float(row.hl2)
            band_seed = prev_band if pd.notna(prev_band) else (lower_base if prev_dir == 1 else upper_base)
            next_dir = prev_dir
            if prev_dir == 1:
                next_band = max(lower_base, band_seed)
                if float(row.close) < next_band:
                    next_dir = -1
                    next_band = upper_base
            else:
                next_band = min(upper_base, band_seed)
                if float(row.close) > next_band:
                    next_dir = 1
                    next_band = lower_base
            st_band.append(float(next_band))
            st_dir.append(int(next_dir))
            prev_band = next_band
            prev_dir = next_dir

        dataframe["st_band"] = st_band
        dataframe["st_dir"] = st_dir
        dataframe["trend_flip_up"] = (dataframe["st_dir"] == 1) & (dataframe["st_dir"].shift(1) == -1)
        dataframe["trend_flip_down"] = (dataframe["st_dir"] == -1) & (dataframe["st_dir"].shift(1) == 1)
        dataframe["trend_ema"] = ta.EMA(dataframe, timeperiod=self.trend_ema_length)
        dataframe["trend_up"] = dataframe["close"] > dataframe["trend_ema"]
        dataframe["trend_down"] = dataframe["close"] < dataframe["trend_ema"]
        dataframe["volume_ma"] = ta.SMA(dataframe["volume"], timeperiod=self.volume_ma_length)
        dataframe["volume_ratio"] = np.where(dataframe["volume_ma"] > 0, dataframe["volume"] / dataframe["volume_ma"], 1.0)
        dataframe["prev_band_distance"] = (dataframe["close"].shift(1) - dataframe["st_band"].shift(1)).abs() / dataframe["atr_safe"]
        dataframe["ema_distance_atr"] = (dataframe["close"] - dataframe["trend_ema"]).abs() / dataframe["atr_safe"]
        dataframe["long_disp_atr"] = (dataframe["close"] - dataframe["st_band"]) / dataframe["atr_safe"]
        dataframe["short_disp_atr"] = (dataframe["st_band"] - dataframe["close"]) / dataframe["atr_safe"]

        volume_score = np.select(
            [
                dataframe["volume_ratio"] >= 2.5,
                dataframe["volume_ratio"] >= 1.5,
                dataframe["volume_ratio"] >= 1.0,
            ],
            [20, 14, 8],
            default=3,
        )
        regime_score = np.select(
            [dataframe["regime"] == 1, dataframe["regime"] == 2],
            [15, 8],
            default=3,
        )
        band_distance_score = np.select(
            [
                dataframe["prev_band_distance"] >= 2.0,
                dataframe["prev_band_distance"] >= 1.0,
                dataframe["prev_band_distance"] >= 0.5,
            ],
            [20, 14, 8],
            default=3,
        )
        long_disp_score = np.select(
            [
                dataframe["long_disp_atr"] >= 1.5,
                dataframe["long_disp_atr"] >= 0.8,
                dataframe["long_disp_atr"] >= 0.3,
                dataframe["long_disp_atr"] > 0,
            ],
            [25, 18, 12, 5],
            default=0,
        )
        short_disp_score = np.select(
            [
                dataframe["short_disp_atr"] >= 1.5,
                dataframe["short_disp_atr"] >= 0.8,
                dataframe["short_disp_atr"] >= 0.3,
                dataframe["short_disp_atr"] > 0,
            ],
            [25, 18, 12, 5],
            default=0,
        )
        long_align_score = np.select(
            [
                dataframe["trend_up"] & (dataframe["ema_distance_atr"] > 0.5),
                dataframe["trend_up"],
                dataframe["ema_distance_atr"] < 0.3,
            ],
            [20, 14, 8],
            default=2,
        )
        short_align_score = np.select(
            [
                dataframe["trend_down"] & (dataframe["ema_distance_atr"] > 0.5),
                dataframe["trend_down"],
                dataframe["ema_distance_atr"] < 0.3,
            ],
            [20, 14, 8],
            default=2,
        )
        dataframe["long_score"] = np.rint(volume_score + long_disp_score + long_align_score + regime_score + band_distance_score).clip(0, 100)
        dataframe["short_score"] = np.rint(volume_score + short_disp_score + short_align_score + regime_score + band_distance_score).clip(0, 100)
        dataframe["long_candidate"] = (
            dataframe["trend_flip_up"]
            & (dataframe["long_score"] >= self.min_signal_score)
            & dataframe["trend_up"]
            & (dataframe["regime"] != 0)
            & (dataframe["volume"] > dataframe["volume_ma"].fillna(np.inf))
        )
        dataframe["short_candidate"] = (
            dataframe["trend_flip_down"]
            & (dataframe["short_score"] >= self.min_signal_score)
            & dataframe["trend_down"]
            & (dataframe["regime"] != 0)
            & (dataframe["volume"] > dataframe["volume_ma"].fillna(np.inf))
        )

        enter_long = np.zeros(len(dataframe), dtype=int)
        enter_short = np.zeros(len(dataframe), dtype=int)
        last_entry_index = -9999
        for index, row in enumerate(dataframe.itertuples()):
            if index - last_entry_index <= self.cooldown_bars:
                continue
            if bool(row.long_candidate):
                enter_long[index] = 1
                last_entry_index = index
                continue
            if bool(row.short_candidate):
                enter_short[index] = 1
                last_entry_index = index

        dataframe["signal_enter_long"] = enter_long
        dataframe["signal_enter_short"] = enter_short
        dataframe["signal_long_tag"] = [
            f"long_s{{int(score)}}" if flag else None
            for flag, score in zip(enter_long, dataframe["long_score"], strict=False)
        ]
        dataframe["signal_short_tag"] = [
            f"short_s{{int(score)}}" if flag else None
            for flag, score in zip(enter_short, dataframe["short_score"], strict=False)
        ]
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = dataframe["signal_enter_long"].fillna(0).astype(int)
        dataframe["enter_short"] = dataframe["signal_enter_short"].fillna(0).astype(int)
        dataframe["enter_tag"] = dataframe["signal_long_tag"]
        dataframe["enter_short_tag"] = dataframe["signal_short_tag"]
        dataframe.loc[dataframe["enter_short"] > 0, "enter_tag"] = dataframe.loc[dataframe["enter_short"] > 0, "signal_short_tag"]
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        dataframe["exit_short"] = 0
        dataframe["exit_tag"] = None
        dataframe["exit_short_tag"] = None
        return dataframe

    def _resolve_exit_plan(self, pair, trade, dataframe: DataFrame | None = None):
        cached_plan = trade.get_custom_data("pulse_exit_plan")
        if cached_plan:
            return cached_plan
        if dataframe is None:
            dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or dataframe.empty:
            return None
        entry_frame = dataframe.loc[dataframe["date"] <= pd.Timestamp(trade.open_date_utc)]
        if entry_frame.empty:
            return None
        entry_candle = entry_frame.iloc[-1]
        atr_raw = entry_candle.get("atr")
        atr_value = float(atr_raw) if pd.notna(atr_raw) else 0.0
        entry_price = float(trade.open_rate)
        stop_distance = max(atr_value * self.stoploss_atr_multiplier, entry_price * 0.0005)
        target_distance = stop_distance * self.takeprofit_rr
        if trade.is_short:
            resolved_plan = {{"stop": entry_price + stop_distance, "target": entry_price - target_distance}}
        else:
            resolved_plan = {{"stop": entry_price - stop_distance, "target": entry_price + target_distance}}
        if getattr(trade, "id", None) is not None:
            trade.set_custom_data("pulse_exit_plan", resolved_plan)
        return resolved_plan
{render_threshold_custom_exit(
    plan_var_name="exit_plan",
    resolve_plan_expression="self._resolve_exit_plan(pair, trade, dataframe)",
    stop_reason="atr_stop",
    target_reason="rr_target",
)}"""


def _base_signal_frame(candles: list[list[float]]) -> pd.DataFrame:
    if not candles:
        return pd.DataFrame(columns=["timestamp", "date", "open", "high", "low", "close", "volume"])
    frame = pd.DataFrame(candles, columns=["timestamp", "open", "high", "low", "close", "volume"])
    frame["date"] = pd.to_datetime(frame["timestamp"], unit="ms", utc=True)
    return frame.sort_values("date").reset_index(drop=True)


def _build_btc_regime_pulse_supertrend_frame(candles: list[list[float]], _timeframe: str) -> pd.DataFrame:
    frame = _base_signal_frame(candles)
    if frame.empty:
        return frame

    atr_length = 10
    base_multiplier = 3.0
    regime_lookback = 40
    adx_length = 14
    adx_threshold = 20
    trend_ema_length = 50
    volume_ma_length = 20
    min_signal_score = 65
    cooldown_bars = 5

    frame["hl2"] = (frame["high"] + frame["low"]) / 2.0
    frame["atr"] = ta.ATR(frame, timeperiod=atr_length)
    frame["atr_safe"] = frame["atr"].fillna(0.001).clip(lower=0.001)
    frame["atr_ma"] = frame["atr"].rolling(regime_lookback).mean()
    frame["atr_ratio"] = np.where(frame["atr_ma"] > 0, frame["atr"] / frame["atr_ma"], 1.0)
    frame["adx"] = ta.ADX(frame, timeperiod=adx_length)
    frame["regime"] = np.select(
        [
            frame["atr_ratio"] > 1.4,
            (frame["adx"] < adx_threshold) & (frame["atr_ratio"] < 0.9),
        ],
        [2, 0],
        default=1,
    ).astype(int)
    frame["adapt_mult"] = np.where(
        frame["regime"] == 2,
        base_multiplier * (1.0 + (frame["atr_ratio"] - 1.0).clip(lower=0.0) * 0.4),
        np.where(frame["regime"] == 0, base_multiplier * 0.85, base_multiplier),
    )
    frame["adapt_mult"] = frame["adapt_mult"].clip(lower=base_multiplier * 0.5, upper=base_multiplier * 2.0)
    frame["upper_base"] = frame["hl2"] + frame["adapt_mult"] * frame["atr"]
    frame["lower_base"] = frame["hl2"] - frame["adapt_mult"] * frame["atr"]

    st_band: list[float] = []
    st_dir: list[int] = []
    prev_dir = 1
    prev_band = np.nan
    for row in frame.itertuples():
        upper_base = float(row.upper_base) if pd.notna(row.upper_base) else float(row.hl2)
        lower_base = float(row.lower_base) if pd.notna(row.lower_base) else float(row.hl2)
        band_seed = prev_band if pd.notna(prev_band) else (lower_base if prev_dir == 1 else upper_base)
        next_dir = prev_dir
        if prev_dir == 1:
            next_band = max(lower_base, band_seed)
            if float(row.close) < next_band:
                next_dir = -1
                next_band = upper_base
        else:
            next_band = min(upper_base, band_seed)
            if float(row.close) > next_band:
                next_dir = 1
                next_band = lower_base
        st_band.append(float(next_band))
        st_dir.append(int(next_dir))
        prev_band = next_band
        prev_dir = next_dir

    frame["st_band"] = st_band
    frame["st_dir"] = st_dir
    frame["trend_flip_up"] = (frame["st_dir"] == 1) & (frame["st_dir"].shift(1) == -1)
    frame["trend_flip_down"] = (frame["st_dir"] == -1) & (frame["st_dir"].shift(1) == 1)
    frame["trend_ema"] = ta.EMA(frame, timeperiod=trend_ema_length)
    frame["trend_up"] = frame["close"] > frame["trend_ema"]
    frame["trend_down"] = frame["close"] < frame["trend_ema"]
    frame["volume_ma"] = ta.SMA(frame["volume"], timeperiod=volume_ma_length)
    frame["volume_ratio"] = np.where(frame["volume_ma"] > 0, frame["volume"] / frame["volume_ma"], 1.0)
    frame["prev_band_distance"] = (frame["close"].shift(1) - frame["st_band"].shift(1)).abs() / frame["atr_safe"]
    frame["ema_distance_atr"] = (frame["close"] - frame["trend_ema"]).abs() / frame["atr_safe"]
    frame["long_disp_atr"] = (frame["close"] - frame["st_band"]) / frame["atr_safe"]
    frame["short_disp_atr"] = (frame["st_band"] - frame["close"]) / frame["atr_safe"]

    volume_score = np.select(
        [frame["volume_ratio"] >= 2.5, frame["volume_ratio"] >= 1.5, frame["volume_ratio"] >= 1.0],
        [20, 14, 8],
        default=3,
    )
    regime_score = np.select([frame["regime"] == 1, frame["regime"] == 2], [15, 8], default=3)
    band_distance_score = np.select(
        [frame["prev_band_distance"] >= 2.0, frame["prev_band_distance"] >= 1.0, frame["prev_band_distance"] >= 0.5],
        [20, 14, 8],
        default=3,
    )
    long_disp_score = np.select(
        [frame["long_disp_atr"] >= 1.5, frame["long_disp_atr"] >= 0.8, frame["long_disp_atr"] >= 0.3, frame["long_disp_atr"] > 0],
        [25, 18, 12, 5],
        default=0,
    )
    short_disp_score = np.select(
        [frame["short_disp_atr"] >= 1.5, frame["short_disp_atr"] >= 0.8, frame["short_disp_atr"] >= 0.3, frame["short_disp_atr"] > 0],
        [25, 18, 12, 5],
        default=0,
    )
    long_align_score = np.select(
        [frame["trend_up"] & (frame["ema_distance_atr"] > 0.5), frame["trend_up"], frame["ema_distance_atr"] < 0.3],
        [20, 14, 8],
        default=2,
    )
    short_align_score = np.select(
        [frame["trend_down"] & (frame["ema_distance_atr"] > 0.5), frame["trend_down"], frame["ema_distance_atr"] < 0.3],
        [20, 14, 8],
        default=2,
    )
    frame["long_score"] = np.rint(volume_score + long_disp_score + long_align_score + regime_score + band_distance_score).clip(0, 100)
    frame["short_score"] = np.rint(volume_score + short_disp_score + short_align_score + regime_score + band_distance_score).clip(0, 100)
    frame["long_candidate"] = (
        frame["trend_flip_up"]
        & (frame["long_score"] >= min_signal_score)
        & frame["trend_up"]
        & (frame["regime"] != 0)
        & (frame["volume"] > frame["volume_ma"].fillna(np.inf))
    )
    frame["short_candidate"] = (
        frame["trend_flip_down"]
        & (frame["short_score"] >= min_signal_score)
        & frame["trend_down"]
        & (frame["regime"] != 0)
        & (frame["volume"] > frame["volume_ma"].fillna(np.inf))
    )

    enter_long = np.zeros(len(frame), dtype=int)
    enter_short = np.zeros(len(frame), dtype=int)
    last_entry_index = -9999
    for index, row in enumerate(frame.itertuples()):
        if index - last_entry_index <= cooldown_bars:
            continue
        if bool(row.long_candidate):
            enter_long[index] = 1
            last_entry_index = index
            continue
        if bool(row.short_candidate):
            enter_short[index] = 1
            last_entry_index = index

    frame["active_regime"] = np.select(
        [frame["regime"] == 0, frame["regime"] == 2],
        ["range", "volatile_trend"],
        default="trend",
    )
    frame["long_entry_signal"] = pd.Series(enter_long, index=frame.index).astype(bool)
    frame["long_exit_signal"] = pd.Series(False, index=frame.index, dtype=bool)
    frame["short_entry_signal"] = pd.Series(enter_short, index=frame.index).astype(bool)
    frame["short_exit_signal"] = pd.Series(False, index=frame.index, dtype=bool)
    return frame
