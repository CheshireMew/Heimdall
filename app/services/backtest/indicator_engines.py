from __future__ import annotations

from copy import deepcopy
from typing import Any

import pandas as pd
import talib.abstract as ta


BUILTIN_INDICATOR_ENGINES: dict[str, dict[str, Any]] = {
    "ema": {
        "engine": "ema",
        "name": "EMA",
        "description": "指数移动平均线",
        "outputs": [{"key": "value", "label": "EMA"}],
        "params": [{"key": "period", "label": "周期", "type": "int", "default": 20, "min": 5, "max": 200, "step": 1}],
    },
    "sma": {
        "engine": "sma",
        "name": "SMA",
        "description": "简单移动平均线",
        "outputs": [{"key": "value", "label": "SMA"}],
        "params": [{"key": "period", "label": "周期", "type": "int", "default": 20, "min": 5, "max": 200, "step": 1}],
    },
    "rsi": {
        "engine": "rsi",
        "name": "RSI",
        "description": "相对强弱指标",
        "outputs": [{"key": "value", "label": "RSI"}],
        "params": [{"key": "period", "label": "周期", "type": "int", "default": 14, "min": 5, "max": 50, "step": 1}],
    },
    "macd": {
        "engine": "macd",
        "name": "MACD",
        "description": "MACD 动量指标",
        "outputs": [{"key": "macd", "label": "MACD"}, {"key": "signal", "label": "Signal"}, {"key": "hist", "label": "Hist"}],
        "params": [
            {"key": "fast", "label": "快线", "type": "int", "default": 12, "min": 2, "max": 50, "step": 1},
            {"key": "slow", "label": "慢线", "type": "int", "default": 26, "min": 5, "max": 100, "step": 1},
            {"key": "signal", "label": "信号线", "type": "int", "default": 9, "min": 2, "max": 50, "step": 1},
        ],
    },
    "bbands": {
        "engine": "bbands",
        "name": "Bollinger Bands",
        "description": "布林带",
        "outputs": [{"key": "upper", "label": "上轨"}, {"key": "middle", "label": "中轨"}, {"key": "lower", "label": "下轨"}],
        "params": [
            {"key": "period", "label": "周期", "type": "int", "default": 20, "min": 5, "max": 100, "step": 1},
            {"key": "stddev", "label": "标准差", "type": "float", "default": 2.0, "min": 0.5, "max": 4.0, "step": 0.1},
        ],
    },
    "volume_sma": {
        "engine": "volume_sma",
        "name": "Volume SMA",
        "description": "成交量均线",
        "outputs": [{"key": "value", "label": "量均线"}],
        "params": [{"key": "period", "label": "周期", "type": "int", "default": 20, "min": 5, "max": 120, "step": 1}],
    },
    "atr": {
        "engine": "atr",
        "name": "ATR",
        "description": "平均真实波幅",
        "outputs": [{"key": "value", "label": "ATR"}],
        "params": [{"key": "period", "label": "周期", "type": "int", "default": 14, "min": 5, "max": 100, "step": 1}],
    },
    "rolling_high": {
        "engine": "rolling_high",
        "name": "Rolling High",
        "description": "滚动最高价",
        "outputs": [{"key": "value", "label": "突破高点"}],
        "params": [{"key": "lookback", "label": "回看周期", "type": "int", "default": 20, "min": 5, "max": 120, "step": 1}],
    },
    "rolling_low": {
        "engine": "rolling_low",
        "name": "Rolling Low",
        "description": "滚动最低价",
        "outputs": [{"key": "value", "label": "支撑低点"}],
        "params": [{"key": "lookback", "label": "回看周期", "type": "int", "default": 20, "min": 5, "max": 120, "step": 1}],
    },
    "roc": {
        "engine": "roc",
        "name": "ROC",
        "description": "价格变化率",
        "outputs": [{"key": "value", "label": "ROC"}],
        "params": [{"key": "period", "label": "周期", "type": "int", "default": 12, "min": 2, "max": 120, "step": 1}],
    },
    "displacement_atr": {
        "engine": "displacement_atr",
        "name": "Displacement / ATR",
        "description": "用 ATR 归一化后的净位移，适合做趋势状态强度 M。",
        "outputs": [{"key": "value", "label": "M"}],
        "params": [
            {"key": "lookback", "label": "位移窗口", "type": "int", "default": 24, "min": 4, "max": 240, "step": 1},
            {"key": "atr_period", "label": "ATR 周期", "type": "int", "default": 14, "min": 5, "max": 100, "step": 1},
        ],
    },
    "efficiency_ratio": {
        "engine": "efficiency_ratio",
        "name": "Efficiency Ratio",
        "description": "净位移除以滚动路径长度，适合做趋势效率 E。",
        "outputs": [{"key": "value", "label": "E"}],
        "params": [{"key": "lookback", "label": "效率窗口", "type": "int", "default": 24, "min": 4, "max": 240, "step": 1}],
    },
    "range_context": {
        "engine": "range_context",
        "name": "Range Context",
        "description": "输出区间上下沿、中轴、位置百分比和区间宽度，适合做 P 和宽度过滤。",
        "outputs": [
            {"key": "upper", "label": "区间上沿"},
            {"key": "lower", "label": "区间下沿"},
            {"key": "middle", "label": "区间中轴"},
            {"key": "position", "label": "P"},
            {"key": "width_ratio", "label": "宽度 / ATR"},
        ],
        "params": [
            {"key": "lookback", "label": "区间窗口", "type": "int", "default": 32, "min": 8, "max": 240, "step": 1},
            {"key": "atr_period", "label": "ATR 周期", "type": "int", "default": 14, "min": 5, "max": 100, "step": 1},
        ],
    },
}


def indicator_engine_catalog() -> dict[str, dict[str, Any]]:
    return deepcopy(BUILTIN_INDICATOR_ENGINES)


def resolve_indicator_engine(indicator_type: str, indicator_spec: dict[str, Any]) -> str:
    return str(indicator_spec.get("engine") or indicator_type)


def indicator_warmup_bars(engine: str, params: dict[str, Any]) -> int:
    if engine in {"ema", "sma", "roc", "volume_sma"}:
        return int(params.get("period", 20 if engine != "roc" else 12))
    if engine == "rsi":
        return int(params.get("period", 14))
    if engine == "macd":
        return int(params.get("slow", 26)) + int(params.get("signal", 9))
    if engine == "bbands":
        return int(params.get("period", 20))
    if engine == "atr":
        return int(params.get("period", 14))
    if engine in {"rolling_high", "rolling_low"}:
        return int(params.get("lookback", 20))
    if engine == "displacement_atr":
        return max(int(params.get("lookback", 24)), int(params.get("atr_period", 14)))
    if engine == "efficiency_ratio":
        return int(params.get("lookback", 24)) + 1
    if engine == "range_context":
        return max(int(params.get("lookback", 32)), int(params.get("atr_period", 14)))
    raise ValueError(f"不支持的指标引擎: {engine}")


def indicator_output_columns(indicator_id: str, indicator_spec: dict[str, Any]) -> list[str]:
    outputs = indicator_spec.get("outputs") or [{"key": "value"}]
    return [f'{indicator_id}__{output.get("key", "value")}' for output in outputs]


def apply_indicator_frame(frame: pd.DataFrame, indicator_id: str, engine: str, params: dict[str, Any]) -> None:
    if engine == "ema":
        frame[f"{indicator_id}__value"] = ta.EMA(frame, timeperiod=int(params.get("period", 20)))
    elif engine == "sma":
        frame[f"{indicator_id}__value"] = ta.SMA(frame, timeperiod=int(params.get("period", 20)))
    elif engine == "rsi":
        frame[f"{indicator_id}__value"] = ta.RSI(frame, timeperiod=int(params.get("period", 14)))
    elif engine == "macd":
        result = ta.MACD(frame, fastperiod=int(params.get("fast", 12)), slowperiod=int(params.get("slow", 26)), signalperiod=int(params.get("signal", 9)))
        frame[f"{indicator_id}__macd"] = result["macd"]
        frame[f"{indicator_id}__signal"] = result["macdsignal"]
        frame[f"{indicator_id}__hist"] = result["macdhist"]
    elif engine == "bbands":
        upper, middle, lower = ta.BBANDS(frame["close"], timeperiod=int(params.get("period", 20)), nbdevup=float(params.get("stddev", 2.0)), nbdevdn=float(params.get("stddev", 2.0)), matype=0)
        frame[f"{indicator_id}__upper"] = upper
        frame[f"{indicator_id}__middle"] = middle
        frame[f"{indicator_id}__lower"] = lower
    elif engine == "volume_sma":
        frame[f"{indicator_id}__value"] = ta.SMA(frame["volume"], timeperiod=int(params.get("period", 20)))
    elif engine == "atr":
        frame[f"{indicator_id}__value"] = ta.ATR(frame, timeperiod=int(params.get("period", 14)))
    elif engine == "rolling_high":
        frame[f"{indicator_id}__value"] = frame["high"].rolling(int(params.get("lookback", 20))).max().shift(1)
    elif engine == "rolling_low":
        frame[f"{indicator_id}__value"] = frame["low"].rolling(int(params.get("lookback", 20))).min().shift(1)
    elif engine == "roc":
        frame[f"{indicator_id}__value"] = ta.ROC(frame, timeperiod=int(params.get("period", 12)))
    elif engine == "displacement_atr":
        lookback = int(params.get("lookback", 24))
        atr = ta.ATR(frame, timeperiod=int(params.get("atr_period", 14)))
        frame[f"{indicator_id}__value"] = (frame["close"] - frame["close"].shift(lookback)) / atr.replace(0.0, pd.NA)
    elif engine == "efficiency_ratio":
        lookback = int(params.get("lookback", 24))
        displacement = (frame["close"] - frame["close"].shift(lookback)).abs()
        path = frame["close"].diff().abs().rolling(lookback).sum()
        frame[f"{indicator_id}__value"] = displacement / path.replace(0.0, pd.NA)
    elif engine == "range_context":
        lookback = int(params.get("lookback", 32))
        upper = frame["high"].rolling(lookback).max().shift(1)
        lower = frame["low"].rolling(lookback).min().shift(1)
        width = upper - lower
        atr = ta.ATR(frame, timeperiod=int(params.get("atr_period", 14)))
        frame[f"{indicator_id}__upper"] = upper
        frame[f"{indicator_id}__lower"] = lower
        frame[f"{indicator_id}__middle"] = (upper + lower) / 2.0
        frame[f"{indicator_id}__position"] = (frame["close"] - lower) / width.replace(0.0, pd.NA)
        frame[f"{indicator_id}__width_ratio"] = width / atr.replace(0.0, pd.NA)
    else:
        raise ValueError(f"不支持的指标引擎: {engine}")


def render_indicator_frame_code(frame_var: str, indicator_id: str, engine: str, params: dict[str, Any]) -> list[str]:
    if engine == "ema":
        return [f'        {frame_var}["{indicator_id}__value"] = ta.EMA({frame_var}, timeperiod={int(params.get("period", 20))})']
    if engine == "sma":
        return [f'        {frame_var}["{indicator_id}__value"] = ta.SMA({frame_var}, timeperiod={int(params.get("period", 20))})']
    if engine == "rsi":
        return [f'        {frame_var}["{indicator_id}__value"] = ta.RSI({frame_var}, timeperiod={int(params.get("period", 14))})']
    if engine == "macd":
        return [
            f'        {indicator_id}_macd = ta.MACD({frame_var}, fastperiod={int(params.get("fast", 12))}, slowperiod={int(params.get("slow", 26))}, signalperiod={int(params.get("signal", 9))})',
            f'        {frame_var}["{indicator_id}__macd"] = {indicator_id}_macd["macd"]',
            f'        {frame_var}["{indicator_id}__signal"] = {indicator_id}_macd["macdsignal"]',
            f'        {frame_var}["{indicator_id}__hist"] = {indicator_id}_macd["macdhist"]',
        ]
    if engine == "bbands":
        return [
            f'        {indicator_id}_upper, {indicator_id}_middle, {indicator_id}_lower = ta.BBANDS({frame_var}["close"], timeperiod={int(params.get("period", 20))}, nbdevup={float(params.get("stddev", 2.0))}, nbdevdn={float(params.get("stddev", 2.0))}, matype=0)',
            f'        {frame_var}["{indicator_id}__upper"] = {indicator_id}_upper',
            f'        {frame_var}["{indicator_id}__middle"] = {indicator_id}_middle',
            f'        {frame_var}["{indicator_id}__lower"] = {indicator_id}_lower',
        ]
    if engine == "volume_sma":
        return [f'        {frame_var}["{indicator_id}__value"] = ta.SMA({frame_var}["volume"], timeperiod={int(params.get("period", 20))})']
    if engine == "atr":
        return [f'        {frame_var}["{indicator_id}__value"] = ta.ATR({frame_var}, timeperiod={int(params.get("period", 14))})']
    if engine == "rolling_high":
        return [f'        {frame_var}["{indicator_id}__value"] = {frame_var}["high"].rolling({int(params.get("lookback", 20))}).max().shift(1)']
    if engine == "rolling_low":
        return [f'        {frame_var}["{indicator_id}__value"] = {frame_var}["low"].rolling({int(params.get("lookback", 20))}).min().shift(1)']
    if engine == "roc":
        return [f'        {frame_var}["{indicator_id}__value"] = ta.ROC({frame_var}, timeperiod={int(params.get("period", 12))})']
    if engine == "displacement_atr":
        lookback = int(params.get("lookback", 24))
        atr_period = int(params.get("atr_period", 14))
        return [
            f'        {indicator_id}_atr = ta.ATR({frame_var}, timeperiod={atr_period})',
            f'        {frame_var}["{indicator_id}__value"] = ({frame_var}["close"] - {frame_var}["close"].shift({lookback})) / {indicator_id}_atr.replace(0.0, pd.NA)',
        ]
    if engine == "efficiency_ratio":
        lookback = int(params.get("lookback", 24))
        return [
            f'        {indicator_id}_displacement = ({frame_var}["close"] - {frame_var}["close"].shift({lookback})).abs()',
            f'        {indicator_id}_path = {frame_var}["close"].diff().abs().rolling({lookback}).sum()',
            f'        {frame_var}["{indicator_id}__value"] = {indicator_id}_displacement / {indicator_id}_path.replace(0.0, pd.NA)',
        ]
    if engine == "range_context":
        lookback = int(params.get("lookback", 32))
        atr_period = int(params.get("atr_period", 14))
        return [
            f'        {frame_var}["{indicator_id}__upper"] = {frame_var}["high"].rolling({lookback}).max().shift(1)',
            f'        {frame_var}["{indicator_id}__lower"] = {frame_var}["low"].rolling({lookback}).min().shift(1)',
            f'        {frame_var}["{indicator_id}__middle"] = ({frame_var}["{indicator_id}__upper"] + {frame_var}["{indicator_id}__lower"]) / 2.0',
            f'        {indicator_id}_width = {frame_var}["{indicator_id}__upper"] - {frame_var}["{indicator_id}__lower"]',
            f'        {indicator_id}_atr = ta.ATR({frame_var}, timeperiod={atr_period})',
            f'        {frame_var}["{indicator_id}__position"] = ({frame_var}["close"] - {frame_var}["{indicator_id}__lower"]) / {indicator_id}_width.replace(0.0, pd.NA)',
            f'        {frame_var}["{indicator_id}__width_ratio"] = {indicator_id}_width / {indicator_id}_atr.replace(0.0, pd.NA)',
        ]
    raise ValueError(f"不支持的指标引擎: {engine}")
