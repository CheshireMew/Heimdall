from __future__ import annotations

from typing import Any

from app.services.backtest.strategy_contract import branch_defaults, build_condition, build_group, execution_defaults


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


BUILTIN_TEMPLATE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "ema_rsi_macd": {
        "template": "ema_rsi_macd",
        "name": "EMA RSI MACD",
        "category": "trend",
        "description": "经典趋势跟随模板，结合 EMA 趋势、RSI 过滤和 MACD 动量确认。",
        "indicator_keys": ["ema", "sma", "rsi", "macd", "atr", "roc"],
        "config": {
            "indicators": {
                "ema": {"label": "EMA", "type": "ema", "timeframe": "base", "params": {"period": 20}},
                "rsi": {"label": "RSI", "type": "rsi", "timeframe": "base", "params": {"period": 14}},
                "macd": {"label": "MACD", "type": "macd", "timeframe": "base", "params": {"fast": 12, "slow": 26, "signal": 9}},
            },
            "execution": execution_defaults(),
            "regime_priority": ["trend", "range"],
            "trend": {
                **branch_defaults("trend", "趋势", enabled=True),
                "long_entry": build_group(
                    "trend_long_entry",
                    "趋势做多入场",
                    "and",
                    [
                        build_condition("price_above_ema", "收盘价站上 EMA", {"kind": "price", "field": "close"}, "gt", {"kind": "indicator", "indicator": "ema", "output": "value"}),
                        build_condition("entry_rsi_max", "RSI 低于入场阈值", {"kind": "indicator", "indicator": "rsi", "output": "value"}, "lt", {"kind": "value", "value": 68}),
                        build_condition("macd_confirmation", "MACD 高于信号线", {"kind": "indicator", "indicator": "macd", "output": "macd"}, "gt", {"kind": "indicator", "indicator": "macd", "output": "signal"}),
                    ],
                ),
                "long_exit": build_group(
                    "trend_long_exit",
                    "趋势做多离场",
                    "or",
                    [
                        build_condition("price_below_ema", "收盘价跌破 EMA", {"kind": "price", "field": "close"}, "lt", {"kind": "indicator", "indicator": "ema", "output": "value"}),
                        build_condition("exit_rsi_min", "RSI 高于离场阈值", {"kind": "indicator", "indicator": "rsi", "output": "value"}, "gt", {"kind": "value", "value": 32}),
                    ],
                ),
            },
            "range": branch_defaults("range", "区间", enabled=False),
            "risk": {
                "stoploss": -0.12,
                "roi_targets": [{"id": "roi_0", "minutes": 0, "profit": 0.09, "enabled": True}, {"id": "roi_1", "minutes": 180, "profit": 0.04, "enabled": True}],
                "trailing": {"enabled": True, "positive": 0.02, "offset": 0.04, "only_offset_reached": True},
                "partial_exits": [{"id": "partial_1", "profit": 0.05, "size_pct": 35, "enabled": True}, {"id": "partial_2", "profit": 0.09, "size_pct": 25, "enabled": True}],
            },
        },
        "parameter_space": {
            "indicators.ema.params.period": [10, 20, 30, 50],
            "trend.long_entry.entry_rsi_max.right.value": [60, 65, 68, 72],
            "trend.long_exit.exit_rsi_min.right.value": [28, 32, 35, 40],
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
                "bbands": {"label": "BBands", "type": "bbands", "timeframe": "base", "params": {"period": 20, "stddev": 2.0}},
                "rsi": {"label": "RSI", "type": "rsi", "timeframe": "base", "params": {"period": 14}},
            },
            "execution": execution_defaults(),
            "regime_priority": ["trend", "range"],
            "trend": branch_defaults("trend", "趋势", enabled=False),
            "range": {
                **branch_defaults("range", "区间", enabled=True),
                "long_entry": build_group(
                    "range_long_entry",
                    "区间做多入场",
                    "and",
                    [
                        build_condition("price_below_lower_band", "收盘价跌破布林下轨", {"kind": "price", "field": "close"}, "lt", {"kind": "indicator", "indicator": "bbands", "output": "lower"}),
                        build_condition("entry_rsi_max", "RSI 低于入场阈值", {"kind": "indicator", "indicator": "rsi", "output": "value"}, "lt", {"kind": "value", "value": 35}),
                    ],
                ),
                "long_exit": build_group(
                    "range_long_exit",
                    "区间做多离场",
                    "or",
                    [
                        build_condition("price_above_middle_band", "收盘价回到布林中轨上方", {"kind": "price", "field": "close"}, "gt", {"kind": "indicator", "indicator": "bbands", "output": "middle"}),
                        build_condition("exit_rsi_min", "RSI 高于离场阈值", {"kind": "indicator", "indicator": "rsi", "output": "value"}, "gt", {"kind": "value", "value": 60}),
                    ],
                ),
            },
            "risk": {
                "stoploss": -0.08,
                "roi_targets": [{"id": "roi_0", "minutes": 0, "profit": 0.06, "enabled": True}, {"id": "roi_1", "minutes": 120, "profit": 0.03, "enabled": True}],
                "trailing": {"enabled": False, "positive": 0.02, "offset": 0.03, "only_offset_reached": True},
                "partial_exits": [],
            },
        },
        "parameter_space": {
            "indicators.bbands.params.period": [14, 20, 26],
            "indicators.bbands.params.stddev": [1.8, 2.0, 2.2],
            "range.long_entry.entry_rsi_max.right.value": [28, 32, 35, 40],
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
                "breakout_high": {"label": "Breakout High", "type": "rolling_high", "timeframe": "base", "params": {"lookback": 20}},
                "volume_sma": {"label": "Volume SMA", "type": "volume_sma", "timeframe": "base", "params": {"period": 20}},
                "atr": {"label": "ATR", "type": "atr", "timeframe": "base", "params": {"period": 14}},
            },
            "execution": execution_defaults(),
            "regime_priority": ["trend", "range"],
            "trend": {
                **branch_defaults("trend", "趋势", enabled=True),
                "long_entry": build_group(
                    "trend_long_entry",
                    "趋势做多入场",
                    "and",
                    [
                        build_condition("price_above_breakout_high", "收盘价突破高点", {"kind": "price", "field": "close"}, "gt", {"kind": "indicator", "indicator": "breakout_high", "output": "value"}),
                        build_condition("volume_above_multiplier", "成交量大于量均线乘数", {"kind": "price", "field": "volume"}, "gt", {"kind": "indicator_multiplier", "indicator": "volume_sma", "output": "value", "multiplier": 1.5}),
                    ],
                ),
                "long_exit": build_group(
                    "trend_long_exit",
                    "趋势做多离场",
                    "or",
                    [
                        build_condition("price_below_atr_stop", "收盘价跌破 ATR 止损", {"kind": "price", "field": "close"}, "lt", {"kind": "indicator_offset", "base_indicator": "breakout_high", "base_output": "value", "offset_indicator": "atr", "offset_output": "value", "offset_multiplier": 2.5}),
                    ],
                ),
            },
            "range": branch_defaults("range", "区间", enabled=False),
            "risk": {
                "stoploss": -0.10,
                "roi_targets": [{"id": "roi_0", "minutes": 0, "profit": 0.12, "enabled": True}, {"id": "roi_1", "minutes": 240, "profit": 0.05, "enabled": True}],
                "trailing": {"enabled": True, "positive": 0.03, "offset": 0.05, "only_offset_reached": True},
                "partial_exits": [{"id": "partial_1", "profit": 0.08, "size_pct": 30, "enabled": True}],
            },
        },
        "parameter_space": {
            "indicators.breakout_high.params.lookback": [10, 20, 30],
            "trend.long_entry.volume_above_multiplier.right.multiplier": [1.2, 1.5, 1.8, 2.0],
            "trend.long_exit.price_below_atr_stop.right.offset_multiplier": [1.5, 2.0, 2.5, 3.0],
            "risk.trailing.offset": [0.04, 0.05, 0.06],
        },
        "builtin": {"key": "breakout_volume", "version_name": "Base v1", "notes": "突破追踪版本"},
    },
    "btc_regime_switch": {
        "template": "btc_regime_switch",
        "name": "BTC Regime Switch",
        "category": "regime",
        "description": "基于 M/E/P 状态源先判趋势或区间，再把 1H 状态、15M 结构和 5M 执行拆开的 BTC 多周期模板。",
        "indicator_keys": ["ema", "rsi", "atr", "displacement_atr", "efficiency_ratio", "range_context"],
        "config": {
            "indicators": {
                "ema_1h": {"label": "1H EMA", "type": "ema", "timeframe": "1h", "params": {"period": 55}},
                "m_1h": {"label": "1H M", "type": "displacement_atr", "timeframe": "1h", "params": {"lookback": 24, "atr_period": 14}},
                "e_1h": {"label": "1H E", "type": "efficiency_ratio", "timeframe": "1h", "params": {"lookback": 24}},
                "range_15m": {"label": "15M Range", "type": "range_context", "timeframe": "15m", "params": {"lookback": 32, "atr_period": 14}},
                "rsi_5m": {"label": "5M RSI", "type": "rsi", "timeframe": "5m", "params": {"period": 14}},
                "atr_5m": {"label": "5M ATR", "type": "atr", "timeframe": "5m", "params": {"period": 14}},
            },
            "execution": {"market_type": "futures", "direction": "long_short"},
            "regime_priority": ["trend", "range"],
            "trend": {
                **branch_defaults("trend", "趋势", enabled=True),
                "regime": build_group(
                    "trend_regime",
                    "趋势状态",
                    "or",
                    [
                        build_group(
                            "trend_regime_up",
                            "上升趋势",
                            "and",
                            [
                                build_condition("trend_up_m", "1H M 高于 2.5", {"kind": "indicator", "indicator": "m_1h", "output": "value"}, "gt", {"kind": "value", "value": 2.5}),
                                build_condition("trend_up_e", "1H E 高于 0.35", {"kind": "indicator", "indicator": "e_1h", "output": "value"}, "gt", {"kind": "value", "value": 0.35}),
                            ],
                        ),
                        build_group(
                            "trend_regime_down",
                            "下降趋势",
                            "and",
                            [
                                build_condition("trend_down_m", "1H M 低于 -2.5", {"kind": "indicator", "indicator": "m_1h", "output": "value"}, "lt", {"kind": "value", "value": -2.5}),
                                build_condition("trend_down_e", "1H E 高于 0.35", {"kind": "indicator", "indicator": "e_1h", "output": "value"}, "gt", {"kind": "value", "value": 0.35}),
                            ],
                        ),
                    ],
                ),
                "long_entry": build_group(
                    "trend_long_entry",
                    "趋势做多入场",
                    "and",
                    [
                        build_condition("trend_long_m_positive", "1H M 仍为正", {"kind": "indicator", "indicator": "m_1h", "output": "value"}, "gt", {"kind": "value", "value": 0.0}),
                        build_condition("trend_long_structure_pullback", "15M P 不高于 0.55", {"kind": "indicator", "indicator": "range_15m", "output": "position"}, "lt", {"kind": "value", "value": 0.55}),
                        build_condition("trend_long_pullback", "收盘价高于 1H EMA 减 0.8ATR", {"kind": "price", "field": "close"}, "gt", {"kind": "indicator_offset", "base_indicator": "ema_1h", "base_output": "value", "offset_indicator": "atr_5m", "offset_output": "value", "offset_multiplier": 0.8}),
                        build_condition("trend_long_rsi", "5M RSI 高于 52", {"kind": "indicator", "indicator": "rsi_5m", "output": "value"}, "gt", {"kind": "value", "value": 52}),
                    ],
                ),
                "long_exit": build_group(
                    "trend_long_exit",
                    "趋势做多离场",
                    "or",
                    [
                        build_condition("trend_long_close_below_ema", "收盘价跌回 1H EMA 下方", {"kind": "price", "field": "close"}, "lt", {"kind": "indicator", "indicator": "ema_1h", "output": "value"}),
                        build_condition("trend_long_m_turn", "1H M 跌回 0 下方", {"kind": "indicator", "indicator": "m_1h", "output": "value"}, "lt", {"kind": "value", "value": 0}),
                    ],
                ),
                "short_entry": build_group(
                    "trend_short_entry",
                    "趋势做空入场",
                    "and",
                    [
                        build_condition("trend_short_m_negative", "1H M 仍为负", {"kind": "indicator", "indicator": "m_1h", "output": "value"}, "lt", {"kind": "value", "value": 0.0}),
                        build_condition("trend_short_structure_pullback", "15M P 不低于 0.45", {"kind": "indicator", "indicator": "range_15m", "output": "position"}, "gt", {"kind": "value", "value": 0.45}),
                        build_condition("trend_short_pullback", "收盘价低于 1H EMA 加 0.8ATR", {"kind": "price", "field": "close"}, "lt", {"kind": "indicator_offset", "base_indicator": "ema_1h", "base_output": "value", "offset_indicator": "atr_5m", "offset_output": "value", "offset_multiplier": -0.8}),
                        build_condition("trend_short_rsi", "5M RSI 低于 48", {"kind": "indicator", "indicator": "rsi_5m", "output": "value"}, "lt", {"kind": "value", "value": 48}),
                    ],
                    enabled=True,
                ),
                "short_exit": build_group(
                    "trend_short_exit",
                    "趋势做空离场",
                    "or",
                    [
                        build_condition("trend_short_close_above_ema", "收盘价站回 1H EMA 上方", {"kind": "price", "field": "close"}, "gt", {"kind": "indicator", "indicator": "ema_1h", "output": "value"}),
                        build_condition("trend_short_m_turn", "1H M 回到 0 上方", {"kind": "indicator", "indicator": "m_1h", "output": "value"}, "gt", {"kind": "value", "value": 0}),
                    ],
                    enabled=True,
                ),
            },
            "range": {
                **branch_defaults("range", "区间", enabled=True),
                "regime": build_group(
                    "range_regime",
                    "区间状态",
                    "and",
                    [
                        build_condition("range_m_ceiling", "1H M 不高于 1.2", {"kind": "indicator", "indicator": "m_1h", "output": "value"}, "lt", {"kind": "value", "value": 1.2}),
                        build_condition("range_m_floor", "1H M 不低于 -1.2", {"kind": "indicator", "indicator": "m_1h", "output": "value"}, "gt", {"kind": "value", "value": -1.2}),
                        build_condition("range_e_cap", "1H E 不高于 0.25", {"kind": "indicator", "indicator": "e_1h", "output": "value"}, "lt", {"kind": "value", "value": 0.25}),
                        build_condition("range_inside_upper", "15M P 不高于 1", {"kind": "indicator", "indicator": "range_15m", "output": "position"}, "lt", {"kind": "value", "value": 1.0}),
                        build_condition("range_inside_lower", "15M P 不低于 0", {"kind": "indicator", "indicator": "range_15m", "output": "position"}, "gt", {"kind": "value", "value": 0.0}),
                        build_condition("range_min_width", "15M 区间宽度至少为 2 倍 ATR", {"kind": "indicator", "indicator": "range_15m", "output": "width_ratio"}, "gt", {"kind": "value", "value": 2.0}),
                    ],
                ),
                "long_entry": build_group(
                    "range_long_entry",
                    "区间假跌破收回后低买",
                    "and",
                    [
                        build_condition("range_long_position", "15M P 不高于 0.15", {"kind": "indicator", "indicator": "range_15m", "output": "position"}, "lt", {"kind": "value", "value": 0.15}),
                        build_condition("range_long_prev_break", "上一根 5M 最低价跌破 15M 下沿", {"kind": "price", "field": "low", "bars_ago": 1}, "lt", {"kind": "indicator", "indicator": "range_15m", "output": "lower", "bars_ago": 1}),
                        build_condition("range_long_rsi_turn", "当前 5M RSI 高于上一根", {"kind": "indicator", "indicator": "rsi_5m", "output": "value"}, "gt", {"kind": "indicator", "indicator": "rsi_5m", "output": "value", "bars_ago": 1}),
                    ],
                ),
                "long_exit": build_group(
                    "range_long_exit",
                    "区间做多离场",
                    "or",
                    [
                        build_condition("range_long_back_to_mid", "收盘价回到 15M 中轴上方", {"kind": "price", "field": "close"}, "gt", {"kind": "indicator", "indicator": "range_15m", "output": "middle"}),
                        build_condition("range_long_rsi_recover", "5M RSI 高于 55", {"kind": "indicator", "indicator": "rsi_5m", "output": "value"}, "gt", {"kind": "value", "value": 55}),
                    ],
                ),
                "short_entry": build_group(
                    "range_short_entry",
                    "区间假突破收回后高空",
                    "and",
                    [
                        build_condition("range_short_position", "15M P 不低于 0.85", {"kind": "indicator", "indicator": "range_15m", "output": "position"}, "gt", {"kind": "value", "value": 0.85}),
                        build_condition("range_short_prev_break", "上一根 5M 最高价突破 15M 上沿", {"kind": "price", "field": "high", "bars_ago": 1}, "gt", {"kind": "indicator", "indicator": "range_15m", "output": "upper", "bars_ago": 1}),
                        build_condition("range_short_rsi_turn", "当前 5M RSI 低于上一根", {"kind": "indicator", "indicator": "rsi_5m", "output": "value"}, "lt", {"kind": "indicator", "indicator": "rsi_5m", "output": "value", "bars_ago": 1}),
                    ],
                    enabled=True,
                ),
                "short_exit": build_group(
                    "range_short_exit",
                    "区间做空离场",
                    "or",
                    [
                        build_condition("range_short_back_to_mid", "收盘价跌回 15M 中轴下方", {"kind": "price", "field": "close"}, "lt", {"kind": "indicator", "indicator": "range_15m", "output": "middle"}),
                        build_condition("range_short_rsi_recover", "5M RSI 低于 45", {"kind": "indicator", "indicator": "rsi_5m", "output": "value"}, "lt", {"kind": "value", "value": 45}),
                    ],
                    enabled=True,
                ),
            },
            "risk": {
                "stoploss": -0.05,
                "roi_targets": [],
                "trailing": {"enabled": False, "positive": 0.01, "offset": 0.02, "only_offset_reached": True},
                "partial_exits": [],
            },
        },
        "parameter_space": {
            "indicators.ema_1h.params.period": [34, 55, 89],
            "indicators.m_1h.params.lookback": [18, 24, 30],
            "indicators.range_15m.params.lookback": [24, 32, 36],
            "trend.regime.trend_regime_up.trend_up_m.right.value": [2.0, 2.5, 3.0],
            "trend.regime.trend_regime_up.trend_up_e.right.value": [0.3, 0.35, 0.4],
            "trend.long_entry.trend_long_pullback.right.offset_multiplier": [0.5, 0.8, 1.0, 1.2],
            "range.regime.range_min_width.right.value": [1.5, 2.0, 2.5, 3.0],
            "range.long_entry.range_long_position.right.value": [0.1, 0.15, 0.2],
            "range.short_entry.range_short_position.right.value": [0.8, 0.85, 0.9],
        },
        "builtin": {"key": "btc_regime_switch", "version_name": "Base v3", "notes": "BTC 多周期 M/E/P 状态切换与假突破收回确认版本"},
    },
}
