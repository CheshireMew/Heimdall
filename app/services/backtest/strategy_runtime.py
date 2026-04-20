from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pandas as pd

from app.schemas.strategy_contract import (
    StrategyConditionNodeResponse,
    StrategyGroupNodeResponse,
    StrategyIndicatorConfigResponse,
    StrategyRuleSourceResponse,
    StrategyTemplateConfigResponse,
)
from app.domain.market.timeframes import timeframe_to_minutes
from app.services.backtest.scripted_template_runtime import get_template_runtime, template_supports_signal_runtime
from app.services.backtest.indicator_engines import (
    apply_indicator_frame,
    indicator_warmup_bars,
    resolve_indicator_engine,
)
from app.services.backtest.strategy_catalog import get_indicator_registry_map, get_template_spec
from app.services.backtest.strategy_config_normalizer import (
    allowed_run_timeframes,
    explicit_indicator_timeframes,
    normalize_strategy_config_model,
    preferred_run_timeframe,
)
from app.services.backtest.strategy_rule_tree import (
    strategy_branch,
)
from utils.time_utils import to_utc_naive_datetime


@dataclass(slots=True)
class StrategySignalSnapshot:
    timestamp: datetime
    price: float
    active_regime: str | None
    long_entry_signal: bool
    long_exit_signal: bool
    short_entry_signal: bool
    short_exit_signal: bool
    indicators: dict[str, Any]


class StrategyRuntime:
    def normalized_config(self, template: str, config: dict[str, Any] | StrategyTemplateConfigResponse) -> StrategyTemplateConfigResponse:
        if isinstance(config, StrategyTemplateConfigResponse):
            return config
        return normalize_strategy_config_model(
            config=dict(config or {}),
            default_config=get_template_spec(template)["default_config"],
        )

    def validate_timeframe_compatibility(self, template: str, config: dict[str, Any] | StrategyTemplateConfigResponse, base_timeframe: str) -> StrategyTemplateConfigResponse:
        normalized_config = self.normalized_config(template, config)
        config_payload = normalized_config.model_dump()
        if base_timeframe not in allowed_run_timeframes(config_payload):
            indicator_details = []
            for indicator_id, indicator in normalized_config.indicators.items():
                indicator_timeframe = self._resolve_indicator_timeframe(indicator, base_timeframe)
                label = str(indicator.label or indicator_id)
                indicator_details.append(f"{label}({indicator_timeframe})")
            joined = ", ".join(indicator_details) if indicator_details else ", ".join(explicit_indicator_timeframes(config_payload))
            raise ValueError(
                f"运行周期 {base_timeframe} 与策略指标周期不兼容。"
                f"当前策略包含更细周期或非整倍数周期指标: {joined}。"
                f"请把运行周期调到 {preferred_run_timeframe(config_payload)}，或改掉对应指标周期。"
            )
        return normalized_config

    def warmup_bars(self, template: str, config: dict[str, Any] | StrategyTemplateConfigResponse, base_timeframe: str) -> int:
        normalized_config = self.validate_timeframe_compatibility(template, config, base_timeframe)
        indicator_registry = get_indicator_registry_map()
        base_minutes = timeframe_to_minutes(base_timeframe)
        warmups = [5]
        for indicator in normalized_config.indicators.values():
            indicator_type = indicator.type
            indicator_spec = indicator_registry.get(indicator_type) or {}
            engine = resolve_indicator_engine(indicator_type, indicator_spec)
            params = indicator.params
            indicator_timeframe = self._resolve_indicator_timeframe(indicator, base_timeframe)
            scale = max(timeframe_to_minutes(indicator_timeframe) // base_minutes, 1)
            warmups.append(indicator_warmup_bars(engine, params) * scale)
        return max(warmups) + 5

    def build_signal_snapshots(
        self,
        template: str,
        config: dict[str, Any] | StrategyTemplateConfigResponse,
        candles: list[list[float]],
        timeframe: str,
        *,
        after_timestamp_ms: int | None = None,
    ) -> list[StrategySignalSnapshot]:
        runtime_contract = get_template_runtime(template)
        if not template_supports_signal_runtime(runtime_contract):
            raise ValueError("该内置脚本策略当前只支持回测编译，不支持规则快照和模拟盘")
        frame = self.build_frame(template, config, candles, timeframe)
        if frame.empty:
            return []
        if after_timestamp_ms is not None:
            frame = frame[frame["timestamp"] > after_timestamp_ms]
        if frame.empty:
            return []
        snapshots: list[StrategySignalSnapshot] = []
        indicators = self.normalized_config(template, config).indicators
        for _, row in frame.iterrows():
            snapshots.append(
                StrategySignalSnapshot(
                    timestamp=to_utc_naive_datetime(row["date"]),
                    price=float(row["close"]),
                    active_regime=str(row["active_regime"]) if row.get("active_regime") else None,
                    long_entry_signal=bool(row["long_entry_signal"]),
                    long_exit_signal=bool(row["long_exit_signal"]),
                    short_entry_signal=bool(row["short_entry_signal"]),
                    short_exit_signal=bool(row["short_exit_signal"]),
                    indicators=self._row_indicator_snapshot(row, indicators),
                )
            )
        return snapshots

    def build_frame(
        self,
        template: str,
        config: dict[str, Any] | StrategyTemplateConfigResponse,
        candles: list[list[float]],
        timeframe: str,
    ) -> pd.DataFrame:
        runtime_contract = get_template_runtime(template)
        if not template_supports_signal_runtime(runtime_contract):
            raise ValueError("该内置脚本策略当前只支持回测编译，不支持规则帧构建")
        frame = self._base_frame(candles)
        if frame.empty:
            return frame
        normalized_config = self.validate_timeframe_compatibility(template, config, timeframe)
        indicator_registry = get_indicator_registry_map()
        frame = self._merge_indicator_frames(frame, normalized_config, indicator_registry, timeframe)
        branch_masks = self._resolve_branch_masks(frame, normalized_config)
        frame["active_regime"] = pd.Series([None] * len(frame), index=frame.index, dtype=object)
        frame["long_entry_signal"] = pd.Series(False, index=frame.index, dtype=bool)
        frame["long_exit_signal"] = pd.Series(False, index=frame.index, dtype=bool)
        frame["short_entry_signal"] = pd.Series(False, index=frame.index, dtype=bool)
        frame["short_exit_signal"] = pd.Series(False, index=frame.index, dtype=bool)
        allow_short = normalized_config.execution.direction == "long_short"
        for branch_key in normalized_config.regime_priority or ["trend", "range"]:
            branch = strategy_branch(normalized_config, branch_key)
            mask = branch_masks.get(branch_key)
            if mask is None:
                continue
            frame.loc[mask, "active_regime"] = branch_key
            frame["long_entry_signal"] = frame["long_entry_signal"] | (mask & self._evaluate_rule_tree(frame, branch.long_entry))
            frame["long_exit_signal"] = frame["long_exit_signal"] | (mask & self._evaluate_rule_tree(frame, branch.long_exit))
            if allow_short:
                frame["short_entry_signal"] = frame["short_entry_signal"] | (mask & self._evaluate_rule_tree(frame, branch.short_entry))
                frame["short_exit_signal"] = frame["short_exit_signal"] | (mask & self._evaluate_rule_tree(frame, branch.short_exit))
        return frame

    def _base_frame(self, candles: list[list[float]]) -> pd.DataFrame:
        if not candles:
            return pd.DataFrame(columns=["timestamp", "date", "open", "high", "low", "close", "volume"])
        frame = pd.DataFrame(candles, columns=["timestamp", "open", "high", "low", "close", "volume"])
        frame["date"] = pd.to_datetime(frame["timestamp"], unit="ms", utc=True)
        frame = frame.sort_values("date").reset_index(drop=True)
        return frame

    def _merge_indicator_frames(
        self,
        frame: pd.DataFrame,
        config: StrategyTemplateConfigResponse,
        indicator_registry: dict[str, dict[str, Any]],
        base_timeframe: str,
    ) -> pd.DataFrame:
        timeframe_frames: dict[str, pd.DataFrame] = {base_timeframe: frame.copy()}
        for indicator in config.indicators.values():
            indicator_timeframe = self._resolve_indicator_timeframe(indicator, base_timeframe)
            if indicator_timeframe not in timeframe_frames:
                timeframe_frames[indicator_timeframe] = self._resample_frame(frame, indicator_timeframe, base_timeframe)
        for indicator_id, indicator in config.indicators.items():
            indicator_timeframe = self._resolve_indicator_timeframe(indicator, base_timeframe)
            indicator_spec = indicator_registry.get(indicator.type) or {}
            apply_indicator_frame(
                timeframe_frames[indicator_timeframe],
                indicator_id,
                resolve_indicator_engine(indicator.type, indicator_spec),
                indicator.params,
            )
        merged = frame.copy()
        for indicator_id, indicator in config.indicators.items():
            indicator_timeframe = self._resolve_indicator_timeframe(indicator, base_timeframe)
            source_frame = timeframe_frames[indicator_timeframe]
            output_columns = [column for column in source_frame.columns if column.startswith(f"{indicator_id}__")]
            if not output_columns:
                continue
            if indicator_timeframe == base_timeframe:
                for column in output_columns:
                    merged[column] = source_frame[column]
                continue
            merge_frame = source_frame[["date", *output_columns]].sort_values("date")
            merged = pd.merge_asof(
                merged.sort_values("date"),
                merge_frame,
                on="date",
                direction="backward",
            )
        return merged

    def _resample_frame(self, frame: pd.DataFrame, target_timeframe: str, base_timeframe: str) -> pd.DataFrame:
        base_minutes = timeframe_to_minutes(base_timeframe)
        target_minutes = timeframe_to_minutes(target_timeframe)
        if target_minutes < base_minutes or target_minutes % base_minutes != 0:
            raise ValueError(f"指标周期必须大于等于运行周期且为整数倍: base={base_timeframe}, indicator={target_timeframe}")
        if target_timeframe == base_timeframe:
            return frame.copy()
        rule = self._pandas_rule(target_timeframe)
        indexed = frame[["date", "open", "high", "low", "close", "volume"]].set_index("date")
        resampled = (
            indexed.resample(rule, label="right", closed="right")
            .agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
            .dropna()
            .reset_index()
        )
        resampled["timestamp"] = resampled["date"].astype("int64").floordiv(1_000_000)
        return resampled[["timestamp", "date", "open", "high", "low", "close", "volume"]]

    def _pandas_rule(self, timeframe: str) -> str:
        mapping = {
            "1m": "1min",
            "5m": "5min",
            "15m": "15min",
            "1h": "1h",
            "4h": "4h",
            "1d": "1D",
        }
        if timeframe not in mapping:
            raise ValueError(f"不支持的重采样周期: {timeframe}")
        return mapping[timeframe]

    def _resolve_indicator_timeframe(self, indicator: StrategyIndicatorConfigResponse, base_timeframe: str) -> str:
        configured = str(indicator.timeframe or "base")
        return base_timeframe if configured == "base" else configured

    def _evaluate_rule_tree(
        self,
        frame: pd.DataFrame,
        node: StrategyGroupNodeResponse | StrategyConditionNodeResponse,
    ) -> pd.Series:
        if not node.enabled:
            return pd.Series(True, index=frame.index, dtype=bool)
        if isinstance(node, StrategyConditionNodeResponse):
            return self._evaluate_condition(frame, node)
        logic = node.logic
        children = [child for child in node.children if child.enabled]
        if not children:
            return pd.Series(True, index=frame.index, dtype=bool)
        evaluated = [self._evaluate_rule_tree(frame, child) for child in children]
        result = evaluated[0]
        for item in evaluated[1:]:
            result = result & item if logic == "and" else result | item
        return result.fillna(False)

    def _evaluate_condition(self, frame: pd.DataFrame, node: StrategyConditionNodeResponse) -> pd.Series:
        left = self._resolve_source(frame, node.left)
        right = self._resolve_source(frame, node.right)
        operator = node.operator
        if operator == "gt":
            return (left > right).fillna(False)
        if operator == "gte":
            return (left >= right).fillna(False)
        if operator == "lt":
            return (left < right).fillna(False)
        if operator == "lte":
            return (left <= right).fillna(False)
        raise ValueError(f"不支持的条件操作符: {operator}")

    def _resolve_source(self, frame: pd.DataFrame, source: StrategyRuleSourceResponse) -> pd.Series:
        kind = source.kind
        bars_ago = max(int(source.bars_ago or 0), 0)
        if kind == "price":
            field = source.field or "close"
            return frame[field].shift(bars_ago)
        if kind == "indicator":
            return frame[f"{source.indicator}__{source.output or 'value'}"].shift(bars_ago)
        if kind == "value":
            return pd.Series(float(source.value or 0), index=frame.index, dtype=float)
        if kind == "indicator_multiplier":
            base = frame[f"{source.indicator}__{source.output or 'value'}"]
            return (base * float(source.multiplier or 1.0)).shift(bars_ago)
        if kind == "indicator_offset":
            base = frame[f"{source.base_indicator}__{source.base_output or 'value'}"]
            offset = frame[f"{source.offset_indicator}__{source.offset_output or 'value'}"]
            return (base - (offset * float(source.offset_multiplier or 1.0))).shift(bars_ago)
        raise ValueError(f"不支持的条件源: {kind}")

    def _resolve_branch_masks(self, frame: pd.DataFrame, config: StrategyTemplateConfigResponse) -> dict[str, pd.Series]:
        remaining = pd.Series(True, index=frame.index, dtype=bool)
        masks: dict[str, pd.Series] = {}
        for branch_key in config.regime_priority or ["trend", "range"]:
            branch = strategy_branch(config, branch_key)
            if not branch.enabled:
                masks[branch_key] = pd.Series(False, index=frame.index, dtype=bool)
                continue
            regime_mask = self._evaluate_rule_tree(frame, branch.regime)
            active_mask = (remaining & regime_mask).fillna(False)
            masks[branch_key] = active_mask
            remaining = (remaining & ~active_mask).fillna(False)
        return masks

    def _row_indicator_snapshot(self, row: pd.Series, indicators: dict[str, StrategyIndicatorConfigResponse]) -> dict[str, Any]:
        snapshot: dict[str, Any] = {}
        for indicator_id, indicator in indicators.items():
            values: dict[str, Any] = {}
            prefix = f"{indicator_id}__"
            for key in row.index:
                if not str(key).startswith(prefix):
                    continue
                output_key = str(key)[len(prefix):]
                values[output_key] = self._coerce_scalar(row[key])
            snapshot[indicator_id] = {
                "label": indicator.label or indicator_id,
                "type": indicator.type,
                "timeframe": indicator.timeframe,
                "values": values,
            }
        return snapshot

    def _coerce_scalar(self, value: Any) -> Any:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        if pd.isna(value):
            return None
        if isinstance(value, (pd.Timestamp, datetime)):
            return to_utc_naive_datetime(value).isoformat()
        if hasattr(value, "item"):
            try:
                return value.item()
            except Exception:
                return value
        return value
