from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from typing import Any

import pandas as pd

from app.infra.db.database import init_db
from app.services.factors.repository import FactorResearchRepository
from app.services.market.indicator_repository import MarketIndicatorRepository
from app.services.market.market_data_service import MarketDataService
from config import settings


@dataclass(frozen=True, slots=True)
class FactorDefinition:
    factor_id: str
    name: str
    category: str
    source: str
    unit: str | None = None
    feature_mode: str = "level"
    description: str | None = None


class FactorResearchService:
    DATASET_SCHEMA_VERSION = 1
    SUPPORTED_TIMEFRAMES = ("1h", "4h", "1d")
    SUPPORTED_CATEGORIES = ("Macro", "Onchain", "Sentiment", "Tech", "Derived")
    DEFAULT_FORWARD_HORIZONS = (1, 3, 5, 10)
    DEFAULT_CLEANING = {
        "winsorize_zscore": 4.0,
        "bucket_count": 5,
        "rolling_ic_window": 30,
        "min_sample_size": 60,
    }
    DERIVED_FACTORS: tuple[FactorDefinition, ...] = (
        FactorDefinition("DERIVED_CLOSE_RETURN_1", "Price Return (1 Bar)", "Derived", "derived", "%", "level", "最近 1 根 K 线的价格涨跌幅。"),
        FactorDefinition("DERIVED_CLOSE_RETURN_5", "Price Return (5 Bars)", "Derived", "derived", "%", "level", "最近 5 根 K 线的累计涨跌幅。"),
        FactorDefinition("DERIVED_VOLUME_CHANGE_1", "Volume Change (1 Bar)", "Derived", "derived", "%", "level", "最近 1 根 K 线成交量变化率。"),
        FactorDefinition("DERIVED_REALIZED_VOL_20", "Realized Volatility (20 Bars)", "Derived", "derived", "%", "level", "最近 20 根 K 线的已实现波动率。"),
        FactorDefinition("DERIVED_RANGE_PCT", "Intrabar Range", "Derived", "derived", "%", "level", "单根 K 线振幅占收盘价比例。"),
        FactorDefinition("DERIVED_MA_GAP_20", "Price vs MA20 Gap", "Derived", "derived", "%", "level", "价格相对 20 均线的偏离比例。"),
    )
    LEVEL_FACTOR_IDS = {"US10Y", "HY_SPREAD", "FED_RATE", "FEAR_GREED", "BTC_DRAWDOWN"}

    def __init__(
        self,
        *,
        market_data_service: MarketDataService | None = None,
        indicator_repository: MarketIndicatorRepository | None = None,
        repository: FactorResearchRepository | None = None,
    ) -> None:
        self.market_data_service = market_data_service or MarketDataService()
        self.indicator_repository = indicator_repository or MarketIndicatorRepository()
        self.repository = repository or FactorResearchRepository()
        init_db()

    def get_catalog(self) -> dict[str, Any]:
        external_factors = [self._meta_to_factor(meta) for meta in self.indicator_repository.list_active_meta()]
        factor_list = sorted(
            [*external_factors, *self.DERIVED_FACTORS],
            key=lambda item: (self.SUPPORTED_CATEGORIES.index(item.category), item.name.lower()),
        )
        return {
            "symbols": settings.SYMBOLS,
            "timeframes": list(self.SUPPORTED_TIMEFRAMES),
            "categories": list(self.SUPPORTED_CATEGORIES),
            "factors": [self._serialize_factor(item) for item in factor_list],
            "forward_horizons": list(self.DEFAULT_FORWARD_HORIZONS),
            "cleaning": dict(self.DEFAULT_CLEANING),
        }

    def list_runs(self, limit: int = 20) -> list[dict[str, Any]]:
        return self.repository.list_research_runs(limit=limit)

    def get_run(self, run_id: int) -> dict[str, Any] | None:
        return self.repository.get_research_run(run_id)

    def build_stored_blend_frame(self, run_id: int) -> tuple[dict[str, Any], pd.DataFrame]:
        run = self.get_run(run_id)
        if not run:
            raise ValueError("因子研究记录不存在。")
        forward_horizons = list((run.get("request") or {}).get("forward_horizons") or self.DEFAULT_FORWARD_HORIZONS)
        frame = self._rows_to_frame(self.repository.get_dataset_rows(run["dataset_id"]), forward_horizons)
        return run, self._apply_blend_weights(frame, run["blend"], forward_horizons)

    def build_live_blend_frame(self, run_id: int, *, end_date: datetime | None = None) -> tuple[dict[str, Any], pd.DataFrame]:
        run = self.get_run(run_id)
        if not run:
            raise ValueError("因子研究记录不存在。")
        request_payload = dict(run.get("request") or {})
        selected_factor_ids = [item["factor_id"] for item in (run.get("blend") or {}).get("selected_factors") or []]
        definitions = self._select_factors([], selected_factor_ids)
        if not definitions:
            raise ValueError("当前研究记录没有可执行的组合因子。")

        request_end = end_date or datetime.now(timezone.utc).replace(tzinfo=None)
        request_start = request_end - timedelta(days=int(request_payload.get("days", 365)))
        timeframe_delta = self._timeframe_delta(request_payload["timeframe"])
        fetch_start = request_start - (timeframe_delta * 60)
        forward_horizons = list(request_payload.get("forward_horizons") or self.DEFAULT_FORWARD_HORIZONS)

        price_frame = self._build_price_frame(
            request_payload["symbol"],
            request_payload["timeframe"],
            fetch_start,
            request_end,
            forward_horizons,
        )
        raw_factor_frame = self._build_raw_factor_frame(definitions, price_frame, fetch_start)
        frame = price_frame.loc[price_frame["timestamp"] >= request_start, ["timestamp", "close", "volume"]].copy().reset_index(drop=True)
        for definition in definitions:
            raw_series = raw_factor_frame.get(definition.factor_id)
            if raw_series is None:
                continue
            feature_series = self._transform_feature(raw_series, definition.feature_mode)
            frame[f"feature::{definition.factor_id}"] = self._aligned_series(price_frame["timestamp"], feature_series, frame["timestamp"]).to_numpy()
        for horizon in forward_horizons:
            frame[f"label::{horizon}"] = self._aligned_series(
                price_frame["timestamp"],
                price_frame[f"future_return_{horizon}"],
                frame["timestamp"],
            ).to_numpy()
        return run, self._apply_blend_weights(frame, run["blend"], forward_horizons)

    def analyze(
        self,
        *,
        symbol: str,
        timeframe: str,
        days: int,
        horizon_bars: int,
        max_lag_bars: int,
        categories: list[str] | None = None,
        factor_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        if symbol not in settings.SYMBOLS:
            raise ValueError(f"无效交易对。可选: {settings.SYMBOLS}")
        if timeframe not in self.SUPPORTED_TIMEFRAMES:
            raise ValueError(f"当前只支持这些周期: {list(self.SUPPORTED_TIMEFRAMES)}")

        definitions = self._select_factors(categories or [], factor_ids or [])
        if not definitions:
            raise ValueError("没有可研究的因子，请至少选择一个分类或因子。")

        forward_horizons = sorted({*self.DEFAULT_FORWARD_HORIZONS, int(horizon_bars)})
        dataset = self._load_or_build_dataset(
            symbol=symbol,
            timeframe=timeframe,
            days=days,
            primary_horizon=horizon_bars,
            forward_horizons=forward_horizons,
            categories=categories or [],
            definitions=definitions,
        )
        frame = self._rows_to_frame(self.repository.get_dataset_rows(dataset["id"]), forward_horizons)
        if frame.empty:
            raise ValueError("可用因子样本不足，暂时无法完成研究。")

        factor_results: list[dict[str, Any]] = []
        for definition in definitions:
            factor_result = self._analyze_factor(
                definition=definition,
                frame=frame,
                primary_horizon=horizon_bars,
                forward_horizons=forward_horizons,
                max_lag_bars=max_lag_bars,
            )
            if factor_result:
                factor_results.append(factor_result)

        if not factor_results:
            raise ValueError("可用因子样本不足，暂时无法完成研究。")

        factor_results.sort(key=lambda item: item["scorecard"]["score"], reverse=True)
        blend = self._build_blend(
            factor_results=factor_results,
            primary_horizon=horizon_bars,
            forward_horizons=forward_horizons,
        )
        summary = self._build_summary(
            dataset=dataset,
            symbol=symbol,
            timeframe=timeframe,
            days=days,
            primary_horizon=horizon_bars,
            max_lag_bars=max_lag_bars,
            factor_count=len(factor_results),
            blend=blend,
        )
        run = self.repository.create_research_run(
            dataset_id=dataset["id"],
            request_payload={
                "symbol": symbol,
                "timeframe": timeframe,
                "days": days,
                "horizon_bars": horizon_bars,
                "max_lag_bars": max_lag_bars,
                "categories": list(categories or []),
                "factor_ids": list(factor_ids or []),
                "forward_horizons": forward_horizons,
            },
            summary=summary,
            ranking=[item["scorecard"] for item in factor_results],
            details=[item["detail"] for item in factor_results],
            blend=blend,
        )
        return {
            "run_id": run["id"],
            "dataset_id": dataset["id"],
            "summary": summary,
            "ranking": [item["scorecard"] for item in factor_results],
            "details": [item["detail"] for item in factor_results],
            "blend": blend,
        }

    def _load_or_build_dataset(
        self,
        *,
        symbol: str,
        timeframe: str,
        days: int,
        primary_horizon: int,
        forward_horizons: list[int],
        categories: list[str],
        definitions: list[FactorDefinition],
    ) -> dict[str, Any]:
        end_date = datetime.now(timezone.utc).replace(tzinfo=None)
        start_date = end_date - timedelta(days=days)
        signature = self._dataset_signature(
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            primary_horizon=primary_horizon,
            forward_horizons=forward_horizons,
            categories=categories,
            factor_ids=[item.factor_id for item in definitions],
            cleaning=self.DEFAULT_CLEANING,
        )
        existing = self.repository.get_dataset_by_signature(signature)
        if existing:
            return existing

        timeframe_delta = self._timeframe_delta(timeframe)
        fetch_start = start_date - (timeframe_delta * 60)
        price_frame = self._build_price_frame(symbol, timeframe, fetch_start, end_date, forward_horizons)
        if price_frame.empty:
            raise ValueError("没有可用于因子研究的价格数据。")
        raw_factor_frame = self._build_raw_factor_frame(definitions, price_frame, fetch_start)

        dataset_frame = price_frame.loc[price_frame["timestamp"] >= start_date, ["timestamp", "close", "volume"]].copy()
        dataset_frame = dataset_frame.reset_index(drop=True)
        for definition in definitions:
            raw_series = raw_factor_frame.get(definition.factor_id)
            if raw_series is None:
                continue
            feature_series = self._transform_feature(raw_series, definition.feature_mode)
            dataset_frame[f"raw::{definition.factor_id}"] = self._aligned_series(price_frame["timestamp"], raw_series, dataset_frame["timestamp"]).to_numpy()
            dataset_frame[f"feature::{definition.factor_id}"] = self._aligned_series(price_frame["timestamp"], feature_series, dataset_frame["timestamp"]).to_numpy()
        for horizon in forward_horizons:
            dataset_frame[f"label::{horizon}"] = self._aligned_series(
                price_frame["timestamp"],
                price_frame[f"future_return_{horizon}"],
                dataset_frame["timestamp"],
            ).to_numpy()

        dataset_rows = []
        for row in dataset_frame.to_dict("records"):
            raw_values = {
                definition.factor_id: self._to_optional_float(row.get(f"raw::{definition.factor_id}"))
                for definition in definitions
            }
            feature_values = {
                definition.factor_id: self._to_optional_float(row.get(f"feature::{definition.factor_id}"))
                for definition in definitions
            }
            labels = {
                str(horizon): self._to_optional_float(row.get(f"label::{horizon}"))
                for horizon in forward_horizons
            }
            dataset_rows.append(
                {
                    "timestamp": row["timestamp"],
                    "close": float(row["close"]),
                    "volume": float(row["volume"]),
                    "raw_values": raw_values,
                    "feature_values": feature_values,
                    "labels": labels,
                }
            )

        sample_rows = [
            row for row in dataset_rows
            if row["feature_values"] and row["labels"].get(str(primary_horizon)) is not None
        ]
        if len(sample_rows) < self.DEFAULT_CLEANING["min_sample_size"]:
            raise ValueError("可用因子样本不足，暂时无法完成研究。")

        return self.repository.create_dataset(
            signature=signature,
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            primary_horizon=primary_horizon,
            forward_horizons=forward_horizons,
            factor_ids=[item.factor_id for item in definitions],
            categories=categories or [item.category for item in definitions],
            cleaning=self.DEFAULT_CLEANING,
            row_count=len(dataset_rows),
            dataset_info={
                "schema_version": self.DATASET_SCHEMA_VERSION,
                "sample_range": {
                    "start": dataset_rows[0]["timestamp"].isoformat(),
                    "end": dataset_rows[-1]["timestamp"].isoformat(),
                },
                "warmup_bars": 60,
            },
            rows=dataset_rows,
        )

    def _rows_to_frame(self, rows: list[dict[str, Any]], forward_horizons: list[int]) -> pd.DataFrame:
        if not rows:
            return pd.DataFrame()
        factor_ids: set[str] = set()
        for row in rows:
            factor_ids.update((row.get("feature_values") or {}).keys())
            factor_ids.update((row.get("raw_values") or {}).keys())

        records = []
        for row in rows:
            payload = {
                "timestamp": row["timestamp"],
                "close": float(row["close"]),
                "volume": float(row["volume"]),
            }
            for factor_id in factor_ids:
                payload[f"raw::{factor_id}"] = self._to_optional_float((row.get("raw_values") or {}).get(factor_id))
                payload[f"feature::{factor_id}"] = self._to_optional_float((row.get("feature_values") or {}).get(factor_id))
            for horizon in forward_horizons:
                payload[f"label::{horizon}"] = self._to_optional_float((row.get("labels") or {}).get(str(horizon)))
            records.append(payload)
        return pd.DataFrame(records).sort_values("timestamp").reset_index(drop=True)

    def _build_summary(
        self,
        *,
        dataset: dict[str, Any],
        symbol: str,
        timeframe: str,
        days: int,
        primary_horizon: int,
        max_lag_bars: int,
        factor_count: int,
        blend: dict[str, Any],
    ) -> dict[str, Any]:
        sample_range = (dataset.get("dataset_info") or {}).get("sample_range") or {}
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "days": days,
            "horizon_bars": primary_horizon,
            "max_lag_bars": max_lag_bars,
            "factor_count": factor_count,
            "dataset_id": dataset["id"],
            "forward_horizons": list(dataset.get("forward_horizons") or []),
            "sample_range": {
                "start": sample_range.get("start") or dataset["start_date"].isoformat(),
                "end": sample_range.get("end") or dataset["end_date"].isoformat(),
            },
            "target_label": f"未来 {primary_horizon} 根 K 线收益",
            "blend_factor_count": len(blend.get("selected_factors") or []),
        }

    def _analyze_factor(
        self,
        *,
        definition: FactorDefinition,
        frame: pd.DataFrame,
        primary_horizon: int,
        forward_horizons: list[int],
        max_lag_bars: int,
    ) -> dict[str, Any] | None:
        raw_column = f"raw::{definition.factor_id}"
        feature_column = f"feature::{definition.factor_id}"
        if raw_column not in frame.columns or feature_column not in frame.columns:
            return None
        base = frame[["timestamp", "close", raw_column, feature_column, *[f"label::{h}" for h in forward_horizons if f'label::{h}' in frame.columns]]].copy()
        base = base.rename(columns={raw_column: "raw_factor", feature_column: "feature"})
        base["feature"] = self._clean_feature(base["feature"])
        base = base.dropna(subset=["feature", f"label::{primary_horizon}"])
        if len(base) < self.DEFAULT_CLEANING["min_sample_size"]:
            return None

        forward_metrics = []
        primary_metric = None
        for horizon in forward_horizons:
            label_column = f"label::{horizon}"
            if label_column not in base.columns:
                continue
            horizon_frame = base[["timestamp", "feature", label_column]].rename(columns={label_column: "target"}).dropna()
            if len(horizon_frame) < self.DEFAULT_CLEANING["min_sample_size"]:
                continue
            rolling_corr = self._build_rolling_corr(horizon_frame["timestamp"], horizon_frame["feature"], horizon_frame["target"])
            quantiles = self._build_quantiles(horizon_frame["feature"], horizon_frame["target"])
            metric = {
                "horizon": horizon,
                "sample_size": int(len(horizon_frame)),
                "target_mean": self._to_float(horizon_frame["target"].mean()),
                "target_std": self._to_float(horizon_frame["target"].std()),
                "correlation": self._safe_corr(horizon_frame["feature"], horizon_frame["target"]),
                "rank_correlation": self._safe_corr(horizon_frame["feature"].rank(), horizon_frame["target"].rank()),
                "ic_mean": self._to_float(pd.Series([item["value"] for item in rolling_corr]).mean() if rolling_corr else 0.0),
                "ic_std": self._to_float(pd.Series([item["value"] for item in rolling_corr]).std() if rolling_corr else 0.0),
                "ic_ir": self._information_ratio(rolling_corr),
                "ic_t_stat": self._t_stat(rolling_corr),
                "quantile_spread": self._quantile_spread(quantiles),
                "hit_rate": self._hit_rate(horizon_frame["feature"], horizon_frame["target"]),
            }
            forward_metrics.append(metric)
            if horizon == primary_horizon:
                primary_metric = metric

        if not primary_metric:
            return None

        primary_target = base[f"label::{primary_horizon}"]
        lag_profile = self._build_lag_profile(base["feature"], primary_target, max_lag_bars)
        best_lag = max(lag_profile, key=lambda item: abs(item["correlation"])) if lag_profile else {"lag": 0, "correlation": 0.0}
        rolling_corr = self._build_rolling_corr(base["timestamp"], base["feature"], primary_target)
        quantiles = self._build_quantiles(base["feature"], primary_target)
        turnover = self._bucket_turnover(base["feature"])
        stability = self._rolling_stability(primary_metric["correlation"], rolling_corr)
        normalized = self._build_normalized_series(
            base.assign(future_return=primary_target),
            feature_column="feature",
            limit=240,
        )
        score = self._score_factor(
            correlation=primary_metric["correlation"],
            rank_correlation=primary_metric["rank_correlation"],
            best_lag_correlation=best_lag["correlation"],
            stability=stability,
            quantile_spread=primary_metric["quantile_spread"],
            turnover=turnover,
            ic_ir=primary_metric["ic_ir"],
        )
        detail = {
            "factor_id": definition.factor_id,
            "name": definition.name,
            "category": definition.category,
            "unit": definition.unit,
            "feature_mode": definition.feature_mode,
            "description": definition.description,
            "sample_range": {
                "start": base["timestamp"].iloc[0].isoformat(),
                "end": base["timestamp"].iloc[-1].isoformat(),
            },
            "sample_size": int(len(base)),
            "latest_raw_value": self._to_float(base["raw_factor"].iloc[-1]),
            "latest_feature_value": self._to_float(base["feature"].iloc[-1]),
            "target_mean": primary_metric["target_mean"],
            "target_std": primary_metric["target_std"],
            "correlation": primary_metric["correlation"],
            "rank_correlation": primary_metric["rank_correlation"],
            "best_lag": int(best_lag["lag"]),
            "best_lag_correlation": self._to_float(best_lag["correlation"]),
            "stability": stability,
            "quantile_spread": primary_metric["quantile_spread"],
            "hit_rate": primary_metric["hit_rate"],
            "turnover": turnover,
            "ic_mean": primary_metric["ic_mean"],
            "ic_std": primary_metric["ic_std"],
            "ic_ir": primary_metric["ic_ir"],
            "ic_t_stat": primary_metric["ic_t_stat"],
            "forward_metrics": forward_metrics,
            "lag_profile": lag_profile,
            "rolling_correlation": rolling_corr,
            "quantiles": quantiles,
            "normalized_series": normalized,
        }
        scorecard = {
            "factor_id": definition.factor_id,
            "name": definition.name,
            "category": definition.category,
            "feature_mode": definition.feature_mode,
            "sample_size": int(len(base)),
            "latest_value": detail["latest_raw_value"],
            "correlation": primary_metric["correlation"],
            "rank_correlation": primary_metric["rank_correlation"],
            "best_lag": int(best_lag["lag"]),
            "best_lag_correlation": self._to_float(best_lag["correlation"]),
            "stability": stability,
            "quantile_spread": primary_metric["quantile_spread"],
            "hit_rate": primary_metric["hit_rate"],
            "turnover": turnover,
            "ic_ir": primary_metric["ic_ir"],
            "direction": "positive" if primary_metric["correlation"] >= 0 else "negative",
            "score": score,
        }
        analysis_frame = base[["timestamp", "close", "feature", *[f"label::{h}" for h in forward_horizons]]].copy()
        return {"scorecard": scorecard, "detail": detail, "analysis_frame": analysis_frame}

    def _build_blend(
        self,
        *,
        factor_results: list[dict[str, Any]],
        primary_horizon: int,
        forward_horizons: list[int],
    ) -> dict[str, Any]:
        ranked = sorted(factor_results, key=lambda item: item["scorecard"]["score"], reverse=True)
        selected: list[dict[str, Any]] = []
        dropped: list[dict[str, Any]] = []
        feature_corr_threshold = 0.8
        for result in ranked:
            scorecard = result["scorecard"]
            if scorecard["sample_size"] < self.DEFAULT_CLEANING["min_sample_size"]:
                dropped.append({"factor_id": scorecard["factor_id"], "name": scorecard["name"], "reason": "sample_too_small"})
                continue
            if scorecard["score"] < 12:
                dropped.append({"factor_id": scorecard["factor_id"], "name": scorecard["name"], "reason": "score_too_low"})
                continue
            keep = True
            for chosen in selected:
                merged = pd.merge(
                    chosen["analysis_frame"][["timestamp", "feature"]],
                    result["analysis_frame"][["timestamp", "feature"]],
                    on="timestamp",
                    how="inner",
                    suffixes=("_left", "_right"),
                ).dropna()
                if len(merged) < self.DEFAULT_CLEANING["min_sample_size"]:
                    continue
                corr = abs(self._safe_corr(merged["feature_left"], merged["feature_right"]))
                if corr >= feature_corr_threshold:
                    dropped.append(
                        {
                            "factor_id": scorecard["factor_id"],
                            "name": scorecard["name"],
                            "reason": f"too_similar_to_{chosen['scorecard']['factor_id']}",
                        }
                    )
                    keep = False
                    break
            if keep:
                selected.append(result)
            if len(selected) >= 5:
                break

        if not selected:
            selected = ranked[: min(3, len(ranked))]

        weights = []
        weight_base = 0.0
        for item in selected:
            scorecard = item["scorecard"]
            raw_weight = scorecard["score"] * max(scorecard["stability"], 0.2) * max(abs(scorecard["correlation"]), 0.05)
            signed_weight = raw_weight if scorecard["direction"] == "positive" else -raw_weight
            weights.append((item, signed_weight))
            weight_base += abs(signed_weight)
        normalized_weights = {
            item["scorecard"]["factor_id"]: (signed_weight / weight_base if weight_base else 0.0)
            for item, signed_weight in weights
        }

        composite_series = None
        composite_meta = []
        for item in selected:
            factor_id = item["scorecard"]["factor_id"]
            feature_frame = item["analysis_frame"][["timestamp", "close", "feature", *[f"label::{h}" for h in forward_horizons]]].copy()
            feature_frame = feature_frame.rename(columns={"feature": f"feature::{factor_id}"})
            if composite_series is None:
                composite_series = feature_frame
            else:
                composite_series = composite_series.merge(feature_frame, on=["timestamp", "close", *[f"label::{h}" for h in forward_horizons]], how="inner")
            composite_meta.append(
                {
                    "factor_id": factor_id,
                    "name": item["scorecard"]["name"],
                    "category": item["scorecard"]["category"],
                    "score": item["scorecard"]["score"],
                    "correlation": item["scorecard"]["correlation"],
                    "stability": item["scorecard"]["stability"],
                    "turnover": item["scorecard"]["turnover"],
                    "weight": self._to_float(normalized_weights[factor_id]),
                }
            )
        if composite_series is None or composite_series.empty:
            return {
                "selected_factors": [],
                "dropped_factors": dropped,
                "weights": [],
                "forward_metrics": [],
                "quantiles": [],
                "normalized_series": [],
                "entry_threshold": 0.0,
                "exit_threshold": 0.0,
            }

        feature_columns = [column for column in composite_series.columns if column.startswith("feature::")]
        composite_series["composite_score"] = 0.0
        for column in feature_columns:
            factor_id = column.split("::", 1)[1]
            composite_series["composite_score"] += self._zscore(composite_series[column]) * normalized_weights.get(factor_id, 0.0)
        composite_series["composite_score"] = self._clean_feature(composite_series["composite_score"])
        composite_series = composite_series.dropna(subset=["composite_score", f"label::{primary_horizon}"])

        forward_metrics = []
        for horizon in forward_horizons:
            label_column = f"label::{horizon}"
            horizon_frame = composite_series[["timestamp", "composite_score", label_column]].rename(columns={label_column: "target"}).dropna()
            if len(horizon_frame) < self.DEFAULT_CLEANING["min_sample_size"]:
                continue
            rolling_corr = self._build_rolling_corr(horizon_frame["timestamp"], horizon_frame["composite_score"], horizon_frame["target"])
            quantiles = self._build_quantiles(horizon_frame["composite_score"], horizon_frame["target"])
            forward_metrics.append(
                {
                    "horizon": horizon,
                    "sample_size": int(len(horizon_frame)),
                    "correlation": self._safe_corr(horizon_frame["composite_score"], horizon_frame["target"]),
                    "rank_correlation": self._safe_corr(horizon_frame["composite_score"].rank(), horizon_frame["target"].rank()),
                    "ic_mean": self._to_float(pd.Series([item["value"] for item in rolling_corr]).mean() if rolling_corr else 0.0),
                    "ic_std": self._to_float(pd.Series([item["value"] for item in rolling_corr]).std() if rolling_corr else 0.0),
                    "ic_ir": self._information_ratio(rolling_corr),
                    "ic_t_stat": self._t_stat(rolling_corr),
                    "quantile_spread": self._quantile_spread(quantiles),
                    "hit_rate": self._hit_rate(horizon_frame["composite_score"], horizon_frame["target"]),
                }
            )

        primary_quantiles = self._build_quantiles(composite_series["composite_score"], composite_series[f"label::{primary_horizon}"])
        normalized = self._build_normalized_series(
            composite_series.rename(columns={f"label::{primary_horizon}": "future_return", "composite_score": "feature"}),
            feature_column="feature",
            limit=240,
        )
        entry_threshold = self._to_float(composite_series["composite_score"].quantile(0.7))
        exit_threshold = self._to_float(composite_series["composite_score"].quantile(0.45))
        return {
            "selected_factors": composite_meta,
            "dropped_factors": dropped,
            "weights": composite_meta,
            "forward_metrics": forward_metrics,
            "quantiles": primary_quantiles,
            "normalized_series": normalized,
            "entry_threshold": entry_threshold,
            "exit_threshold": exit_threshold,
            "score_std": self._to_float(composite_series["composite_score"].std()),
            "score_mean": self._to_float(composite_series["composite_score"].mean()),
        }

    def _apply_blend_weights(
        self,
        frame: pd.DataFrame,
        blend: dict[str, Any],
        forward_horizons: list[int],
    ) -> pd.DataFrame:
        selected = list(blend.get("selected_factors") or [])
        if not selected:
            return pd.DataFrame()
        result = frame[["timestamp", "close", *[f"label::{h}" for h in forward_horizons if f"label::{h}" in frame.columns]]].copy()
        result["composite_score"] = 0.0
        for item in selected:
            factor_id = item["factor_id"]
            column = f"feature::{factor_id}"
            if column not in frame.columns:
                continue
            result["composite_score"] += self._zscore(frame[column]) * float(item.get("weight", 0.0))
        result["composite_score"] = self._clean_feature(result["composite_score"])
        result = result.sort_values("timestamp").reset_index(drop=True)
        return result

    def _select_factors(self, categories: list[str], factor_ids: list[str]) -> list[FactorDefinition]:
        selected_categories = {item for item in categories if item in self.SUPPORTED_CATEGORIES}
        selected_ids = {item for item in factor_ids if item}
        catalog = [self._meta_to_factor(meta) for meta in self.indicator_repository.list_active_meta()]
        catalog.extend(self.DERIVED_FACTORS)
        if not selected_categories and not selected_ids:
            return catalog
        result = []
        for definition in catalog:
            if selected_categories and definition.category not in selected_categories:
                continue
            if selected_ids and definition.factor_id not in selected_ids:
                continue
            result.append(definition)
        return result

    def _build_price_frame(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
        forward_horizons: list[int],
    ) -> pd.DataFrame:
        rows = self.market_data_service.fetch_ohlcv_range(symbol, timeframe, start_date, end_date)
        if not rows:
            return pd.DataFrame()
        frame = pd.DataFrame(rows, columns=["timestamp_ms", "open", "high", "low", "close", "volume"])
        frame["timestamp"] = pd.to_datetime(frame["timestamp_ms"], unit="ms", utc=True).dt.tz_localize(None)
        frame = frame.sort_values("timestamp").drop_duplicates("timestamp")
        frame["close_return_1"] = frame["close"].pct_change()
        frame["close_return_5"] = frame["close"].pct_change(5)
        frame["volume_change_1"] = frame["volume"].pct_change()
        frame["realized_vol_20"] = frame["close_return_1"].rolling(20).std()
        frame["range_pct"] = (frame["high"] - frame["low"]) / frame["close"].replace(0, pd.NA)
        frame["ma20"] = frame["close"].rolling(20).mean()
        frame["ma_gap_20"] = (frame["close"] / frame["ma20"]) - 1
        for horizon in forward_horizons:
            frame[f"future_return_{horizon}"] = frame["close"].shift(-horizon) / frame["close"] - 1
        return frame

    def _build_raw_factor_frame(
        self,
        definitions: list[FactorDefinition],
        price_frame: pd.DataFrame,
        start_date: datetime,
    ) -> pd.DataFrame:
        frame = pd.DataFrame(index=price_frame["timestamp"])
        derived_ids = {item.factor_id for item in self.DERIVED_FACTORS}
        for definition in definitions:
            if definition.factor_id in derived_ids:
                frame[definition.factor_id] = self._derived_series(definition.factor_id, price_frame).values

        external_ids = [item.factor_id for item in definitions if item.source == "indicator"]
        history_points = self.indicator_repository.get_history_points(external_ids, start_date=start_date - timedelta(days=30))
        for definition in definitions:
            if definition.source != "indicator":
                continue
            rows = history_points.get(definition.factor_id, [])
            if not rows:
                continue
            indicator_frame = pd.DataFrame(rows)
            indicator_frame["timestamp"] = pd.to_datetime(indicator_frame["timestamp"], utc=True).dt.tz_localize(None)
            indicator_frame = indicator_frame.sort_values("timestamp").drop_duplicates("timestamp")
            series = indicator_frame.set_index("timestamp")["value"].astype(float)
            aligned = series.reindex(frame.index.union(series.index)).sort_index().ffill().reindex(frame.index)
            frame[definition.factor_id] = aligned.values
        return frame

    def _derived_series(self, factor_id: str, price_frame: pd.DataFrame) -> pd.Series:
        mapping = {
            "DERIVED_CLOSE_RETURN_1": price_frame["close_return_1"],
            "DERIVED_CLOSE_RETURN_5": price_frame["close_return_5"],
            "DERIVED_VOLUME_CHANGE_1": price_frame["volume_change_1"],
            "DERIVED_REALIZED_VOL_20": price_frame["realized_vol_20"],
            "DERIVED_RANGE_PCT": price_frame["range_pct"],
            "DERIVED_MA_GAP_20": price_frame["ma_gap_20"],
        }
        return mapping[factor_id].astype(float)

    def _transform_feature(self, series: pd.Series, mode: str) -> pd.Series:
        numeric = pd.to_numeric(series, errors="coerce").astype(float)
        if mode == "pct_change":
            return numeric.pct_change().replace([float("inf"), float("-inf")], pd.NA)
        if mode == "difference":
            return numeric.diff()
        return numeric

    def _clean_feature(self, series: pd.Series) -> pd.Series:
        numeric = pd.to_numeric(series, errors="coerce").astype(float)
        winsorize = float(self.DEFAULT_CLEANING["winsorize_zscore"])
        zscore = self._zscore(numeric)
        upper = numeric.mean() + numeric.std() * winsorize
        lower = numeric.mean() - numeric.std() * winsorize
        return numeric.mask(zscore > winsorize, upper).mask(zscore < -winsorize, lower)

    def _build_lag_profile(self, feature: pd.Series, target: pd.Series, max_lag_bars: int) -> list[dict[str, Any]]:
        return [
            {"lag": lag, "correlation": self._safe_corr(feature, target.shift(-lag))}
            for lag in range(max_lag_bars + 1)
        ]

    def _build_rolling_corr(self, timestamps: pd.Series, feature: pd.Series, target: pd.Series) -> list[dict[str, Any]]:
        window = max(20, min(self.DEFAULT_CLEANING["rolling_ic_window"], len(feature) // 3))
        if len(feature) < window:
            return []
        frame = pd.DataFrame({"timestamp": timestamps, "feature": feature, "target": target}).dropna()
        rolling = frame["feature"].rolling(window).corr(frame["target"]).dropna()
        result = []
        for index, value in rolling.items():
            ts = frame.loc[index, "timestamp"]
            result.append({"date": ts.isoformat(), "value": self._to_float(value)})
        return result

    def _rolling_stability(self, overall_corr: float, rolling: list[dict[str, Any]]) -> float:
        if not rolling or overall_corr == 0:
            return 0.0
        same_direction = sum(1 for item in rolling if self._sign(item["value"]) == self._sign(overall_corr))
        return round(same_direction / len(rolling), 4)

    def _build_quantiles(self, feature: pd.Series, target: pd.Series) -> list[dict[str, Any]]:
        quantile_frame = pd.DataFrame({"feature": feature, "target": target}).dropna()
        if len(quantile_frame) < self.DEFAULT_CLEANING["min_sample_size"]:
            return []
        try:
            quantile_frame["bucket"] = pd.qcut(
                quantile_frame["feature"],
                q=int(self.DEFAULT_CLEANING["bucket_count"]),
                labels=False,
                duplicates="drop",
            )
        except ValueError:
            return []
        max_bucket = quantile_frame["bucket"].max()
        if pd.isna(max_bucket):
            return []
        result = []
        total_buckets = int(max_bucket) + 1
        for bucket in range(total_buckets):
            sliced = quantile_frame.loc[quantile_frame["bucket"] == bucket]
            if sliced.empty:
                continue
            result.append(
                {
                    "bucket": bucket + 1,
                    "label": f"Q{bucket + 1}",
                    "avg_future_return": self._to_float(sliced["target"].mean()),
                    "count": int(len(sliced)),
                }
            )
        return result

    def _build_normalized_series(
        self,
        frame: pd.DataFrame,
        *,
        feature_column: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        sliced = frame.tail(limit).copy()
        if sliced.empty:
            return []
        sliced["price_z"] = self._zscore(sliced["close"])
        sliced["factor_z"] = self._zscore(sliced[feature_column])
        return [
            {
                "date": row.timestamp.isoformat(),
                "price_z": self._to_float(row.price_z),
                "factor_z": self._to_float(row.factor_z),
                "future_return": self._to_float(row.future_return),
            }
            for row in sliced.itertuples(index=False)
        ]

    def _bucket_turnover(self, feature: pd.Series) -> float:
        turnover_frame = pd.DataFrame({"feature": feature}).dropna()
        if len(turnover_frame) < self.DEFAULT_CLEANING["min_sample_size"]:
            return 0.0
        try:
            turnover_frame["bucket"] = pd.qcut(
                turnover_frame["feature"],
                q=int(self.DEFAULT_CLEANING["bucket_count"]),
                labels=False,
                duplicates="drop",
            )
        except ValueError:
            return 0.0
        changed = turnover_frame["bucket"].ne(turnover_frame["bucket"].shift(1))
        if len(changed) <= 1:
            return 0.0
        return self._to_float(changed.iloc[1:].mean())

    def _score_factor(
        self,
        *,
        correlation: float,
        rank_correlation: float,
        best_lag_correlation: float,
        stability: float,
        quantile_spread: float,
        turnover: float,
        ic_ir: float,
    ) -> float:
        score = 0.0
        score += min(abs(correlation) / 0.2, 1.0) * 25
        score += min(abs(rank_correlation) / 0.2, 1.0) * 10
        score += min(abs(best_lag_correlation) / 0.2, 1.0) * 15
        score += min(stability / 0.75, 1.0) * 18
        score += min(abs(quantile_spread) / 0.05, 1.0) * 12
        score += min(abs(ic_ir) / 1.5, 1.0) * 10
        score += max(0.0, 1 - min(turnover / 0.75, 1.0)) * 10
        return round(score, 2)

    def _meta_to_factor(self, meta: Any) -> FactorDefinition:
        indicator_id = meta["id"]
        mode = "level" if indicator_id in self.LEVEL_FACTOR_IDS else "pct_change"
        return FactorDefinition(
            factor_id=indicator_id,
            name=meta["name"],
            category=meta["category"],
            source="indicator",
            unit=meta["unit"],
            feature_mode=mode,
            description=meta.get("description"),
        )

    def _serialize_factor(self, definition: FactorDefinition) -> dict[str, Any]:
        return {
            "factor_id": definition.factor_id,
            "name": definition.name,
            "category": definition.category,
            "source": definition.source,
            "unit": definition.unit,
            "feature_mode": definition.feature_mode,
            "description": definition.description,
        }

    def _dataset_signature(
        self,
        *,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
        primary_horizon: int,
        forward_horizons: list[int],
        categories: list[str],
        factor_ids: list[str],
        cleaning: dict[str, Any],
    ) -> str:
        payload = {
            "schema_version": self.DATASET_SCHEMA_VERSION,
            "symbol": symbol,
            "timeframe": timeframe,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "primary_horizon": primary_horizon,
            "forward_horizons": list(forward_horizons),
            "categories": sorted(set(categories)),
            "factor_ids": sorted(set(factor_ids)),
            "cleaning": cleaning,
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()

    def _safe_corr(self, left: pd.Series, right: pd.Series) -> float:
        aligned = pd.concat([left, right], axis=1).dropna()
        if len(aligned) < 10:
            return 0.0
        if aligned.iloc[:, 0].nunique() <= 1 or aligned.iloc[:, 1].nunique() <= 1:
            return 0.0
        value = aligned.iloc[:, 0].corr(aligned.iloc[:, 1])
        return self._to_float(value)

    def _hit_rate(self, feature: pd.Series, target: pd.Series) -> float:
        aligned = pd.concat([feature, target], axis=1).dropna()
        if aligned.empty:
            return 0.0
        return self._to_float((aligned.iloc[:, 0].apply(self._sign) == aligned.iloc[:, 1].apply(self._sign)).mean())

    def _information_ratio(self, rolling: list[dict[str, Any]]) -> float:
        if not rolling:
            return 0.0
        values = pd.Series([item["value"] for item in rolling]).dropna()
        std = values.std()
        if std is None or pd.isna(std) or std == 0:
            return 0.0
        return self._to_float(values.mean() / std)

    def _t_stat(self, rolling: list[dict[str, Any]]) -> float:
        if not rolling:
            return 0.0
        values = pd.Series([item["value"] for item in rolling]).dropna()
        if len(values) < 2:
            return 0.0
        std = values.std()
        if std is None or pd.isna(std) or std == 0:
            return 0.0
        return self._to_float(values.mean() / (std / math.sqrt(len(values))))

    def _quantile_spread(self, quantiles: list[dict[str, Any]]) -> float:
        if len(quantiles) < 2:
            return 0.0
        return self._to_float(quantiles[-1]["avg_future_return"] - quantiles[0]["avg_future_return"])

    def _zscore(self, series: pd.Series) -> pd.Series:
        numeric = pd.to_numeric(series, errors="coerce").astype(float)
        std = numeric.std()
        if std is None or pd.isna(std) or std == 0:
            return pd.Series([0.0] * len(numeric), index=numeric.index)
        return (numeric - numeric.mean()) / std

    def _aligned_series(self, source_index: pd.Series, source_series: pd.Series, target_index: pd.Series) -> pd.Series:
        index = pd.Index(source_index)
        series = pd.Series(source_series.values, index=index)
        aligned = series.reindex(index.union(pd.Index(target_index))).sort_index().ffill().reindex(pd.Index(target_index))
        return aligned

    def _timeframe_delta(self, timeframe: str) -> timedelta:
        value = int(timeframe[:-1])
        unit = timeframe[-1]
        if unit == "m":
            return timedelta(minutes=value)
        if unit == "h":
            return timedelta(hours=value)
        if unit == "d":
            return timedelta(days=value)
        raise ValueError(f"暂不支持的时间周期: {timeframe}")

    def _sign(self, value: float | int | None) -> int:
        if value is None:
            return 0
        if value > 0:
            return 1
        if value < 0:
            return -1
        return 0

    def _to_optional_float(self, value: Any) -> float | None:
        try:
            if pd.isna(value):
                return None
        except TypeError:
            pass
        numeric = float(value)
        if not math.isfinite(numeric):
            return None
        return round(numeric, 6)

    def _to_float(self, value: Any) -> float:
        optional = self._to_optional_float(value)
        return optional if optional is not None else 0.0
