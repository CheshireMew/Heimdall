from __future__ import annotations

import pandas as pd
import pytest
from sqlalchemy import create_engine

import app.infra.db.database as db_module
from app.infra.db.schema import Base, StrategyDefinition, StrategyVersion
from app.schemas.backtest import StrategyDefinitionResponse, StrategyVersionResponse
from app.schemas.strategy_contract import StrategyTemplateConfigResponse
from app.services.backtest.strategy_catalog import get_template_spec
from app.services.backtest.strategy_contract import (
    blank_strategy_config,
    build_condition,
    build_group,
    normalize_strategy_config,
)
from app.services.backtest.strategy_query_service import StrategyQueryService
from app.services.backtest.strategy_support import (
    build_strategy_version_response_payload,
)
from app.services.backtest.strategy_runtime import StrategyRuntime
from config.settings import AppSettings


def test_normalize_strategy_config_does_not_migrate_old_entry_exit_shape():
    old_shape_config = {
        "indicators": {
            "ema": {"label": "EMA", "type": "ema", "params": {"period": 20}},
        },
        "entry": build_group(
            "entry_root",
            "入场条件组",
            "and",
            [
                build_condition(
                    "legacy_entry",
                    "旧版入场",
                    {"kind": "price", "field": "close"},
                    "gt",
                    {"kind": "value", "value": 100},
                )
            ],
        ),
        "exit": build_group(
            "exit_root",
            "离场条件组",
            "or",
            [
                build_condition(
                    "legacy_exit",
                    "旧版离场",
                    {"kind": "price", "field": "close"},
                    "lt",
                    {"kind": "value", "value": 95},
                )
            ],
        ),
        "risk": {"stoploss": -0.05},
    }

    normalized = normalize_strategy_config(old_shape_config, blank_strategy_config())

    assert normalized["regime_priority"] == ["trend", "range"]
    assert normalized["trend"]["enabled"] is True
    assert normalized["range"]["enabled"] is False
    assert normalized["execution"]["market_type"] == "spot"
    assert normalized["execution"]["direction"] == "long_only"
    assert normalized["trend"]["long_entry"]["children"] == []
    assert normalized["trend"]["long_exit"]["children"] == []
    assert normalized["range"]["long_entry"]["children"] == []
    assert normalized["range"]["long_exit"]["children"] == []
    assert normalized["trend"]["short_entry"]["enabled"] is False
    assert normalized["trend"]["short_exit"]["enabled"] is False


def test_resolve_branch_masks_gives_trend_priority_over_range():
    runtime = StrategyRuntime()
    frame = pd.DataFrame(
        {
            "close": [98.0, 104.0, 106.0],
            "volume": [1.0, 1.0, 1.0],
        }
    )
    config = {
        "regime_priority": ["trend", "range"],
        "trend": {
            "enabled": True,
            "regime": build_group(
                "trend_regime",
                "趋势状态",
                "and",
                [
                    build_condition(
                        "trend_close_gt_100",
                        "价格高于 100",
                        {"kind": "price", "field": "close"},
                        "gt",
                        {"kind": "value", "value": 100},
                    )
                ],
            ),
            "long_entry": build_group("trend_long_entry", "趋势做多入场", "and", []),
            "long_exit": build_group("trend_long_exit", "趋势做多离场", "or", []),
            "short_entry": build_group(
                "trend_short_entry", "趋势做空入场", "and", [], enabled=False
            ),
            "short_exit": build_group(
                "trend_short_exit", "趋势做空离场", "or", [], enabled=False
            ),
        },
        "range": {
            "enabled": True,
            "regime": build_group("range_regime", "区间状态", "and", []),
            "long_entry": build_group("range_long_entry", "区间做多入场", "and", []),
            "long_exit": build_group("range_long_exit", "区间做多离场", "or", []),
            "short_entry": build_group(
                "range_short_entry", "区间做空入场", "and", [], enabled=False
            ),
            "short_exit": build_group(
                "range_short_exit", "区间做空离场", "or", [], enabled=False
            ),
        },
    }

    masks = runtime._resolve_branch_masks(frame, config)

    assert masks["trend"].tolist() == [False, True, True]
    assert masks["range"].tolist() == [True, False, False]


def test_btc_regime_switch_uses_mep_state_sources_on_multitimeframe_frame():
    runtime = StrategyRuntime()
    template = get_template_spec("btc_regime_switch")
    candles: list[list[float]] = []
    base_timestamp = 1_710_000_000_000
    price = 100.0
    for index in range(420):
        drift = 0.45 if index < 320 else 0.05
        open_price = price
        close_price = price + drift
        high_price = close_price + 0.2
        low_price = open_price - 0.2
        volume = 1_000.0 + index
        candles.append(
            [
                base_timestamp + index * 300_000,
                open_price,
                high_price,
                low_price,
                close_price,
                volume,
            ]
        )
        price = close_price

    frame = runtime.build_frame(
        "btc_regime_switch", template["default_config"], candles, "5m"
    )

    assert "m_1h__value" in frame.columns
    assert "e_1h__value" in frame.columns
    assert "range_15m__position" in frame.columns
    assert "range_15m__width_ratio" in frame.columns
    assert frame["active_regime"].eq("trend").any()


def test_runtime_supports_shifted_price_and_indicator_sources():
    runtime = StrategyRuntime()
    candles = [
        [1_710_000_000_000, 100.0, 101.0, 99.0, 100.5, 1000.0],
        [1_710_000_300_000, 100.5, 101.5, 98.5, 99.5, 1100.0],
        [1_710_000_600_000, 99.5, 100.8, 99.2, 100.6, 1200.0],
        [1_710_000_900_000, 100.6, 101.4, 100.2, 101.2, 1300.0],
    ]
    config = {
        "indicators": {
            "ema_fast": {
                "label": "EMA",
                "type": "ema",
                "timeframe": "base",
                "params": {"period": 2},
            },
        },
        "execution": {"market_type": "spot", "direction": "long_only"},
        "regime_priority": ["trend", "range"],
        "trend": {
            "id": "trend",
            "label": "Trend",
            "enabled": True,
            "regime": build_group("trend_regime", "趋势状态", "and", []),
            "long_entry": build_group(
                "trend_long_entry",
                "趋势做多入场",
                "and",
                [
                    build_condition(
                        "prev_low_break",
                        "上一根 low 小于 99",
                        {"kind": "price", "field": "low", "bars_ago": 1},
                        "lt",
                        {"kind": "value", "value": 99.0},
                    ),
                    build_condition(
                        "ema_turn_up",
                        "当前 EMA 大于上一根 EMA",
                        {
                            "kind": "indicator",
                            "indicator": "ema_fast",
                            "output": "value",
                        },
                        "gt",
                        {
                            "kind": "indicator",
                            "indicator": "ema_fast",
                            "output": "value",
                            "bars_ago": 1,
                        },
                    ),
                ],
            ),
            "long_exit": build_group("trend_long_exit", "趋势做多离场", "or", []),
            "short_entry": build_group(
                "trend_short_entry", "趋势做空入场", "and", [], enabled=False
            ),
            "short_exit": build_group(
                "trend_short_exit", "趋势做空离场", "or", [], enabled=False
            ),
        },
        "range": {
            "id": "range",
            "label": "Range",
            "enabled": False,
            "regime": build_group("range_regime", "区间状态", "and", []),
            "long_entry": build_group("range_long_entry", "区间做多入场", "and", []),
            "long_exit": build_group("range_long_exit", "区间做多离场", "or", []),
            "short_entry": build_group(
                "range_short_entry", "区间做空入场", "and", [], enabled=False
            ),
            "short_exit": build_group(
                "range_short_exit", "区间做空离场", "or", [], enabled=False
            ),
        },
        "risk": {
            "stoploss": -0.05,
            "roi_targets": [],
            "trailing": {
                "enabled": False,
                "positive": 0.02,
                "offset": 0.03,
                "only_offset_reached": True,
            },
            "partial_exits": [],
        },
    }

    frame = runtime.build_frame("ema_rsi_macd", config, candles, "5m")

    assert bool(frame.iloc[2]["long_entry_signal"]) is True


def test_strategy_query_service_returns_api_records_after_session_close(monkeypatch):
    original_runtime = db_module.get_database_runtime()
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    runtime = db_module.create_database_runtime(AppSettings(DATABASE_URL="sqlite:///:memory:"))
    runtime.dispose()
    runtime.engine = engine
    runtime.session_factory.configure(bind=engine)
    db_module.configure_database_runtime(runtime)

    with db_module.session_scope() as session:
        session.add(
            StrategyDefinition(
                key="custom_trend",
                name="Custom Trend",
                template="ema_rsi_macd",
                category="trend",
                description="Custom",
                is_active=True,
            )
        )
        session.add(
            StrategyVersion(
                strategy_key="custom_trend",
                version=2,
                name="Custom Trend v2",
                config=blank_strategy_config(),
                parameter_space={},
                notes="Stable",
                is_default=True,
            )
        )

    service = StrategyQueryService()
    strategies = service.list_strategies()
    for strategy in strategies:
        StrategyDefinitionResponse.model_validate(strategy)

    record = service.get_strategy_version("custom_trend")
    payload = build_strategy_version_response_payload(record)

    assert payload["runtime"]["preferred_run_timeframe"]
    StrategyVersionResponse.model_validate(payload)
    db_module.configure_database_runtime(original_runtime)
    engine.dispose()


def test_strategy_contract_keeps_trade_plan_at_api_boundary():
    payload = StrategyTemplateConfigResponse.model_validate(
        blank_strategy_config()
    ).model_dump()

    assert payload["risk"]["trade_plan"]["enabled"] is False
    assert payload["risk"]["trade_plan"]["reward_multiplier"] == 2.0


def test_strategy_contract_rejects_unsafe_indicator_identifier():
    config = blank_strategy_config()
    config["indicators"] = {
        'bad"] = 1 #': {"label": "Bad", "type": "ema", "params": {"period": 20}}
    }

    with pytest.raises(ValueError, match="指标标识"):
        normalize_strategy_config(config, blank_strategy_config())
