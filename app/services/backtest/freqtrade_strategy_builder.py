from __future__ import annotations

import json
from copy import deepcopy
from itertools import islice, product
from typing import Any

from app.services.backtest.strategy_catalog import (
    get_indicator_registry_map,
)
from app.services.backtest.strategy_contract import set_by_path
from app.services.backtest.strategy_runtime import StrategyRuntime


class FreqtradeStrategyBuilder:
    def __init__(self, strategy_class_name: str) -> None:
        self.strategy_class_name = strategy_class_name
        self.runtime = StrategyRuntime()

    def build_code(self, template: str, timeframe: str, config: dict[str, Any]) -> str:
        normalized_config = self.runtime.normalized_config(template, config)
        indicator_registry = get_indicator_registry_map()
        indicators = normalized_config.get("indicators") or {}
        risk = normalized_config.get("risk") or {}
        indicator_lines = "\n".join(
            self._render_indicator_block(indicator_id, indicator, indicator_registry)
            for indicator_id, indicator in indicators.items()
        )
        entry_condition = self._compile_rule_tree(normalized_config.get("entry") or {})
        exit_condition = self._compile_rule_tree(normalized_config.get("exit") or {})
        roi_targets = {
            str(int(item.get("minutes", 0))): float(item.get("profit", 0))
            for item in sorted(
                [item for item in risk.get("roi_targets") or [] if item.get("enabled", True)],
                key=lambda item: int(item.get("minutes", 0)),
                reverse=True,
            )
        }
        trailing = risk.get("trailing") or {}
        partial_exits = [item for item in risk.get("partial_exits") or [] if item.get("enabled", True)]
        partial_exit_block = self._build_partial_exit_block(partial_exits)
        return f"""from pandas import DataFrame
import talib.abstract as ta
from freqtrade.strategy import IStrategy


class {self.strategy_class_name}(IStrategy):
    INTERFACE_VERSION = 3
    can_short = False
    timeframe = "{timeframe}"
    process_only_new_candles = True
    startup_candle_count = {self.warmup_bars(template, normalized_config)}
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
    order_types = {{"entry": "market", "exit": "market", "stoploss": "market", "stoploss_on_exchange": False}}

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
{indicator_lines or "        return dataframe"}
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        condition = {entry_condition}
        dataframe.loc[condition, ["enter_long", "enter_tag"]] = (1, "entry_signal")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        condition = {exit_condition}
        dataframe.loc[condition, ["exit_long", "exit_tag"]] = (1, "exit_signal")
        return dataframe
{partial_exit_block}
"""

    def warmup_bars(self, template: str, config: dict[str, Any]) -> int:
        return self.runtime.warmup_bars(template, config)

    def candidate_configs(
        self,
        base_config: dict[str, Any],
        parameter_space: dict[str, list[Any]],
        optimize_trials: int,
    ):
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

    def _render_indicator_block(self, indicator_id: str, indicator: dict[str, Any], indicator_registry: dict[str, dict[str, Any]]) -> str:
        indicator_type = indicator.get("type")
        indicator_spec = indicator_registry.get(indicator_type) or {}
        engine = indicator_spec.get("engine", indicator_type)
        params = indicator.get("params") or {}
        if engine == "ema":
            return f'        dataframe["{indicator_id}__value"] = ta.EMA(dataframe, timeperiod={int(params.get("period", 20))})'
        if engine == "sma":
            return f'        dataframe["{indicator_id}__value"] = ta.SMA(dataframe, timeperiod={int(params.get("period", 20))})'
        if engine == "rsi":
            return f'        dataframe["{indicator_id}__value"] = ta.RSI(dataframe, timeperiod={int(params.get("period", 14))})'
        if engine == "macd":
            return (
                f'        {indicator_id}_macd = ta.MACD(dataframe, fastperiod={int(params.get("fast", 12))}, '
                f'slowperiod={int(params.get("slow", 26))}, signalperiod={int(params.get("signal", 9))})\n'
                f'        dataframe["{indicator_id}__macd"] = {indicator_id}_macd["macd"]\n'
                f'        dataframe["{indicator_id}__signal"] = {indicator_id}_macd["macdsignal"]\n'
                f'        dataframe["{indicator_id}__hist"] = {indicator_id}_macd["macdhist"]'
            )
        if engine == "bbands":
            return (
                f'        {indicator_id}_upper, {indicator_id}_middle, {indicator_id}_lower = ta.BBANDS('
                f'dataframe["close"], timeperiod={int(params.get("period", 20))}, '
                f'nbdevup={float(params.get("stddev", 2.0))}, nbdevdn={float(params.get("stddev", 2.0))}, matype=0)\n'
                f'        dataframe["{indicator_id}__upper"] = {indicator_id}_upper\n'
                f'        dataframe["{indicator_id}__middle"] = {indicator_id}_middle\n'
                f'        dataframe["{indicator_id}__lower"] = {indicator_id}_lower'
            )
        if engine == "volume_sma":
            return f'        dataframe["{indicator_id}__value"] = ta.SMA(dataframe["volume"], timeperiod={int(params.get("period", 20))})'
        if engine == "atr":
            return f'        dataframe["{indicator_id}__value"] = ta.ATR(dataframe, timeperiod={int(params.get("period", 14))})'
        if engine == "rolling_high":
            return f'        dataframe["{indicator_id}__value"] = dataframe["high"].rolling({int(params.get("lookback", 20))}).max().shift(1)'
        if engine == "rolling_low":
            return f'        dataframe["{indicator_id}__value"] = dataframe["low"].rolling({int(params.get("lookback", 20))}).min().shift(1)'
        if engine == "roc":
            return f'        dataframe["{indicator_id}__value"] = ta.ROC(dataframe, timeperiod={int(params.get("period", 12))})'
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
        operator_map = {
            "gt": ">",
            "gte": ">=",
            "lt": "<",
            "lte": "<=",
        }
        operator = operator_map.get(rule.get("operator"))
        if not operator:
            raise ValueError(f"不支持的条件操作符: {rule.get('operator')}")
        return f"({self._compile_source(rule.get('left') or {})} {operator} {self._compile_source(rule.get('right') or {})})"

    def _compile_source(self, source: dict[str, Any]) -> str:
        kind = source.get("kind")
        if kind == "price":
            return f'dataframe["{source.get("field", "close")}"]'
        if kind == "indicator":
            return f'dataframe["{source.get("indicator")}__{source.get("output", "value")}"]'
        if kind == "value":
            return repr(float(source.get("value", 0)))
        if kind == "indicator_multiplier":
            return (
                f'(dataframe["{source.get("indicator")}__{source.get("output", "value")}"] '
                f'* {float(source.get("multiplier", 1.0))})'
            )
        if kind == "indicator_offset":
            return (
                f'(dataframe["{source.get("base_indicator")}__{source.get("base_output", "value")}"] '
                f'- dataframe["{source.get("offset_indicator")}__{source.get("offset_output", "value")}"] '
                f'* {float(source.get("offset_multiplier", 1.0))})'
            )
        raise ValueError(f"不支持的条件源: {kind}")

    def _build_partial_exit_block(self, partial_exits: list[dict[str, Any]]) -> str:
        if not partial_exits:
            return ""
        steps = [
            {
                "profit": float(item.get("profit", 0)),
                "size_pct": float(item.get("size_pct", 0)),
            }
            for item in sorted(partial_exits, key=lambda item: float(item.get("profit", 0)))
            if float(item.get("size_pct", 0)) > 0
        ]
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
