from __future__ import annotations

import json
from copy import deepcopy
from itertools import islice, product
from typing import Any

from app.schemas.strategy_contract import (
    StrategyConditionNodeResponse,
    StrategyGroupNodeResponse,
    StrategyIndicatorConfigResponse,
    StrategyPartialExitResponse,
    StrategyRuleSourceResponse,
    StrategyTemplateConfigResponse,
    StrategyTradePlanConfigResponse,
)
from app.services.backtest.scripted_template_runtime import (
    build_scripted_strategy_code,
    get_template_runtime,
    scripted_trade_settings,
    scripted_warmup_bars,
    template_builder_kind,
)
from app.services.backtest.freqtrade_exit_codegen import render_threshold_custom_exit
from app.services.backtest.freqtrade_strategy_runtime import (
    render_freqtrade_strategy_runtime,
    resolve_freqtrade_strategy_runtime,
)
from app.services.backtest.indicator_engines import (
    indicator_engine_definition,
)
from app.services.backtest.strategy_catalog import get_indicator_registry_map
from app.services.backtest.strategy_config_normalizer import normalize_strategy_identifier
from app.services.backtest.strategy_rule_tree import set_by_path, strategy_branch
from app.services.backtest.strategy_runtime import StrategyRuntime


class FreqtradeStrategyBuilder:
    def __init__(self, strategy_class_name: str) -> None:
        self.strategy_class_name = strategy_class_name
        self.runtime = StrategyRuntime()

    def build_code(self, template: str, timeframe: str, config: dict[str, Any] | StrategyTemplateConfigResponse) -> str:
        runtime_contract = get_template_runtime(template)
        if template_builder_kind(runtime_contract) == "scripted":
            return build_scripted_strategy_code(
                template=template,
                strategy_class_name=self.strategy_class_name,
                timeframe=timeframe,
            )
        normalized_config = self.runtime.normalized_config(template, config)
        trade_settings = self.trade_settings(template, normalized_config)
        indicator_registry = get_indicator_registry_map()
        risk = normalized_config.risk
        trade_plan = risk.trade_plan
        uses_trade_plan = bool(trade_plan.enabled)
        can_short = normalized_config.execution.direction == "long_short"
        indicator_script = self._build_indicator_script(normalized_config, indicator_registry, timeframe)
        regime_priority = normalized_config.regime_priority or ["trend", "range"]
        branch_masks = self._build_branch_masks(normalized_config, regime_priority)
        entry_assignments = self._build_signal_assignments(normalized_config, regime_priority, branch_masks, signal_kind="entry", can_short=can_short)
        exit_assignments = self._build_exit_assignments(
            normalized_config,
            regime_priority,
            branch_masks,
            can_short=can_short,
            uses_trade_plan=uses_trade_plan,
        )
        roi_targets = {
            str(int(item.minutes)): float(item.profit)
            for item in sorted([item for item in risk.roi_targets if item.enabled], key=lambda item: int(item.minutes), reverse=True)
        }
        if uses_trade_plan:
            roi_targets = {"0": 99.0}
        partial_exits = [item for item in risk.partial_exits if item.enabled]
        partial_exit_block = self._build_partial_exit_block(partial_exits)
        trade_plan_block = self._build_trade_plan_block(trade_plan) if uses_trade_plan else ""
        warmup_bars = self.warmup_bars(template, normalized_config, timeframe)
        runtime_block = render_freqtrade_strategy_runtime(
            resolve_freqtrade_strategy_runtime(
                can_short=can_short,
                timeframe=timeframe,
                startup_candle_count=warmup_bars,
                risk=risk.model_dump(),
                roi_targets=roi_targets,
                order_types=trade_settings["order_types"],
                has_exit_signals=True,
                has_custom_exit=uses_trade_plan,
                position_adjustment_enable=bool(partial_exits),
            )
        )
        return f"""import pandas as pd
import talib.abstract as ta
from pandas import DataFrame
from freqtrade.strategy import IStrategy


class {self.strategy_class_name}(IStrategy):
{runtime_block}

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
{trade_plan_block}
"""

    def warmup_bars(self, template: str, config: dict[str, Any] | StrategyTemplateConfigResponse, timeframe: str) -> int:
        runtime_contract = get_template_runtime(template)
        if template_builder_kind(runtime_contract) == "scripted":
            payload = config.model_dump() if isinstance(config, StrategyTemplateConfigResponse) else config
            return scripted_warmup_bars(template, payload, timeframe)
        payload = config.model_dump() if isinstance(config, StrategyTemplateConfigResponse) else config
        return self.runtime.warmup_bars(template, payload, timeframe)

    def trade_settings(self, template: str, config: dict[str, Any] | StrategyTemplateConfigResponse) -> dict[str, Any]:
        runtime_contract = get_template_runtime(template)
        if template_builder_kind(runtime_contract) == "scripted":
            payload = config.model_dump() if isinstance(config, StrategyTemplateConfigResponse) else config
            return scripted_trade_settings(template, payload)
        normalized_config = config if isinstance(config, StrategyTemplateConfigResponse) else self.runtime.normalized_config(template, config)
        partial_exits = [item for item in normalized_config.risk.partial_exits if item.enabled]
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
        normalized_config: StrategyTemplateConfigResponse,
        indicator_registry: dict[str, dict[str, Any]],
        base_timeframe: str,
    ) -> str:
        indicators = normalized_config.indicators
        timeframes: dict[str, list[tuple[str, StrategyIndicatorConfigResponse, dict[str, Any]]]] = {}
        for indicator_id, indicator in indicators.items():
            indicator_timeframe = indicator.timeframe or "base"
            resolved_timeframe = base_timeframe if indicator_timeframe == "base" else indicator_timeframe
            indicator_spec = indicator_registry.get(indicator.type) or {}
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
                normalize_strategy_identifier(indicator_id, "指标标识")
                engine = indicator_engine_definition(indicator.type, indicator_spec)
                lines.extend(
                    engine.render_code(
                        frame_var,
                        indicator_id,
                        indicator.params,
                    )
                )

        for timeframe in sorted([key for key in timeframes.keys() if key != base_timeframe], key=self._timeframe_sort_key):
            frame_var = frame_vars[timeframe]
            columns = [
                column
                for indicator_id, indicator, indicator_spec in timeframes[timeframe]
                for column in indicator_engine_definition(indicator.type, indicator_spec).output_columns(indicator_id)
            ]
            lines.append(f"        dataframe = self._merge_indicator_frame(dataframe, {frame_var}, {repr(columns)})")
        return "\n".join(lines)

    def _timeframe_sort_key(self, timeframe: str) -> int:
        from app.domain.market.timeframes import timeframe_to_minutes

        return timeframe_to_minutes(timeframe)

    def _compile_rule_tree(self, node: StrategyGroupNodeResponse | StrategyConditionNodeResponse) -> str:
        if not node.enabled:
            return '(dataframe["volume"] >= 0)'
        if isinstance(node, StrategyConditionNodeResponse):
            return self._compile_single_rule(node)
        logic = node.logic
        enabled_children = [child for child in node.children if child.enabled]
        if not enabled_children:
            return '(dataframe["volume"] >= 0)'
        compiled = [self._compile_rule_tree(child) for child in enabled_children]
        glue = " & " if logic == "and" else " | "
        return "(" + glue.join(compiled) + ")"

    def _compile_single_rule(self, rule: StrategyConditionNodeResponse) -> str:
        operator_map = {"gt": ">", "gte": ">=", "lt": "<", "lte": "<="}
        operator = operator_map.get(rule.operator)
        if not operator:
            raise ValueError(f"不支持的条件操作符: {rule.operator}")
        return f"({self._compile_source(rule.left)} {operator} {self._compile_source(rule.right)})"

    def _compile_source(self, source: StrategyRuleSourceResponse) -> str:
        kind = source.kind
        bars_ago = max(int(source.bars_ago or 0), 0)
        if kind == "price":
            expression = f'dataframe["{source.field or "close"}"]'
            return self._apply_shift(expression, bars_ago)
        if kind == "indicator":
            normalize_strategy_identifier(source.indicator, "指标标识")
            normalize_strategy_identifier(source.output or "value", "指标输出")
            expression = f'dataframe["{source.indicator}__{source.output or "value"}"]'
            return self._apply_shift(expression, bars_ago)
        if kind == "value":
            return repr(float(source.value or 0))
        if kind == "indicator_multiplier":
            normalize_strategy_identifier(source.indicator, "指标标识")
            normalize_strategy_identifier(source.output or "value", "指标输出")
            expression = f'(dataframe["{source.indicator}__{source.output or "value"}"] * {float(source.multiplier or 1.0)})'
            return self._apply_shift(expression, bars_ago)
        if kind == "indicator_offset":
            normalize_strategy_identifier(source.base_indicator, "基础指标标识")
            normalize_strategy_identifier(source.base_output or "value", "基础指标输出")
            normalize_strategy_identifier(source.offset_indicator, "偏移指标标识")
            normalize_strategy_identifier(source.offset_output or "value", "偏移指标输出")
            expression = (
                f'(dataframe["{source.base_indicator}__{source.base_output or "value"}"] '
                f'- dataframe["{source.offset_indicator}__{source.offset_output or "value"}"] * {float(source.offset_multiplier or 1.0)})'
            )
            return self._apply_shift(expression, bars_ago)
        raise ValueError(f"不支持的条件源: {kind}")

    def _apply_shift(self, expression: str, bars_ago: int) -> str:
        if bars_ago <= 0:
            return expression
        return f"({expression}).shift({bars_ago})"

    def _build_branch_masks(self, normalized_config: StrategyTemplateConfigResponse, regime_priority: list[str]) -> dict[str, str]:
        masks: dict[str, str] = {}
        remaining = '(dataframe["volume"] >= 0)'
        false_mask = '(dataframe["volume"] < 0)'
        for branch_key in regime_priority:
            branch = strategy_branch(normalized_config, branch_key)
            if not branch.enabled:
                masks[branch_key] = false_mask
                continue
            regime_mask = self._compile_rule_tree(branch.regime)
            active_mask = f"(({remaining}) & ({regime_mask}))"
            masks[branch_key] = active_mask
            remaining = f"(({remaining}) & ~({active_mask}))"
        return masks

    def _build_signal_assignments(
        self,
        normalized_config: StrategyTemplateConfigResponse,
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
            branch = strategy_branch(normalized_config, branch_key)
            if not branch.enabled:
                continue
            long_tree = branch.long_entry if signal_kind == "entry" else branch.long_exit
            long_column = "enter_long" if signal_kind == "entry" else "exit_long"
            long_tag = "enter_tag" if signal_kind == "entry" else "exit_tag"
            long_condition = f"(({branch_masks[branch_key]}) & ({self._compile_rule_tree(long_tree)}))"
            lines.append(f'        dataframe.loc[{long_condition}, ["{long_column}", "{long_tag}"]] = (1, "{branch_key}_long_{signal_kind}")')
            if not can_short:
                continue
            short_tree = branch.short_entry if signal_kind == "entry" else branch.short_exit
            short_column = "enter_short" if signal_kind == "entry" else "exit_short"
            short_tag = "enter_short_tag" if signal_kind == "entry" else "exit_short_tag"
            shared_tag = "enter_tag" if signal_kind == "entry" else "exit_tag"
            short_condition = f"(({branch_masks[branch_key]}) & ({self._compile_rule_tree(short_tree)}))"
            lines.append(
                f'        dataframe.loc[{short_condition}, ["{short_column}", "{short_tag}", "{shared_tag}"]] = '
                f'(1, "{branch_key}_short_{signal_kind}", "{branch_key}_short_{signal_kind}")'
            )
        if not can_short:
            if signal_kind == "entry":
                lines = ['        dataframe["enter_short"] = 0', '        dataframe["enter_short_tag"] = None', *lines[2:]]
            else:
                lines = ['        dataframe["exit_short"] = 0', '        dataframe["exit_short_tag"] = None', *lines[2:]]
        return "\n".join(lines) if lines else "        pass"

    def _build_exit_assignments(
        self,
        normalized_config: StrategyTemplateConfigResponse,
        regime_priority: list[str],
        branch_masks: dict[str, str],
        *,
        can_short: bool,
        uses_trade_plan: bool,
    ) -> str:
        if not uses_trade_plan:
            return self._build_signal_assignments(
                normalized_config,
                regime_priority,
                branch_masks,
                signal_kind="exit",
                can_short=can_short,
            )
        lines = [
            '        dataframe["exit_short"] = 0',
            '        dataframe["exit_short_tag"] = None',
        ]
        return "\n".join(lines)

    def _build_trade_plan_block(self, trade_plan: StrategyTradePlanConfigResponse) -> str:
        atr_indicator = str(trade_plan.atr_indicator or "").strip()
        support_indicator = str(trade_plan.support_indicator or "").strip()
        resistance_indicator = str(trade_plan.resistance_indicator or "").strip()
        if not atr_indicator or not support_indicator or not resistance_indicator:
            raise ValueError("trade_plan 已启用，但缺少 ATR / 支撑 / 阻力指标")
        normalize_strategy_identifier(atr_indicator, "ATR 指标标识")
        normalize_strategy_identifier(support_indicator, "支撑指标标识")
        normalize_strategy_identifier(resistance_indicator, "阻力指标标识")
        stop_multiplier = float(trade_plan.stop_multiplier or 1.0)
        min_stop_pct = float(trade_plan.min_stop_pct or 0.01)
        reward_multiplier = float(trade_plan.reward_multiplier or 2.0)
        return f"""
    def _resolve_trade_plan(self, pair, trade):
        cached_plan = trade.get_custom_data("trade_plan")
        if cached_plan:
            return cached_plan
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or dataframe.empty:
            return None
        open_time = pd.Timestamp(trade.open_date_utc)
        entry_frame = dataframe.loc[dataframe["date"] <= open_time]
        if entry_frame.empty:
            return None
        entry_candle = entry_frame.iloc[-1]
        entry_price = float(trade.open_rate)
        atr_value = float(entry_candle.get("{atr_indicator}__value") or 0.0)
        stop_distance = max(atr_value * {stop_multiplier}, entry_price * {min_stop_pct})
        if trade.is_short:
            structure = float(entry_candle.get("{resistance_indicator}__value") or (entry_price + stop_distance))
            stop_price = max(entry_price + stop_distance, structure)
            target_price = entry_price - abs(entry_price - stop_price) * {reward_multiplier}
        else:
            structure = float(entry_candle.get("{support_indicator}__value") or (entry_price - stop_distance))
            stop_price = min(entry_price - stop_distance, structure)
            target_price = entry_price + abs(entry_price - stop_price) * {reward_multiplier}
        resolved_plan = {{"target": float(target_price), "stop": float(stop_price)}}
        if getattr(trade, "id", None) is not None:
            trade.set_custom_data("trade_plan", resolved_plan)
        return resolved_plan
{render_threshold_custom_exit(
    plan_var_name="trade_plan",
    resolve_plan_expression="self._resolve_trade_plan(pair, trade)",
    stop_reason="trade_plan_stop",
    target_reason="trade_plan_target",
)}"""

    def _build_partial_exit_block(self, partial_exits: list[StrategyPartialExitResponse]) -> str:
        if not partial_exits:
            return ""
        steps = [
            {"profit": float(item.profit), "size_pct": float(item.size_pct)}
            for item in sorted(partial_exits, key=lambda item: float(item.profit))
            if float(item.size_pct) > 0
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
