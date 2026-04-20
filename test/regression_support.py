from __future__ import annotations

from copy import deepcopy

from app.services.backtest.run_form_contract import backtest_run_defaults
from app.schemas.market import (
    build_market_history_response,
    build_ohlcv_points,
)


def make_kline_data() -> list[list[float]]:
    return [
        [1710000000000, 100.0, 110.0, 95.0, 108.0, 1000.0],
        [1710003600000, 108.0, 112.0, 101.0, 111.0, 1200.0],
        [1710007200000, 111.0, 118.0, 109.0, 116.0, 1300.0],
    ]


def make_strategy_config() -> dict:
    return {
        "indicators": {
            "ema_fast": {
                "label": "EMA Fast",
                "type": "ema",
                "timeframe": "base",
                "params": {"period": 12},
            }
        },
        "execution": {
            "market_type": "spot",
            "direction": "long_only",
        },
        "regime_priority": ["trend", "range"],
        "trend": {
            "id": "trend",
            "label": "Trend",
            "enabled": True,
            "regime": {
                "id": "trend-regime",
                "node_type": "group",
                "label": "Trend Regime",
                "logic": "and",
                "enabled": True,
                "children": [],
            },
            "long_entry": {
                "id": "trend-long-entry",
                "node_type": "group",
                "label": "Trend Long Entry",
                "logic": "and",
                "enabled": True,
                "children": [
                    {
                        "id": "entry-condition",
                        "node_type": "condition",
                        "label": "EMA bullish",
                        "left": {"kind": "indicator", "indicator": "ema_fast", "output": "value"},
                        "operator": "gt",
                        "right": {"kind": "value", "value": 100.0},
                        "enabled": True,
                    }
                ],
            },
            "long_exit": {
                "id": "trend-long-exit",
                "node_type": "group",
                "label": "Trend Long Exit",
                "logic": "or",
                "enabled": True,
                "children": [
                    {
                        "id": "exit-condition",
                        "node_type": "condition",
                        "label": "EMA bearish",
                        "left": {"kind": "indicator", "indicator": "ema_fast", "output": "value"},
                        "operator": "lt",
                        "right": {"kind": "value", "value": 95.0},
                        "enabled": True,
                    }
                ],
            },
            "short_entry": {
                "id": "trend-short-entry",
                "node_type": "group",
                "label": "Trend Short Entry",
                "logic": "and",
                "enabled": False,
                "children": [],
            },
            "short_exit": {
                "id": "trend-short-exit",
                "node_type": "group",
                "label": "Trend Short Exit",
                "logic": "or",
                "enabled": False,
                "children": [],
            },
        },
        "range": {
            "id": "range",
            "label": "Range",
            "enabled": False,
            "regime": {
                "id": "range-regime",
                "node_type": "group",
                "label": "Range Regime",
                "logic": "and",
                "enabled": True,
                "children": [],
            },
            "long_entry": {
                "id": "range-long-entry",
                "node_type": "group",
                "label": "Range Long Entry",
                "logic": "and",
                "enabled": True,
                "children": [],
            },
            "long_exit": {
                "id": "range-long-exit",
                "node_type": "group",
                "label": "Range Long Exit",
                "logic": "or",
                "enabled": True,
                "children": [],
            },
            "short_entry": {
                "id": "range-short-entry",
                "node_type": "group",
                "label": "Range Short Entry",
                "logic": "and",
                "enabled": False,
                "children": [],
            },
            "short_exit": {
                "id": "range-short-exit",
                "node_type": "group",
                "label": "Range Short Exit",
                "logic": "or",
                "enabled": False,
                "children": [],
            },
        },
        "risk": {
            "stoploss": -0.08,
            "roi_targets": [
                {"id": "roi-1", "minutes": 60, "profit": 0.03, "enabled": True}
            ],
            "trailing": {
                "enabled": True,
                "positive": 0.01,
                "offset": 0.02,
                "only_offset_reached": True,
            },
            "partial_exits": [
                {"id": "px-1", "profit": 0.05, "size_pct": 50.0, "enabled": True}
            ],
        },
    }


def make_indicator_registry_item() -> dict:
    return {
        "key": "ema_fast",
        "engine": "ema",
        "name": "EMA Fast",
        "description": "Fast EMA indicator",
        "outputs": [{"key": "value", "label": "Value"}],
        "params": [
            {
                "key": "period",
                "label": "Period",
                "type": "int",
                "default": 12,
                "min": 1,
                "max": 200,
                "step": 1,
            }
        ],
        "is_builtin": True,
    }


def make_indicator_engine_item() -> dict:
    item = make_indicator_registry_item()
    item["engine"] = "builtin.ema"
    return item


def make_editor_contract() -> dict:
    return {
        "operators": [{"key": "gt", "label": "Greater Than"}],
        "group_logics": [{"key": "and", "label": "All"}],
        "timeframe_options": [
            {"key": "base", "label": "Base"},
            {"key": "1h", "label": "1 Hour"},
            {"key": "4h", "label": "4 Hours"},
            {"key": "1d", "label": "1 Day"},
        ],
        "market_type_options": [{"key": "spot", "label": "Spot"}],
        "direction_options": [{"key": "long_only", "label": "Long Only"}],
        "blank_condition": {
            "id": "blank-condition",
            "node_type": "condition",
            "label": "Condition",
            "left": {"kind": "indicator", "indicator": "ema_fast", "output": "value"},
            "operator": "gt",
            "right": {"kind": "value", "value": 0.0},
            "enabled": True,
        },
        "blank_group": {
            "id": "blank-group",
            "node_type": "group",
            "label": "Group",
            "logic": "and",
            "enabled": True,
            "children": [],
        },
        "blank_config": make_strategy_config(),
        "run_defaults": {
            **backtest_run_defaults(),
            "optimize_metric_options": [
                {"key": "sharpe", "label": "Sharpe"},
                {"key": "profit_pct", "label": "Profit %"},
            ],
        },
    }


def make_template_response() -> dict:
    return {
        "template": "trend_following",
        "name": "Trend Following",
        "category": "trend",
        "description": "Template for trend strategies",
        "is_builtin": True,
        "template_runtime": {
            "builder_kind": "rules",
            "capabilities": {
                "signal_runtime": True,
                "paper": True,
                "version_editing": True,
            },
        },
        "indicator_keys": ["ema_fast"],
        "indicator_registry": [make_indicator_registry_item()],
        "operators": [{"key": "gt", "label": "Greater Than"}],
        "group_logics": [{"key": "and", "label": "All"}],
        "default_config": make_strategy_config(),
        "default_parameter_space": {"indicators.ema_fast.params.period": [9, 12, 20]},
    }


def make_strategy_version(version: int = 2, *, is_default: bool = True) -> dict:
    return {
        "id": version,
        "version": version,
        "name": f"Strategy v{version}",
        "notes": "Stable release",
        "is_default": is_default,
        "config": make_strategy_config(),
        "parameter_space": {"indicators.ema_fast.params.period": [9, 12, 20]},
        "runtime": {
            "indicator_timeframes": [],
            "allowed_run_timeframes": ["1h", "4h", "1d"],
            "preferred_run_timeframe": "1h",
        },
    }


def make_strategy_definition() -> dict:
    return {
        "key": "ema_rsi_macd",
        "name": "EMA RSI MACD",
        "template": "trend_following",
        "category": "trend",
        "description": "Momentum strategy",
        "is_active": True,
        "template_runtime": {
            "builder_kind": "rules",
            "capabilities": {
                "signal_runtime": True,
                "paper": True,
                "version_editing": True,
            },
        },
        "versions": [make_strategy_version()],
    }


def make_backtest_report() -> dict:
    return {
        "initial_cash": 100000.0,
        "final_balance": 112500.0,
        "profit_abs": 12500.0,
        "profit_pct": 12.5,
        "annualized_return_pct": 18.0,
        "max_drawdown_pct": -6.4,
        "sharpe": 1.8,
        "sortino": 2.1,
        "calmar": 2.4,
        "profit_factor": 1.9,
        "expectancy_ratio": 1.2,
        "win_rate": 58.0,
        "total_trades": 14,
        "wins": 8,
        "losses": 5,
        "draws": 1,
        "avg_trade_pct": 1.2,
        "avg_trade_duration_minutes": 180,
        "best_trade_pct": 7.5,
        "worst_trade_pct": -3.4,
        "pair_breakdown": [
            {
                "pair": "BTC/USDT",
                "trades": 9,
                "profit_abs": 8600.0,
                "profit_pct": 8.6,
                "win_rate": 55.6,
            }
        ],
        "symbols": ["BTC/USDT", "ETH/USDT"],
        "timeframe": "1h",
        "strategy": {
            "key": "ema_rsi_macd",
            "name": "EMA RSI MACD",
            "version": 2,
            "template": "trend_following",
        },
        "portfolio": {
            "symbols": ["BTC/USDT", "ETH/USDT"],
            "max_open_trades": 2,
            "position_size_pct": 25.0,
            "stake_mode": "fixed",
            "stake_currency": "USDT",
        },
        "research": {
            "selected_config": {"ema_fast.period": 12},
            "in_sample_ratio": 70.0,
            "slippage_bps": 5.0,
            "funding_rate_daily": 0.0,
            "optimization": {
                "metric": "sharpe",
                "trial_count": 2,
                "best_score": 1.8,
                "best_config": {"ema_fast.period": 12},
                "trials": [
                    {
                        "trial": 1,
                        "score": 1.6,
                        "config": {"ema_fast.period": 9},
                        "report": {"profit_pct": 9.2, "profit_abs": 9200.0},
                    },
                    {
                        "trial": 2,
                        "score": 1.8,
                        "config": {"ema_fast.period": 12},
                        "report": {"profit_pct": 12.5, "profit_abs": 12500.0},
                    },
                ],
            },
            "in_sample": {
                "range": {"start": "2025-01-01", "end": "2025-04-30"},
                "config": {"ema_fast.period": 12},
                "report": {"profit_pct": 13.4, "profit_abs": 13400.0},
            },
            "out_of_sample": {
                "range": {"start": "2025-05-01", "end": "2025-06-30"},
                "config": {"ema_fast.period": 12},
                "report": {"profit_pct": 4.1, "profit_abs": 4100.0},
            },
            "rolling_windows": [
                {
                    "index": 1,
                    "train": {"start": "2025-01-01", "end": "2025-03-31"},
                    "test": {"start": "2025-04-01", "end": "2025-04-30"},
                    "config": {"ema_fast.period": 12},
                    "optimization": {
                        "metric": "sharpe",
                        "trial_count": 1,
                        "best_score": 1.5,
                        "best_config": {"ema_fast.period": 12},
                        "trials": [],
                    },
                    "report": {"profit_pct": 2.0, "profit_abs": 2000.0},
                }
            ],
        },
    }


def make_backtest_metadata() -> dict:
    return {
        "schema_version": 4,
        "execution_mode": "backtest",
        "engine": "Freqtrade",
        "exchange": "binance",
        "strategy_key": "ema_rsi_macd",
        "strategy_name": "EMA RSI MACD",
        "strategy_version": 2,
        "strategy_template": "trend_following",
        "strategy_notes": "Stable release",
        "symbols": ["BTC/USDT", "ETH/USDT"],
        "portfolio_label": "BTC/USDT, ETH/USDT",
        "initial_cash": 100000.0,
        "fee_rate": 0.1,
        "fee_ratio": 0.001,
        "timeframe": "1h",
        "stake_currency": "USDT",
        "portfolio": {
            "symbols": ["BTC/USDT", "ETH/USDT"],
            "max_open_trades": 2,
            "position_size_pct": 25.0,
            "stake_mode": "fixed",
        },
        "research": {
            "slippage_bps": 5.0,
            "funding_rate_daily": 0.0,
            "in_sample_ratio": 70.0,
            "optimize_metric": "sharpe",
            "optimize_trials": 12,
            "rolling_windows": 3,
        },
        "selected_config": {"ema_fast.period": 12},
        "sample_ranges": {
            "requested": {"start": "2025-01-01", "end": "2025-06-30"},
            "displayed": {"start": "2025-01-01", "end": "2025-06-30"},
            "in_sample": {"start": "2025-01-01", "end": "2025-04-30"},
            "out_of_sample": {"start": "2025-05-01", "end": "2025-06-30"},
        },
        "runtime_state": {
            "cash_balance": 90000.0,
            "last_processed": {"BTC/USDT": 1710007200000},
            "last_synced_end": 1710007200000,
            "positions": {
                "BTC/USDT": {
                    "symbol": "BTC/USDT",
                    "side": "long",
                    "opened_at": "2025-06-01T00:00:00",
                    "entry_price": 100.0,
                    "remaining_amount": 0.5,
                    "remaining_cost": 50.0,
                    "highest_price": 118.0,
                    "lowest_price": 96.0,
                    "last_price": 116.0,
                    "taken_partial_ids": ["px-1"],
                }
            },
        },
        "paper_live": {
            "cash_balance": 90000.0,
            "open_positions": 1,
            "positions": [
                {
                    "symbol": "BTC/USDT",
                    "side": "long",
                    "opened_at": "2025-06-01T00:00:00",
                    "entry_price": 100.0,
                    "remaining_amount": 0.5,
                    "remaining_cost": 50.0,
                    "highest_price": 118.0,
                    "lowest_price": 96.0,
                    "last_price": 116.0,
                    "taken_partial_ids": ["px-1"],
                }
            ],
            "last_updated": "2025-06-01T12:00:00",
            "stop_reason": None,
        },
        "report": make_backtest_report(),
        "raw_stats": {
            "profit_pct": 12.5,
            "profit_abs": 12500.0,
            "final_balance": 112500.0,
            "max_drawdown_pct": -6.4,
            "sharpe": 1.8,
            "calmar": 2.4,
            "profit_factor": 1.9,
            "win_rate": 58.0,
            "total_trades": 14,
        },
        "error": None,
    }


def make_backtest_run(run_id: int = 101, *, execution_mode: str = "backtest") -> dict:
    metadata = make_backtest_metadata()
    metadata["execution_mode"] = execution_mode
    if execution_mode == "paper_live":
        metadata["engine"] = "FreqtradePaper"
    return {
        "id": run_id,
        "symbol": "BTC/USDT",
        "timeframe": "1h",
        "start_date": "2025-01-01T00:00:00",
        "end_date": "2025-06-30T00:00:00",
        "status": "completed" if execution_mode == "backtest" else "running",
        "metadata": metadata,
        "report": make_backtest_report(),
        "created_at": "2025-07-01T00:00:00",
        "metrics": {
            "total_candles": 1000,
            "total_signals": 20,
            "buy_signals": 10,
            "sell_signals": 8,
            "hold_signals": 2,
        },
        "signals": [
            {
                "id": 1,
                "timestamp": "2025-06-01T00:00:00",
                "price": 100.0,
                "signal": "BUY",
                "confidence": 0.87,
                "indicators": {"ema": 102.0},
                "reasoning": "Trend confirmed",
            }
        ],
    }


def make_backtest_detail(run_id: int = 101, *, execution_mode: str = "backtest") -> dict:
    detail = make_backtest_run(run_id=run_id, execution_mode=execution_mode)
    detail["trades"] = [
        {
            "id": 1,
            "pair": "BTC/USDT",
            "opened_at": "2025-06-01T00:00:00",
            "closed_at": "2025-06-01T04:00:00",
            "entry_price": 100.0,
            "exit_price": 108.0,
            "stake_amount": 1000.0,
            "amount": 10.0,
            "profit_abs": 80.0,
            "profit_pct": 8.0,
            "max_drawdown_pct": -1.5,
            "duration_minutes": 240,
            "entry_tag": "trend",
            "exit_reason": "target",
            "leverage": 1.0,
        }
    ]
    detail["equity_curve"] = [
        {
            "id": 1,
            "timestamp": "2025-06-01T00:00:00",
            "equity": 100000.0,
            "pnl_abs": 0.0,
            "drawdown_pct": 0.0,
        },
        {
            "id": 2,
            "timestamp": "2025-06-01T04:00:00",
            "equity": 100080.0,
            "pnl_abs": 80.0,
            "drawdown_pct": -0.1,
        },
    ]
    detail["pagination"] = {
        "page": 1,
        "page_size": 100,
        "total": 1,
        "total_pages": 1,
    }
    return detail


def make_market_realtime_response() -> dict:
    return {
        "symbol": "BTC/USDT",
        "timestamp": "2025-06-01T12:00:00",
        "current_price": 116.0,
        "indicators": {
            "ema": 110.5,
            "rsi": 61.2,
            "macd": {"dif": 1.2, "dea": 0.8, "histogram": 0.4},
            "atr": 5.3,
            "atr_pct": 0.045,
            "realized_volatility_pct": 0.13,
            "annualized_volatility_pct": 0.44,
        },
        "ai_analysis": {"signal": "BUY", "confidence": 78},
        "kline_data": [item.model_dump() for item in build_ohlcv_points(make_kline_data())],
        "timeframe": "1h",
        "type": "snapshot",
    }


def make_market_indicator() -> dict:
    return {
        "indicator_id": "FEAR_GREED",
        "name": "Fear & Greed",
        "category": "Sentiment",
        "unit": "index",
        "current_value": 72.0,
        "last_updated": "2025-06-01T12:00:00",
        "history": [{"date": "2025-05-31", "value": 68.0}],
    }


def make_funding_rate_snapshot() -> dict:
    return {
        "exchange": "binance",
        "market_type": "perpetual",
        "symbol": "BTCUSDT",
        "funding_rate": 0.0001,
        "funding_rate_pct": 0.01,
        "mark_price": 68000.0,
        "index_price": 67980.0,
        "interest_rate": 0.0003,
        "next_funding_time": "2025-06-01T16:00:00",
        "collected_at": "2025-06-01T12:00:00",
    }


def make_funding_rate_history() -> dict:
    return {
        "exchange": "binance",
        "market_type": "perpetual",
        "symbol": "BTCUSDT",
        "count": 1,
        "items": [
            {
                "funding_time": "2025-06-01T08:00:00",
                "funding_rate": 0.0001,
                "funding_rate_pct": 0.01,
                "mark_price": 67500.0,
            }
        ],
    }


def make_funding_rate_sync_response() -> dict:
    return {
        "exchange": "binance",
        "market_type": "perpetual",
        "symbol": "BTCUSDT",
        "fetched": 50,
        "inserted": 50,
        "total": 50,
        "start_date": "2025-01-01",
        "end_date": "2025-01-10",
    }


def make_binance_breakout_monitor_response() -> dict:
    return {
        "exchange": "binance",
        "min_rise_pct": 5.0,
        "quote_asset": "USDT",
        "updated_at": 1717243200000,
        "summary": {
            "monitored_count": 2,
            "natural_count": 2,
            "momentum_count": 1,
            "focus_count": 1,
            "advancing_count": 1,
            "spot_count": 1,
            "contract_count": 1,
        },
        "items": [
            {
                "market": "spot",
                "market_label": "现货",
                "symbol": "DOGEUSDT",
                "last_price": 0.164,
                "mark_price": None,
                "price_change_pct": 8.6,
                "quote_volume": 310000000.0,
                "funding_rate_pct": None,
                "change_15m_pct": 0.9,
                "change_1h_pct": 2.3,
                "change_4h_pct": 5.7,
                "pullback_from_high_pct": -1.1,
                "range_position_pct": 88.0,
                "ema20_gap_15m_pct": 1.8,
                "ema20_gap_1h_pct": 4.2,
                "rsi_15m": 63.0,
                "rsi_1h": 66.0,
                "macd_hist_15m": 0.004,
                "green_ratio_15m_pct": 66.0,
                "natural_score": 82,
                "momentum_score": 84,
                "structure_ok": True,
                "momentum_ok": True,
                "follow_status": "继续上行",
                "verdict": "优先关注",
                "reasons": ["离高点不远，回撤不深", "15 分钟仍站在均线之上"],
            },
            {
                "market": "usdm",
                "market_label": "U 本位",
                "symbol": "SUIUSDT",
                "last_price": 1.82,
                "mark_price": 1.81,
                "price_change_pct": 6.2,
                "quote_volume": 180000000.0,
                "funding_rate_pct": 0.012,
                "change_15m_pct": -0.2,
                "change_1h_pct": 0.5,
                "change_4h_pct": 3.1,
                "pullback_from_high_pct": -2.9,
                "range_position_pct": 71.0,
                "ema20_gap_15m_pct": 0.5,
                "ema20_gap_1h_pct": 2.1,
                "rsi_15m": 57.0,
                "rsi_1h": 59.0,
                "macd_hist_15m": 0.001,
                "green_ratio_15m_pct": 58.0,
                "natural_score": 71,
                "momentum_score": 62,
                "structure_ok": True,
                "momentum_ok": False,
                "follow_status": "高位蓄势",
                "verdict": "继续跟踪",
                "reasons": ["价格仍压在强势区间上沿"],
            },
        ],
    }


def make_technical_metrics_response() -> dict:
    return {
        "symbol": "BTC/USDT",
        "timeframe": "1d",
        "sample_size": 120,
        "current_price": 68000.0,
        "atr": 2100.0,
        "atr_pct": 0.03,
        "realized_volatility_pct": 0.14,
        "annualized_volatility_pct": 0.48,
    }


def make_trade_setup_response() -> dict:
    return {
        "symbol": "BTC/USDT",
        "timeframe": "1h",
        "timestamp": "2025-06-01T12:00:00",
        "current_price": 116.0,
        "setup": {
            "side": "long",
            "entry": 116.0,
            "target": 126.6,
            "stop": 110.7,
            "risk_reward": 2.0,
            "confidence": 85,
            "risk_amount": 10.0,
            "entry_time": 1710007200000,
            "style": "Scalping",
            "strategy": "最大收益",
            "source": "rules",
        },
        "reason": "做多：价格站上EMA，MACD 偏强，RSI 61.2",
        "source": "rules",
    }


def make_crypto_index_response() -> dict:
    return {
        "top_n": 20,
        "days": 90,
        "base_value": 1000.0,
        "constituents": [
            {
                "id": "bitcoin",
                "symbol": "BTC",
                "name": "Bitcoin",
                "image": None,
                "rank": 1,
                "price": 68000.0,
                "market_cap": 1_200_000_000_000.0,
                "market_cap_change_24h_pct": 1.2,
                "price_change_24h_pct": 1.6,
                "volume_24h": 30_000_000_000.0,
            }
        ],
        "history": [
            {
                "date": "2025-06-01",
                "timestamp": 1717200000000,
                "market_cap": 1_500_000_000_000.0,
                "index_value": 1142.3,
            }
        ],
        "summary": {
            "current_basket_market_cap": 1_500_000_000_000.0,
            "current_index_value": 1142.3,
            "basket_change_24h_pct": 1.4,
            "btc_weight_pct": 52.0,
            "eth_weight_pct": 18.0,
            "common_start_date": "2025-03-03",
            "methodology": "Market-cap weighted basket",
        },
        "is_partial": False,
        "resolved_constituents_count": 20,
        "missing_symbols": [],
    }


def make_factor_catalog() -> dict:
    return {
        "symbols": ["BTC/USDT"],
        "timeframes": ["1h", "4h", "1d"],
        "categories": ["macro", "sentiment"],
        "factors": [
            {
                "factor_id": "fear_greed",
                "name": "Fear & Greed",
                "category": "sentiment",
                "source": "alternative.me",
                "unit": "index",
                "feature_mode": "level",
                "description": "Sentiment indicator",
            }
        ],
        "forward_horizons": [1, 3, 5],
        "cleaning": {"winsorize": True},
    }


def make_factor_forward_metric() -> dict:
    return {
        "horizon": 3,
        "sample_size": 180,
        "target_mean": 0.012,
        "target_std": 0.08,
        "correlation": 0.24,
        "rank_correlation": 0.22,
        "ic_mean": 0.03,
        "ic_std": 0.11,
        "ic_ir": 0.27,
        "ic_t_stat": 2.1,
        "quantile_spread": 0.05,
        "hit_rate": 0.61,
    }


def make_factor_scorecard() -> dict:
    return {
        "factor_id": "fear_greed",
        "name": "Fear & Greed",
        "category": "sentiment",
        "feature_mode": "level",
        "sample_size": 180,
        "latest_value": 72.0,
        "correlation": 0.24,
        "rank_correlation": 0.22,
        "best_lag": 1,
        "best_lag_correlation": 0.28,
        "stability": 0.74,
        "quantile_spread": 0.05,
        "hit_rate": 0.61,
        "turnover": 0.12,
        "ic_ir": 0.27,
        "direction": "pro-cyclical",
        "score": 78.0,
    }


def make_factor_detail() -> dict:
    metric = make_factor_forward_metric()
    return {
        "factor_id": "fear_greed",
        "name": "Fear & Greed",
        "category": "sentiment",
        "unit": "index",
        "feature_mode": "level",
        "description": "Sentiment indicator",
        "sample_range": {"start": "2024-01-01", "end": "2025-06-01"},
        "sample_size": 180,
        "latest_raw_value": 72.0,
        "latest_feature_value": 0.72,
        "target_mean": 0.012,
        "target_std": 0.08,
        "correlation": 0.24,
        "rank_correlation": 0.22,
        "best_lag": 1,
        "best_lag_correlation": 0.28,
        "stability": 0.74,
        "quantile_spread": 0.05,
        "hit_rate": 0.61,
        "turnover": 0.12,
        "ic_mean": 0.03,
        "ic_std": 0.11,
        "ic_ir": 0.27,
        "ic_t_stat": 2.1,
        "forward_metrics": [metric],
        "lag_profile": [{"lag": 0, "correlation": 0.21}, {"lag": 1, "correlation": 0.28}],
        "rolling_correlation": [{"date": "2025-05-01", "value": 0.23}],
        "quantiles": [{"bucket": 1, "label": "Q1", "avg_future_return": -0.01, "count": 45}],
        "normalized_series": [{"date": "2025-05-01", "price_z": 0.2, "factor_z": 1.1, "future_return": 0.03}],
    }


def make_factor_blend() -> dict:
    metric = make_factor_forward_metric()
    component = {
        "factor_id": "fear_greed",
        "name": "Fear & Greed",
        "category": "sentiment",
        "score": 78.0,
        "correlation": 0.24,
        "stability": 0.74,
        "turnover": 0.12,
        "weight": 1.0,
    }
    return {
        "selected_factors": [component],
        "dropped_factors": [{"factor_id": "mvrv", "name": "MVRV", "reason": "collinear"}],
        "weights": [component],
        "forward_metrics": [metric],
        "quantiles": [{"bucket": 5, "label": "Q5", "avg_future_return": 0.04, "count": 36}],
        "normalized_series": [{"date": "2025-05-01", "price_z": 0.2, "factor_z": 1.1, "future_return": 0.03}],
        "entry_threshold": 0.8,
        "exit_threshold": 0.2,
        "score_std": 0.14,
        "score_mean": 0.52,
    }


def make_factor_research_response() -> dict:
    return {
        "run_id": 301,
        "dataset_id": 91,
        "summary": {
            "symbol": "BTC/USDT",
            "timeframe": "1d",
            "days": 365,
            "horizon_bars": 3,
            "max_lag_bars": 7,
            "factor_count": 1,
            "dataset_id": 91,
            "forward_horizons": [1, 3, 5],
            "sample_range": {"start": "2024-01-01", "end": "2025-06-01"},
            "target_label": "future_return_3",
            "blend_factor_count": 1,
        },
        "ranking": [make_factor_scorecard()],
        "details": [make_factor_detail()],
        "blend": make_factor_blend(),
    }


def make_factor_run_detail() -> dict:
    result = make_factor_research_response()
    return {
        "id": result["run_id"],
        "dataset_id": result["dataset_id"],
        "status": "completed",
        "request": {
            "symbol": "BTC/USDT",
            "timeframe": "1d",
            "days": 365,
            "horizon_bars": 3,
            "max_lag_bars": 7,
            "categories": ["sentiment"],
            "factor_ids": ["fear_greed"],
        },
        "summary": result["summary"],
        "ranking": result["ranking"],
        "blend": result["blend"],
        "details": result["details"],
        "error": None,
        "created_at": "2025-06-01T12:00:00",
    }


class StubMarketDataService:
    def __init__(self) -> None:
        self.saved_klines: list[tuple[str, str, list[list[float]]]] = []

    def save_klines_background(self, symbol: str, timeframe: str, klines: list[list[float]]) -> None:
        self.saved_klines.append((symbol, timeframe, deepcopy(klines)))


class StubMarketQueryAppService:
    valid_symbols = ["BTC/USDT", "ETH/USDT"]
    valid_timeframes = ["1h", "4h", "1d"]
    full_history_used_external_persist_callback = False

    async def get_realtime(self, **kwargs):
        return make_market_realtime_response()

    async def get_current_price(self, **kwargs):
        return {
            "symbol": kwargs.get("symbol", "BTC/USDT"),
            "timeframe": kwargs.get("timeframe", "1d"),
            "timestamp": "2025-06-01T12:00:00",
            "current_price": 68000.0,
        }

    async def get_current_price_batch(self, **kwargs):
        symbols = kwargs.get("symbols", ["BTC/USDT"])
        timeframe = kwargs.get("timeframe", "1d")
        return {
            "timeframe": timeframe,
            "items": [
                {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "timestamp": "2025-06-01T12:00:00",
                    "current_price": 68000.0 if symbol == "BTC/USDT" else 3500.0,
                    "source": "websocket_snapshot",
                }
                for symbol in symbols
            ],
        }

    async def get_history(self, **kwargs):
        return build_market_history_response(
            symbol=kwargs.get("symbol", "BTC/USDT"),
            timeframe=kwargs.get("timeframe", "1h"),
            rows=make_kline_data(),
        ).model_dump()

    async def get_recent_klines(self, **kwargs):
        return await self.get_history(**kwargs)

    async def get_full_history(self, *, persist_klines=None, **kwargs):
        klines = make_kline_data()
        self.full_history_used_external_persist_callback = persist_klines is not None
        if persist_klines:
            persist_klines(kwargs["symbol"], kwargs["timeframe"], klines)
        return build_market_history_response(
            symbol=kwargs.get("symbol", "BTC/USDT"),
            timeframe=kwargs.get("timeframe", "1h"),
            rows=klines,
        ).model_dump()

    async def get_technical_metrics(self, **kwargs):
        return make_technical_metrics_response()

    async def get_live_kline_tail(self, **kwargs):
        return {
            "symbol": kwargs.get("symbol", "BTC/USDT"),
            "timeframe": kwargs.get("timeframe", "1h"),
            "timestamp": "2025-06-01T12:00:00",
            "current_price": 116.0,
            "kline_data": [item.model_dump() for item in build_ohlcv_points(make_kline_data())],
        }


class StubMarketInsightAppService:
    async def get_indicators_async(self, **kwargs):
        return [make_market_indicator()]

    async def get_trade_setup(self, **kwargs):
        return make_trade_setup_response()

    async def get_crypto_index(self, **kwargs):
        return make_crypto_index_response()


class StubFundingRateAppService:
    async def get_current_funding_rate(self, symbol: str):
        return make_funding_rate_snapshot()

    async def sync_funding_rate_history(self, **kwargs):
        return make_funding_rate_sync_response()

    async def get_funding_rate_history(self, **kwargs):
        return make_funding_rate_history()


class StubBinanceMarketService:
    async def get_market_breakout_monitor(self, **kwargs):
        return make_binance_breakout_monitor_response()


class StubBinanceWeb3Service:
    pass


class StubBacktestCommandService:
    def __init__(self) -> None:
        self.received_commands: dict[str, object] = {}

    async def start_backtest(self, command):
        self.received_commands["start_backtest"] = command
        return {"success": True, "backtest_id": 101, "message": "Backtest started"}

    async def start_paper_run(self, command):
        self.received_commands["start_paper_run"] = command
        return {"success": True, "run_id": 202, "message": "Paper run started"}

    async def stop_paper_run(self, run_id: int):
        self.received_commands["stop_paper_run"] = run_id
        return {"success": True, "run_id": run_id, "message": "Paper run stopped"}

    async def delete_backtest(self, backtest_id: int):
        self.received_commands["delete_backtest"] = backtest_id
        return {"success": True, "run_id": backtest_id, "message": "Backtest deleted"}

    async def delete_paper_run(self, run_id: int):
        self.received_commands["delete_paper_run"] = run_id
        return {"success": True, "run_id": run_id, "message": "Paper run deleted"}

    async def create_template(self, command):
        self.received_commands["create_template"] = command
        return make_template_response()

    async def create_indicator(self, command):
        self.received_commands["create_indicator"] = command
        return make_indicator_registry_item()

    async def create_strategy_version(self, command):
        self.received_commands["create_strategy_version"] = command
        return make_strategy_version()


class StubBacktestQueryService:
    async def list_strategies(self):
        return [make_strategy_definition()]

    async def list_templates(self):
        return [make_template_response()]

    async def get_editor_contract(self):
        return make_editor_contract()

    async def list_indicators(self):
        return [make_indicator_registry_item()]

    async def list_indicator_engines(self):
        return [make_indicator_engine_item()]

    async def list_runs(self):
        return [make_backtest_run()]

    async def get_run(self, backtest_id: int, page: int, page_size: int):
        return make_backtest_detail(run_id=backtest_id)

    async def list_paper_runs(self):
        return [make_backtest_run(run_id=202, execution_mode="paper_live")]

    async def get_paper_run(self, run_id: int, page: int, page_size: int):
        return make_backtest_detail(run_id=run_id, execution_mode="paper_live")


class StubToolsAppService:
    async def simulate_dca(self, command):
        return {
            "symbol": command.symbol,
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "target_time": "23:00",
            "total_days": 365,
            "total_invested": 1200.0,
            "final_value": 1480.0,
            "total_coins": 0.02,
            "roi": 23.33,
            "average_cost": 60000.0,
            "profit_loss": 280.0,
            "current_price": 74000.0,
            "history": [],
            "profit_pct": 23.33,
        }

    async def compare_pairs(self, command):
        return {
            "symbol_a": command.symbol_a,
            "symbol_b": command.symbol_b,
            "data_a": [],
            "data_b": [],
            "ratio_ohlc": [],
            "ratio_symbol": f"{command.symbol_a}/{command.symbol_b}",
            "relative_strength": 1.12,
        }


class StubFactorResearchService:
    async def get_catalog_async(self):
        return make_factor_catalog()

    async def analyze_async(self, **kwargs):
        return make_factor_research_response()

    async def list_runs_async(self, limit: int = 20):
        return [make_factor_run_detail()]

    async def get_run_async(self, run_id: int):
        result = make_factor_run_detail()
        result["id"] = run_id
        return result


class StubFactorExecutionService:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    async def run_backtest_async(self, **kwargs):
        self.calls.append(kwargs)
        return 707


class StubFactorPaperRunManager:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    async def start_run(self, **kwargs):
        self.calls.append(kwargs)
        return {"success": True, "run_id": 808, "message": "Factor paper run started"}
