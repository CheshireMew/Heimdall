from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pandas as pd
import talib.abstract as ta

from app.services.backtest.strategy_catalog import get_indicator_registry_map, get_template_spec
from app.services.backtest.strategy_contract import (
    allowed_run_timeframes,
    explicit_indicator_timeframes,
    normalize_strategy_payload,
    preferred_run_timeframe,
    timeframe_to_minutes,
)


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
    def normalized_config(self, template: str, config: dict[str, Any]) -> dict[str, Any]:
        normalized_config, _ = normalize_strategy_payload(
            template_spec=get_template_spec(template),
            config=dict(config or {}),
            parameter_space={},
        )
        return normalized_config

    def validate_timeframe_compatibility(self, template: str, config: dict[str, Any], base_timeframe: str) -> dict[str, Any]:
        normalized_config = self.normalized_config(template, config)
        if base_timeframe not in allowed_run_timeframes(normalized_config):
            indicator_details = []
            for indicator_id, indicator in (normalized_config.get("indicators") or {}).items():
                indicator_timeframe = self._resolve_indicator_timeframe(indicator, base_timeframe)
                label = str(indicator.get("label") or indicator_id)
                indicator_details.append(f"{label}({indicator_timeframe})")
            joined = ", ".join(indicator_details) if indicator_details else ", ".join(explicit_indicator_timeframes(normalized_config))
            raise ValueError(
                f"运行周期 {base_timeframe} 与策略指标周期不兼容。"
                f"当前策略包含更细周期或非整倍数周期指标: {joined}。"
                f"请把运行周期调到 {preferred_run_timeframe(normalized_config)}，或改掉对应指标周期。"
            )
        return normalized_config

    def warmup_bars(self, template: str, config: dict[str, Any], base_timeframe: str) -> int:
        normalized_config = self.validate_timeframe_compatibility(template, config, base_timeframe)
        indicator_registry = get_indicator_registry_map()
        base_minutes = timeframe_to_minutes(base_timeframe)
        warmups = [5]
        for indicator in (normalized_config.get("indicators") or {}).values():
            indicator_type = indicator.get("type")
            indicator_spec = indicator_registry.get(indicator_type) or {}
            engine = indicator_spec.get("engine", indicator_type)
            params = indicator.get("params") or {}
            indicator_timeframe = self._resolve_indicator_timeframe(indicator, base_timeframe)
            scale = max(timeframe_to_minutes(indicator_timeframe) // base_minutes, 1)
            if engine in {"ema", "sma", "roc"}:
                warmups.append(int(params.get("period", 20)) * scale)
            elif engine == "rsi":
                warmups.append(int(params.get("period", 14)) * scale)
            elif engine == "macd":
                warmups.append((int(params.get("slow", 26)) + int(params.get("signal", 9))) * scale)
            elif engine == "bbands":
                warmups.append(int(params.get("period", 20)) * scale)
            elif engine == "volume_sma":
                warmups.append(int(params.get("period", 20)) * scale)
            elif engine == "atr":
                warmups.append(int(params.get("period", 14)) * scale)
            elif engine in {"rolling_high", "rolling_low"}:
                warmups.append(int(params.get("lookback", 20)) * scale)
            elif engine == "displacement_atr":
                warmups.append(max(int(params.get("lookback", 24)), int(params.get("atr_period", 14))) * scale)
            elif engine == "efficiency_ratio":
                warmups.append((int(params.get("lookback", 24)) + 1) * scale)
            elif engine == "range_context":
                warmups.append(max(int(params.get("lookback", 32)), int(params.get("atr_period", 14))) * scale)
        return max(warmups) + 5

    def build_signal_snapshots(
        self,
        template: str,
        config: dict[str, Any],
        candles: list[list[float]],
        timeframe: str,
        *,
        after_timestamp_ms: int | None = None,
    ) -> list[StrategySignalSnapshot]:
        frame = self.build_frame(template, config, candles, timeframe)
        if frame.empty:
            return []
        if after_timestamp_ms is not None:
            frame = frame[frame["timestamp"] > after_timestamp_ms]
        if frame.empty:
            return []
        snapshots: list[StrategySignalSnapshot] = []
        indicators = self.normalized_config(template, config).get("indicators") or {}
        for _, row in frame.iterrows():
            snapshots.append(
                StrategySignalSnapshot(
                    timestamp=self._to_datetime(row["date"]),
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
        config: dict[str, Any],
        candles: list[list[float]],
        timeframe: str,
    ) -> pd.DataFrame:
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
        execution = normalized_config.get("execution") or {}
        allow_short = execution.get("direction") == "long_short"
        for branch_key in normalized_config.get("regime_priority") or ["trend", "range"]:
            branch = normalized_config.get(branch_key) or {}
            mask = branch_masks.get(branch_key)
            if mask is None:
                continue
            frame.loc[mask, "active_regime"] = branch_key
            frame["long_entry_signal"] = frame["long_entry_signal"] | (mask & self._evaluate_rule_tree(frame, branch.get("long_entry") or {}))
            frame["long_exit_signal"] = frame["long_exit_signal"] | (mask & self._evaluate_rule_tree(frame, branch.get("long_exit") or {}))
            if allow_short:
                frame["short_entry_signal"] = frame["short_entry_signal"] | (mask & self._evaluate_rule_tree(frame, branch.get("short_entry") or {}))
                frame["short_exit_signal"] = frame["short_exit_signal"] | (mask & self._evaluate_rule_tree(frame, branch.get("short_exit") or {}))
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
        config: dict[str, Any],
        indicator_registry: dict[str, dict[str, Any]],
        base_timeframe: str,
    ) -> pd.DataFrame:
        timeframe_frames: dict[str, pd.DataFrame] = {base_timeframe: frame.copy()}
        for indicator in (config.get("indicators") or {}).values():
            indicator_timeframe = self._resolve_indicator_timeframe(indicator, base_timeframe)
            if indicator_timeframe not in timeframe_frames:
                timeframe_frames[indicator_timeframe] = self._resample_frame(frame, indicator_timeframe, base_timeframe)
        for indicator_id, indicator in (config.get("indicators") or {}).items():
            indicator_timeframe = self._resolve_indicator_timeframe(indicator, base_timeframe)
            self._apply_indicator(timeframe_frames[indicator_timeframe], indicator_id, indicator, indicator_registry)
        merged = frame.copy()
        for indicator_id, indicator in (config.get("indicators") or {}).items():
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

    def _resolve_indicator_timeframe(self, indicator: dict[str, Any], base_timeframe: str) -> str:
        configured = str(indicator.get("timeframe") or "base")
        return base_timeframe if configured == "base" else configured

    def _apply_indicator(
        self,
        frame: pd.DataFrame,
        indicator_id: str,
        indicator: dict[str, Any],
        indicator_registry: dict[str, dict[str, Any]],
    ) -> None:
        indicator_type = indicator.get("type")
        indicator_spec = indicator_registry.get(indicator_type) or {}
        engine = indicator_spec.get("engine", indicator_type)
        params = indicator.get("params") or {}
        if engine == "ema":
            frame[f"{indicator_id}__value"] = ta.EMA(frame, timeperiod=int(params.get("period", 20)))
            return
        if engine == "sma":
            frame[f"{indicator_id}__value"] = ta.SMA(frame, timeperiod=int(params.get("period", 20)))
            return
        if engine == "rsi":
            frame[f"{indicator_id}__value"] = ta.RSI(frame, timeperiod=int(params.get("period", 14)))
            return
        if engine == "macd":
            result = ta.MACD(frame, fastperiod=int(params.get("fast", 12)), slowperiod=int(params.get("slow", 26)), signalperiod=int(params.get("signal", 9)))
            frame[f"{indicator_id}__macd"] = result["macd"]
            frame[f"{indicator_id}__signal"] = result["macdsignal"]
            frame[f"{indicator_id}__hist"] = result["macdhist"]
            return
        if engine == "bbands":
            upper, middle, lower = ta.BBANDS(
                frame["close"],
                timeperiod=int(params.get("period", 20)),
                nbdevup=float(params.get("stddev", 2.0)),
                nbdevdn=float(params.get("stddev", 2.0)),
                matype=0,
            )
            frame[f"{indicator_id}__upper"] = upper
            frame[f"{indicator_id}__middle"] = middle
            frame[f"{indicator_id}__lower"] = lower
            return
        if engine == "volume_sma":
            frame[f"{indicator_id}__value"] = ta.SMA(frame["volume"], timeperiod=int(params.get("period", 20)))
            return
        if engine == "atr":
            frame[f"{indicator_id}__value"] = ta.ATR(frame, timeperiod=int(params.get("period", 14)))
            return
        if engine == "rolling_high":
            frame[f"{indicator_id}__value"] = frame["high"].rolling(int(params.get("lookback", 20))).max().shift(1)
            return
        if engine == "rolling_low":
            frame[f"{indicator_id}__value"] = frame["low"].rolling(int(params.get("lookback", 20))).min().shift(1)
            return
        if engine == "roc":
            frame[f"{indicator_id}__value"] = ta.ROC(frame, timeperiod=int(params.get("period", 12)))
            return
        if engine == "displacement_atr":
            lookback = int(params.get("lookback", 24))
            atr_period = int(params.get("atr_period", 14))
            atr = ta.ATR(frame, timeperiod=atr_period)
            displacement = frame["close"] - frame["close"].shift(lookback)
            frame[f"{indicator_id}__value"] = displacement / atr.replace(0.0, pd.NA)
            return
        if engine == "efficiency_ratio":
            lookback = int(params.get("lookback", 24))
            displacement = (frame["close"] - frame["close"].shift(lookback)).abs()
            path = frame["close"].diff().abs().rolling(lookback).sum()
            frame[f"{indicator_id}__value"] = displacement / path.replace(0.0, pd.NA)
            return
        if engine == "range_context":
            lookback = int(params.get("lookback", 32))
            atr_period = int(params.get("atr_period", 14))
            upper = frame["high"].rolling(lookback).max().shift(1)
            lower = frame["low"].rolling(lookback).min().shift(1)
            width = upper - lower
            atr = ta.ATR(frame, timeperiod=atr_period)
            frame[f"{indicator_id}__upper"] = upper
            frame[f"{indicator_id}__lower"] = lower
            frame[f"{indicator_id}__middle"] = (upper + lower) / 2.0
            frame[f"{indicator_id}__position"] = (frame["close"] - lower) / width.replace(0.0, pd.NA)
            frame[f"{indicator_id}__width_ratio"] = width / atr.replace(0.0, pd.NA)
            return
        raise ValueError(f"不支持的指标类型: {indicator_type}")

    def _evaluate_rule_tree(self, frame: pd.DataFrame, node: dict[str, Any]) -> pd.Series:
        if not node or not node.get("enabled", True):
            return pd.Series(True, index=frame.index, dtype=bool)
        if node.get("node_type") == "condition":
            return self._evaluate_condition(frame, node)
        logic = node.get("logic", "and")
        children = [child for child in node.get("children") or [] if child.get("enabled", True)]
        if not children:
            return pd.Series(True, index=frame.index, dtype=bool)
        evaluated = [self._evaluate_rule_tree(frame, child) for child in children]
        result = evaluated[0]
        for item in evaluated[1:]:
            result = result & item if logic == "and" else result | item
        return result.fillna(False)

    def _evaluate_condition(self, frame: pd.DataFrame, node: dict[str, Any]) -> pd.Series:
        left = self._resolve_source(frame, node.get("left") or {})
        right = self._resolve_source(frame, node.get("right") or {})
        operator = node.get("operator")
        if operator == "gt":
            return (left > right).fillna(False)
        if operator == "gte":
            return (left >= right).fillna(False)
        if operator == "lt":
            return (left < right).fillna(False)
        if operator == "lte":
            return (left <= right).fillna(False)
        raise ValueError(f"不支持的条件操作符: {operator}")

    def _resolve_source(self, frame: pd.DataFrame, source: dict[str, Any]) -> pd.Series:
        kind = source.get("kind")
        bars_ago = max(int(source.get("bars_ago", 0) or 0), 0)
        if kind == "price":
            field = source.get("field", "close")
            return frame[field].shift(bars_ago)
        if kind == "indicator":
            return frame[f'{source.get("indicator")}__{source.get("output", "value")}'].shift(bars_ago)
        if kind == "value":
            return pd.Series(float(source.get("value", 0)), index=frame.index, dtype=float)
        if kind == "indicator_multiplier":
            base = frame[f'{source.get("indicator")}__{source.get("output", "value")}']
            return (base * float(source.get("multiplier", 1.0))).shift(bars_ago)
        if kind == "indicator_offset":
            base = frame[f'{source.get("base_indicator")}__{source.get("base_output", "value")}']
            offset = frame[f'{source.get("offset_indicator")}__{source.get("offset_output", "value")}']
            return (base - (offset * float(source.get("offset_multiplier", 1.0)))).shift(bars_ago)
        raise ValueError(f"不支持的条件源: {kind}")

    def _resolve_branch_masks(self, frame: pd.DataFrame, config: dict[str, Any]) -> dict[str, pd.Series]:
        remaining = pd.Series(True, index=frame.index, dtype=bool)
        masks: dict[str, pd.Series] = {}
        for branch_key in config.get("regime_priority") or ["trend", "range"]:
            branch = config.get(branch_key) or {}
            if not branch.get("enabled", True):
                masks[branch_key] = pd.Series(False, index=frame.index, dtype=bool)
                continue
            regime_mask = self._evaluate_rule_tree(frame, branch.get("regime") or {})
            active_mask = (remaining & regime_mask).fillna(False)
            masks[branch_key] = active_mask
            remaining = (remaining & ~active_mask).fillna(False)
        return masks

    def _row_indicator_snapshot(self, row: pd.Series, indicators: dict[str, Any]) -> dict[str, Any]:
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
                "label": indicator.get("label") or indicator_id,
                "type": indicator.get("type"),
                "timeframe": indicator.get("timeframe", "base"),
                "values": values,
            }
        return snapshot

    def _coerce_scalar(self, value: Any) -> Any:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        if pd.isna(value):
            return None
        if isinstance(value, (pd.Timestamp, datetime)):
            return self._to_datetime(value).isoformat()
        if hasattr(value, "item"):
            try:
                return value.item()
            except Exception:
                return value
        return value

    def _to_datetime(self, value: Any) -> datetime:
        timestamp = pd.Timestamp(value)
        if timestamp.tzinfo is None:
            return timestamp.to_pydatetime().replace(tzinfo=None)
        return timestamp.tz_convert("UTC").to_pydatetime().replace(tzinfo=None)
