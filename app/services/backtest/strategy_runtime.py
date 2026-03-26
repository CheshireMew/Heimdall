from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pandas as pd
import talib.abstract as ta

from app.services.backtest.strategy_catalog import get_indicator_registry_map, get_template_spec
from app.services.backtest.strategy_contract import normalize_strategy_payload


@dataclass(slots=True)
class StrategySignalSnapshot:
    timestamp: datetime
    price: float
    entry_signal: bool
    exit_signal: bool
    indicators: dict[str, Any]


class StrategyRuntime:
    def normalized_config(self, template: str, config: dict[str, Any]) -> dict[str, Any]:
        normalized_config, _ = normalize_strategy_payload(
            template_spec=get_template_spec(template),
            config=dict(config or {}),
            parameter_space={},
        )
        return normalized_config

    def warmup_bars(self, template: str, config: dict[str, Any]) -> int:
        normalized_config = self.normalized_config(template, config)
        indicator_registry = get_indicator_registry_map()
        warmups = [5]
        for indicator in (normalized_config.get("indicators") or {}).values():
            indicator_type = indicator.get("type")
            indicator_spec = indicator_registry.get(indicator_type) or {}
            engine = indicator_spec.get("engine", indicator_type)
            params = indicator.get("params") or {}
            if engine in {"ema", "sma", "roc"}:
                warmups.append(int(params.get("period", 20)))
            elif engine == "rsi":
                warmups.append(int(params.get("period", 14)))
            elif engine == "macd":
                warmups.append(int(params.get("slow", 26)) + int(params.get("signal", 9)))
            elif engine == "bbands":
                warmups.append(int(params.get("period", 20)))
            elif engine == "volume_sma":
                warmups.append(int(params.get("period", 20)))
            elif engine == "atr":
                warmups.append(int(params.get("period", 14)))
            elif engine in {"rolling_high", "rolling_low"}:
                warmups.append(int(params.get("lookback", 20)))
        return max(warmups) + 5

    def build_signal_snapshots(
        self,
        template: str,
        config: dict[str, Any],
        candles: list[list[float]],
        *,
        after_timestamp_ms: int | None = None,
    ) -> list[StrategySignalSnapshot]:
        frame = self.build_frame(template, config, candles)
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
                    entry_signal=bool(row["entry_signal"]),
                    exit_signal=bool(row["exit_signal"]),
                    indicators=self._row_indicator_snapshot(row, indicators),
                )
            )
        return snapshots

    def build_frame(
        self,
        template: str,
        config: dict[str, Any],
        candles: list[list[float]],
    ) -> pd.DataFrame:
        frame = self._base_frame(candles)
        if frame.empty:
            return frame
        normalized_config = self.normalized_config(template, config)
        indicator_registry = get_indicator_registry_map()
        for indicator_id, indicator in (normalized_config.get("indicators") or {}).items():
            self._apply_indicator(frame, indicator_id, indicator, indicator_registry)
        frame["entry_signal"] = self._evaluate_rule_tree(frame, normalized_config.get("entry") or {})
        frame["exit_signal"] = self._evaluate_rule_tree(frame, normalized_config.get("exit") or {})
        return frame

    def _base_frame(self, candles: list[list[float]]) -> pd.DataFrame:
        if not candles:
            return pd.DataFrame(columns=["timestamp", "date", "open", "high", "low", "close", "volume"])
        frame = pd.DataFrame(candles, columns=["timestamp", "open", "high", "low", "close", "volume"])
        frame["date"] = pd.to_datetime(frame["timestamp"], unit="ms", utc=True)
        return frame

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
            result = ta.MACD(
                frame,
                fastperiod=int(params.get("fast", 12)),
                slowperiod=int(params.get("slow", 26)),
                signalperiod=int(params.get("signal", 9)),
            )
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
        if kind == "price":
            field = source.get("field", "close")
            return frame[field]
        if kind == "indicator":
            return frame[f'{source.get("indicator")}__{source.get("output", "value")}']
        if kind == "value":
            return pd.Series(float(source.get("value", 0)), index=frame.index, dtype=float)
        if kind == "indicator_multiplier":
            base = frame[f'{source.get("indicator")}__{source.get("output", "value")}']
            return base * float(source.get("multiplier", 1.0))
        if kind == "indicator_offset":
            base = frame[f'{source.get("base_indicator")}__{source.get("base_output", "value")}']
            offset = frame[f'{source.get("offset_indicator")}__{source.get("offset_output", "value")}']
            return base - (offset * float(source.get("offset_multiplier", 1.0)))
        raise ValueError(f"不支持的条件源: {kind}")

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
