from __future__ import annotations

import json
from copy import deepcopy
from itertools import islice, product
from typing import Any

from app.services.backtest.strategy_catalog import get_indicator_registry_map
from app.services.backtest.strategy_contract import set_by_path
from app.services.backtest.strategy_runtime import StrategyRuntime


class FreqtradeStrategyBuilder:
    def __init__(self, strategy_class_name: str) -> None:
        self.strategy_class_name = strategy_class_name
        self.runtime = StrategyRuntime()

    def build_code(self, template: str, timeframe: str, config: dict[str, Any]) -> str:
        normalized_config = self.runtime.normalized_config(template, config)
        trade_settings = self.trade_settings(template, normalized_config)
        indicator_registry = get_indicator_registry_map()
        risk = normalized_config.get("risk") or {}
        execution = normalized_config.get("execution") or {}
        can_short = execution.get("direction") == "long_short"
        indicator_script = self._build_indicator_script(normalized_config, indicator_registry, timeframe)
        regime_priority = normalized_config.get("regime_priority") or ["trend", "range"]
        branch_masks = self._build_branch_masks(normalized_config, regime_priority)
        entry_assignments = self._build_signal_assignments(normalized_config, regime_priority, branch_masks, signal_kind="entry", can_short=can_short)
        exit_assignments = self._build_signal_assignments(normalized_config, regime_priority, branch_masks, signal_kind="exit", can_short=can_short)
        roi_targets = {
            str(int(item.get("minutes", 0))): float(item.get("profit", 0))
            for item in sorted([item for item in risk.get("roi_targets") or [] if item.get("enabled", True)], key=lambda item: int(item.get("minutes", 0)), reverse=True)
        }
        trailing = risk.get("trailing") or {}
        partial_exits = [item for item in risk.get("partial_exits") or [] if item.get("enabled", True)]
        partial_exit_block = self._build_partial_exit_block(partial_exits)
        warmup_bars = self.warmup_bars(template, normalized_config, timeframe)
        return f"""import pandas as pd
import talib.abstract as ta
from pandas import DataFrame
from freqtrade.strategy import IStrategy


class {self.strategy_class_name}(IStrategy):
    INTERFACE_VERSION = 3
    can_short = {can_short}
    timeframe = "{timeframe}"
    process_only_new_candles = True
    startup_candle_count = {warmup_bars}
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    minimal_roi = {repr(roi_targets)}
    stoploss = {float(risk.get("stoploss", -0.1))}
    trailing_stop = {bool(trailing.get("enabled", False))}
    trailing_stop_positive = {float(trailing.get("positive", 0.0))}
    trailing_stop_positive_offset = {float(trailing.get("offset", 0.0))}
    trailing_only_offset_is_reached = {bool(trailing.get("only_offset_reached", True))}
    position_adjustment_enable = {bool(partial_exits)}
    order_types = {repr(trade_settings["order_types"])}

    def _resample_ohlcv(self, dataframe: DataFrame, timeframe: str) -> DataFrame:
        rule_map = {{"1m": "1min", "5m": "5min", "15m": "15min", "1h": "1h", "4h": "4h", "1d": "1D"}}
        if timeframe not in rule_map:
            raise ValueError(f"Unsupported timeframe: {{timeframe}}")
        indexed = dataframe[["date", "open", "high", "low", "close", "volume"]].copy().set_index("date")
        resampled = (
            indexed.resample(rule_map[timeframe], label="right", closed="right")
            .agg({{"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}})
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
{indicator_script}
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = None
{entry_assignments}
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        dataframe["exit_tag"] = None
{exit_assignments}
        return dataframe
{partial_exit_block}
"""

    def warmup_bars(self, template: str, config: dict[str, Any], timeframe: str) -> int:
        return self.runtime.warmup_bars(template, config, timeframe)

    def trade_settings(self, template: str, config: dict[str, Any]) -> dict[str, Any]:
        normalized_config = self.runtime.normalized_config(template, config)
        partial_exits = [item for item in (normalized_config.get("risk") or {}).get("partial_exits") or [] if item.get("enabled", True)]
        order_types = {
            "entry": "market",
            "exit": "market",
            "stoploss": "market",
            "stoploss_on_exchange": False,
        }
        uses_market_entry = order_types.get("entry") == "market"
        uses_market_exit = order_types.get("exit") == "market"
        return {
            "order_types": order_types,
            "position_adjustment_enable": bool(partial_exits),
            "entry_pricing": {
                "price_side": "other" if uses_market_entry else "same",
                "use_order_book": True,
                "order_book_top": 1,
                "price_last_balance": 0.0,
                "check_depth_of_market": {"enabled": False, "bids_to_ask_delta": 1},
            },
            "exit_pricing": {
                "price_side": "other" if uses_market_exit else "same",
                "use_order_book": True,
                "order_book_top": 1,
            },
        }

    def candidate_configs(self, base_config: dict[str, Any], parameter_space: dict[str, list[Any]], optimize_trials: int):
        yield deepcopy(base_config)
        if optimize_trials <= 1 or not parameter_space:
            return
        keys = [key for key, values in parameter_space.items() if values]
        if not keys:
            return
        seen = {json.dumps(base_config, sort_keys=True, default=str)}
        for combo in islice(product(*(parameter_space[key] for key in keys)), max(optimize_trials - 1, 0)):
            candidate = deepcopy(base_config)
            for key, value in zip(keys, combo):
                set_by_path(candidate, key, value)
            signature = json.dumps(candidate, sort_keys=True, default=str)
            if signature in seen:
                continue
            seen.add(signature)
            yield candidate

    def _build_indicator_script(
        self,
        normalized_config: dict[str, Any],
        indicator_registry: dict[str, dict[str, Any]],
        base_timeframe: str,
    ) -> str:
        indicators = normalized_config.get("indicators") or {}
        timeframes: dict[str, list[tuple[str, dict[str, Any], dict[str, Any]]]] = {}
        for indicator_id, indicator in indicators.items():
            indicator_timeframe = indicator.get("timeframe") or "base"
            resolved_timeframe = base_timeframe if indicator_timeframe == "base" else indicator_timeframe
            indicator_spec = indicator_registry.get(indicator.get("type")) or {}
            timeframes.setdefault(resolved_timeframe, []).append((indicator_id, indicator, indicator_spec))

        lines = ["        dataframe = dataframe.sort_values(\"date\").copy()"]
        frame_vars: dict[str, str] = {base_timeframe: "dataframe"}
        for timeframe in sorted([key for key in timeframes.keys() if key != base_timeframe], key=self._timeframe_sort_key):
            frame_var = f'frame_{timeframe.replace("m", "m").replace("h", "h").replace("d", "d")}'
            frame_vars[timeframe] = frame_var
            lines.append(f'        {frame_var} = self._resample_ohlcv(dataframe, "{timeframe}")')

        for timeframe, indicator_items in timeframes.items():
            frame_var = frame_vars[timeframe]
            for indicator_id, indicator, indicator_spec in indicator_items:
                lines.extend(self._render_indicator_block(frame_var, indicator_id, indicator, indicator_spec))

        for timeframe in sorted([key for key in timeframes.keys() if key != base_timeframe], key=self._timeframe_sort_key):
            frame_var = frame_vars[timeframe]
            columns = [column for indicator_id, _indicator, indicator_spec in timeframes[timeframe] for column in self._indicator_output_columns(indicator_id, indicator_spec)]
            lines.append(f"        dataframe = self._merge_indicator_frame(dataframe, {frame_var}, {repr(columns)})")
        return "\n".join(lines)

    def _timeframe_sort_key(self, timeframe: str) -> int:
        from app.services.backtest.strategy_contract import timeframe_to_minutes

        return timeframe_to_minutes(timeframe)

    def _indicator_output_columns(self, indicator_id: str, indicator_spec: dict[str, Any]) -> list[str]:
        outputs = indicator_spec.get("outputs") or [{"key": "value"}]
        return [f'{indicator_id}__{output.get("key", "value")}' for output in outputs]

    def _render_indicator_block(self, frame_var: str, indicator_id: str, indicator: dict[str, Any], indicator_spec: dict[str, Any]) -> list[str]:
        indicator_type = indicator.get("type")
        engine = indicator_spec.get("engine", indicator_type)
        params = indicator.get("params") or {}
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
        raise ValueError(f"不支持的指标类型: {indicator_type}")

    def _compile_rule_tree(self, node: dict[str, Any]) -> str:
        if not node or not node.get("enabled", True):
            return '(dataframe["volume"] >= 0)'
        if node.get("node_type") == "condition":
            return self._compile_single_rule(node)
        logic = node.get("logic", "and")
        enabled_children = [child for child in node.get("children") or [] if child.get("enabled", True)]
        if not enabled_children:
            return '(dataframe["volume"] >= 0)'
        compiled = [self._compile_rule_tree(child) for child in enabled_children]
        glue = " & " if logic == "and" else " | "
        return "(" + glue.join(compiled) + ")"

    def _compile_single_rule(self, rule: dict[str, Any]) -> str:
        operator_map = {"gt": ">", "gte": ">=", "lt": "<", "lte": "<="}
        operator = operator_map.get(rule.get("operator"))
        if not operator:
            raise ValueError(f"不支持的条件操作符: {rule.get('operator')}")
        return f"({self._compile_source(rule.get('left') or {})} {operator} {self._compile_source(rule.get('right') or {})})"

    def _compile_source(self, source: dict[str, Any]) -> str:
        kind = source.get("kind")
        bars_ago = max(int(source.get("bars_ago", 0) or 0), 0)
        if kind == "price":
            expression = f'dataframe["{source.get("field", "close")}"]'
            return self._apply_shift(expression, bars_ago)
        if kind == "indicator":
            expression = f'dataframe["{source.get("indicator")}__{source.get("output", "value")}"]'
            return self._apply_shift(expression, bars_ago)
        if kind == "value":
            return repr(float(source.get("value", 0)))
        if kind == "indicator_multiplier":
            expression = f'(dataframe["{source.get("indicator")}__{source.get("output", "value")}"] * {float(source.get("multiplier", 1.0))})'
            return self._apply_shift(expression, bars_ago)
        if kind == "indicator_offset":
            expression = (
                f'(dataframe["{source.get("base_indicator")}__{source.get("base_output", "value")}"] '
                f'- dataframe["{source.get("offset_indicator")}__{source.get("offset_output", "value")}"] * {float(source.get("offset_multiplier", 1.0))})'
            )
            return self._apply_shift(expression, bars_ago)
        raise ValueError(f"不支持的条件源: {kind}")

    def _apply_shift(self, expression: str, bars_ago: int) -> str:
        if bars_ago <= 0:
            return expression
        return f"({expression}).shift({bars_ago})"

    def _build_branch_masks(self, normalized_config: dict[str, Any], regime_priority: list[str]) -> dict[str, str]:
        masks: dict[str, str] = {}
        remaining = '(dataframe["volume"] >= 0)'
        false_mask = '(dataframe["volume"] < 0)'
        for branch_key in regime_priority:
            branch = normalized_config.get(branch_key) or {}
            if not branch.get("enabled", True):
                masks[branch_key] = false_mask
                continue
            regime_mask = self._compile_rule_tree(branch.get("regime") or {})
            active_mask = f"(({remaining}) & ({regime_mask}))"
            masks[branch_key] = active_mask
            remaining = f"(({remaining}) & ~({active_mask}))"
        return masks

    def _build_signal_assignments(
        self,
        normalized_config: dict[str, Any],
        regime_priority: list[str],
        branch_masks: dict[str, str],
        *,
        signal_kind: str,
        can_short: bool,
    ) -> str:
        lines: list[str] = []
        if signal_kind == "entry":
            lines.append('        dataframe["enter_short"] = 0')
            lines.append('        dataframe["enter_short_tag"] = None')
        else:
            lines.append('        dataframe["exit_short"] = 0')
            lines.append('        dataframe["exit_short_tag"] = None')
        for branch_key in regime_priority:
            branch = normalized_config.get(branch_key) or {}
            if not branch.get("enabled", True):
                continue
            long_tree = "long_entry" if signal_kind == "entry" else "long_exit"
            long_column = "enter_long" if signal_kind == "entry" else "exit_long"
            long_tag = "enter_tag" if signal_kind == "entry" else "exit_tag"
            long_condition = f"(({branch_masks[branch_key]}) & ({self._compile_rule_tree(branch.get(long_tree) or {})}))"
            lines.append(f'        dataframe.loc[{long_condition}, ["{long_column}", "{long_tag}"]] = (1, "{branch_key}_long_{signal_kind}")')
            if not can_short:
                continue
            short_tree = "short_entry" if signal_kind == "entry" else "short_exit"
            short_column = "enter_short" if signal_kind == "entry" else "exit_short"
            short_tag = "enter_short_tag" if signal_kind == "entry" else "exit_short_tag"
            short_condition = f"(({branch_masks[branch_key]}) & ({self._compile_rule_tree(branch.get(short_tree) or {})}))"
            lines.append(f'        dataframe.loc[{short_condition}, ["{short_column}", "{short_tag}"]] = (1, "{branch_key}_short_{signal_kind}")')
        if not can_short:
            if signal_kind == "entry":
                lines = ['        dataframe["enter_short"] = 0', '        dataframe["enter_short_tag"] = None', *lines[2:]]
            else:
                lines = ['        dataframe["exit_short"] = 0', '        dataframe["exit_short_tag"] = None', *lines[2:]]
        return "\n".join(lines) if lines else "        pass"

    def _build_partial_exit_block(self, partial_exits: list[dict[str, Any]]) -> str:
        if not partial_exits:
            return ""
        steps = [{"profit": float(item.get("profit", 0)), "size_pct": float(item.get("size_pct", 0))} for item in sorted(partial_exits, key=lambda item: float(item.get("profit", 0))) if float(item.get("size_pct", 0)) > 0]
        if not steps:
            return ""
        return f"""
    def adjust_trade_position(self, trade, current_time, current_rate, current_profit, min_stake, max_stake, current_entry_rate, current_exit_rate, current_entry_profit, current_exit_profit, **kwargs):
        partial_steps = {repr(steps)}
        if trade.nr_of_successful_exits >= len(partial_steps):
            return None
        step = partial_steps[trade.nr_of_successful_exits]
        if current_profit < step["profit"]:
            return None
        reduction = trade.stake_amount * (step["size_pct"] / 100.0)
        if min_stake and reduction < min_stake:
            return None
        return -reduction, f"partial_{{trade.nr_of_successful_exits + 1}}"
"""
