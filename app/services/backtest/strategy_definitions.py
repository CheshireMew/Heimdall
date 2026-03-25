from __future__ import annotations

from typing import Any

from app.services.backtest.strategy_contract import build_condition, build_group


BUILTIN_INDICATOR_ENGINES: dict[str, dict[str, Any]] = {
    "ema": {
        "engine": "ema",
        "name": "EMA",
        "description": "指数移动平均线",
        "outputs": [{"key": "value", "label": "EMA"}],
        "params": [
            {"key": "period", "label": "周期", "type": "int", "default": 20, "min": 5, "max": 200, "step": 1},
        ],
    },
    "sma": {
        "engine": "sma",
        "name": "SMA",
        "description": "简单移动平均线",
        "outputs": [{"key": "value", "label": "SMA"}],
        "params": [
            {"key": "period", "label": "周期", "type": "int", "default": 20, "min": 5, "max": 200, "step": 1},
        ],
    },
    "rsi": {
        "engine": "rsi",
        "name": "RSI",
        "description": "相对强弱指标",
        "outputs": [{"key": "value", "label": "RSI"}],
        "params": [
            {"key": "period", "label": "周期", "type": "int", "default": 14, "min": 5, "max": 50, "step": 1},
        ],
    },
    "macd": {
        "engine": "macd",
        "name": "MACD",
        "description": "MACD 动量指标",
        "outputs": [
            {"key": "macd", "label": "MACD"},
            {"key": "signal", "label": "Signal"},
            {"key": "hist", "label": "Hist"},
        ],
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
        "outputs": [
            {"key": "upper", "label": "上轨"},
            {"key": "middle", "label": "中轨"},
            {"key": "lower", "label": "下轨"},
        ],
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
        "params": [
            {"key": "period", "label": "周期", "type": "int", "default": 20, "min": 5, "max": 120, "step": 1},
        ],
    },
    "atr": {
        "engine": "atr",
        "name": "ATR",
        "description": "平均真实波幅",
        "outputs": [{"key": "value", "label": "ATR"}],
        "params": [
            {"key": "period", "label": "周期", "type": "int", "default": 14, "min": 5, "max": 100, "step": 1},
        ],
    },
    "rolling_high": {
        "engine": "rolling_high",
        "name": "Rolling High",
        "description": "滚动最高价",
        "outputs": [{"key": "value", "label": "突破高点"}],
        "params": [
            {"key": "lookback", "label": "回看周期", "type": "int", "default": 20, "min": 5, "max": 120, "step": 1},
        ],
    },
    "rolling_low": {
        "engine": "rolling_low",
        "name": "Rolling Low",
        "description": "滚动最低价",
        "outputs": [{"key": "value", "label": "支撑低点"}],
        "params": [
            {"key": "lookback", "label": "回看周期", "type": "int", "default": 20, "min": 5, "max": 120, "step": 1},
        ],
    },
    "roc": {
        "engine": "roc",
        "name": "ROC",
        "description": "价格变化率",
        "outputs": [{"key": "value", "label": "ROC"}],
        "params": [
            {"key": "period", "label": "周期", "type": "int", "default": 12, "min": 2, "max": 120, "step": 1},
        ],
    },
}


BUILTIN_TEMPLATE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "ema_rsi_macd": {
        "template": "ema_rsi_macd",
        "name": "EMA RSI MACD",
        "category": "trend",
        "description": "经典趋势跟随模板，结合 EMA 趋势、RSI 过滤和 MACD 动量确认。",
        "indicator_keys": ["ema", "sma", "rsi", "macd", "atr", "roc"],
        "config": {
            "indicators": {
                "ema": {"label": "EMA", "type": "ema", "params": {"period": 20}},
                "rsi": {"label": "RSI", "type": "rsi", "params": {"period": 14}},
                "macd": {"label": "MACD", "type": "macd", "params": {"fast": 12, "slow": 26, "signal": 9}},
            },
            "entry": build_group(
                "entry_root",
                "入场条件组",
                "and",
                [
                    build_condition("price_above_ema", "收盘价站上 EMA", {"kind": "price", "field": "close"}, "gt", {"kind": "indicator", "indicator": "ema", "output": "value"}),
                    build_condition("entry_rsi_max", "RSI 低于入场阈值", {"kind": "indicator", "indicator": "rsi", "output": "value"}, "lt", {"kind": "value", "value": 68}),
                    build_condition("macd_confirmation", "MACD 高于信号线", {"kind": "indicator", "indicator": "macd", "output": "macd"}, "gt", {"kind": "indicator", "indicator": "macd", "output": "signal"}),
                ],
            ),
            "exit": build_group(
                "exit_root",
                "离场条件组",
                "or",
                [
                    build_condition("price_below_ema", "收盘价跌破 EMA", {"kind": "price", "field": "close"}, "lt", {"kind": "indicator", "indicator": "ema", "output": "value"}),
                    build_condition("exit_rsi_min", "RSI 高于离场阈值", {"kind": "indicator", "indicator": "rsi", "output": "value"}, "gt", {"kind": "value", "value": 32}),
                ],
            ),
            "risk": {
                "stoploss": -0.12,
                "roi_targets": [
                    {"id": "roi_0", "minutes": 0, "profit": 0.09, "enabled": True},
                    {"id": "roi_1", "minutes": 180, "profit": 0.04, "enabled": True},
                ],
                "trailing": {"enabled": True, "positive": 0.02, "offset": 0.04, "only_offset_reached": True},
                "partial_exits": [
                    {"id": "partial_1", "profit": 0.05, "size_pct": 35, "enabled": True},
                    {"id": "partial_2", "profit": 0.09, "size_pct": 25, "enabled": True},
                ],
            },
        },
        "parameter_space": {
            "indicators.ema.params.period": [10, 20, 30, 50],
            "entry.entry_rsi_max.right.value": [60, 65, 68, 72],
            "exit.exit_rsi_min.right.value": [28, 32, 35, 40],
            "risk.trailing.positive": [0.015, 0.02, 0.03],
        },
        "builtin": {"key": "ema_rsi_macd", "version_name": "Base v1", "notes": "默认趋势跟随版本"},
    },
    "bbands_mean_reversion": {
        "template": "bbands_mean_reversion",
        "name": "Bollinger Mean Reversion",
        "category": "mean_reversion",
        "description": "布林带均值回归模板，用 RSI 过滤超卖与回归离场。",
        "indicator_keys": ["bbands", "rsi", "atr", "roc", "rolling_low"],
        "config": {
            "indicators": {
                "bbands": {"label": "BBands", "type": "bbands", "params": {"period": 20, "stddev": 2.0}},
                "rsi": {"label": "RSI", "type": "rsi", "params": {"period": 14}},
            },
            "entry": build_group(
                "entry_root",
                "入场条件组",
                "and",
                [
                    build_condition("price_below_lower_band", "收盘价跌破布林下轨", {"kind": "price", "field": "close"}, "lt", {"kind": "indicator", "indicator": "bbands", "output": "lower"}),
                    build_condition("entry_rsi_max", "RSI 低于入场阈值", {"kind": "indicator", "indicator": "rsi", "output": "value"}, "lt", {"kind": "value", "value": 35}),
                ],
            ),
            "exit": build_group(
                "exit_root",
                "离场条件组",
                "or",
                [
                    build_condition("price_above_middle_band", "收盘价回到布林中轨上方", {"kind": "price", "field": "close"}, "gt", {"kind": "indicator", "indicator": "bbands", "output": "middle"}),
                    build_condition("exit_rsi_min", "RSI 高于离场阈值", {"kind": "indicator", "indicator": "rsi", "output": "value"}, "gt", {"kind": "value", "value": 60}),
                ],
            ),
            "risk": {
                "stoploss": -0.08,
                "roi_targets": [
                    {"id": "roi_0", "minutes": 0, "profit": 0.06, "enabled": True},
                    {"id": "roi_1", "minutes": 120, "profit": 0.03, "enabled": True},
                ],
                "trailing": {"enabled": False, "positive": 0.02, "offset": 0.03, "only_offset_reached": True},
                "partial_exits": [],
            },
        },
        "parameter_space": {
            "indicators.bbands.params.period": [14, 20, 26],
            "indicators.bbands.params.stddev": [1.8, 2.0, 2.2],
            "entry.entry_rsi_max.right.value": [28, 32, 35, 40],
        },
        "builtin": {"key": "bbands_mean_reversion", "version_name": "Base v1", "notes": "震荡市值回归版本"},
    },
    "breakout_volume": {
        "template": "breakout_volume",
        "name": "Breakout Volume",
        "category": "breakout",
        "description": "通道突破模板，结合成交量放大和 ATR 跟踪止损。",
        "indicator_keys": ["rolling_high", "rolling_low", "volume_sma", "atr", "roc", "ema"],
        "config": {
            "indicators": {
                "breakout_high": {"label": "Breakout High", "type": "rolling_high", "params": {"lookback": 20}},
                "volume_sma": {"label": "Volume SMA", "type": "volume_sma", "params": {"period": 20}},
                "atr": {"label": "ATR", "type": "atr", "params": {"period": 14}},
            },
            "entry": build_group(
                "entry_root",
                "入场条件组",
                "and",
                [
                    build_condition("price_above_breakout_high", "收盘价突破高点", {"kind": "price", "field": "close"}, "gt", {"kind": "indicator", "indicator": "breakout_high", "output": "value"}),
                    build_condition("volume_above_multiplier", "成交量大于量均线乘数", {"kind": "price", "field": "volume"}, "gt", {"kind": "indicator_multiplier", "indicator": "volume_sma", "output": "value", "multiplier": 1.5}),
                ],
            ),
            "exit": build_group(
                "exit_root",
                "离场条件组",
                "or",
                [
                    build_condition("price_below_atr_stop", "收盘价跌破 ATR 止损", {"kind": "price", "field": "close"}, "lt", {"kind": "indicator_offset", "base_indicator": "breakout_high", "base_output": "value", "offset_indicator": "atr", "offset_output": "value", "offset_multiplier": 2.5}),
                ],
            ),
            "risk": {
                "stoploss": -0.10,
                "roi_targets": [
                    {"id": "roi_0", "minutes": 0, "profit": 0.12, "enabled": True},
                    {"id": "roi_1", "minutes": 240, "profit": 0.05, "enabled": True},
                ],
                "trailing": {"enabled": True, "positive": 0.03, "offset": 0.05, "only_offset_reached": True},
                "partial_exits": [
                    {"id": "partial_1", "profit": 0.08, "size_pct": 30, "enabled": True},
                ],
            },
        },
        "parameter_space": {
            "indicators.breakout_high.params.lookback": [10, 20, 30],
            "entry.volume_above_multiplier.right.multiplier": [1.2, 1.5, 1.8, 2.0],
            "exit.price_below_atr_stop.right.offset_multiplier": [1.5, 2.0, 2.5, 3.0],
            "risk.trailing.offset": [0.04, 0.05, 0.06],
        },
        "builtin": {"key": "breakout_volume", "version_name": "Base v1", "notes": "突破追踪版本"},
    },
}
