import pytest

from app.domain.market.trade_setup import TradeSetupEngine, TradeSetupRequest


def make_request() -> TradeSetupRequest:
    return TradeSetupRequest(
        symbol="BTC/USDT",
        timeframe="1h",
        account_size=1000,
        style="Scalping",
        strategy="最大收益",
    )


def make_klines(close: float = 120.0) -> list[list[float]]:
    return [
        [1710000000000 + index * 3600000, 100.0 + index, 102.0 + index, 98.0 + index, 100.0 + index, 1000.0]
        for index in range(29)
    ] + [[1710104400000, close - 1, close + 2, close - 3, close, 1400.0]]


def test_trade_setup_engine_builds_long_plan_from_bullish_snapshot():
    result = TradeSetupEngine().build_rules(
        make_request(),
        make_klines(130.0),
        {"atr": 5.0, "ema": 120.0, "rsi": 58.0, "macd": (1.0, 0.7, 0.3)},
    )

    setup = result["setup"]
    assert setup["side"] == "long"
    assert setup["entry"] == 130.0
    assert setup["stop"] < setup["entry"] < setup["target"]
    assert setup["risk_reward"] == pytest.approx(2.4)
    assert setup["risk_amount"] == 6.0
    assert setup["source"] == "rules"


def test_trade_setup_engine_builds_short_plan_from_bearish_snapshot():
    result = TradeSetupEngine().build_rules(
        make_request(),
        make_klines(110.0),
        {"atr": 4.0, "ema": 120.0, "rsi": 45.0, "macd": (-1.0, -0.7, -0.3)},
    )

    setup = result["setup"]
    assert setup["side"] == "short"
    assert setup["target"] < setup["entry"] < setup["stop"]
    assert setup["risk_reward"] == pytest.approx(2.4)


def test_trade_setup_engine_waits_when_snapshot_is_unclear():
    result = TradeSetupEngine().build_rules(
        make_request(),
        make_klines(120.0),
        {"atr": 4.0, "ema": 120.0, "rsi": 78.0, "macd": (0.1, 0.1, 0.0)},
    )

    assert result["setup"] is None
    assert "等待" in result["reason"]


def test_trade_setup_engine_applies_strategy_reward_profile():
    request = TradeSetupRequest(
        symbol="BTC/USDT",
        timeframe="1h",
        account_size=1000,
        style="Intraday",
        strategy="稳健突破",
    )
    result = TradeSetupEngine().build_rules(
        request,
        make_klines(130.0),
        {"atr": 5.0, "ema": 120.0, "rsi": 58.0, "macd": (1.0, 0.7, 0.3)},
    )

    assert result["setup"]["risk_reward"] == pytest.approx(1.8)
    assert result["setup"]["risk_amount"] == 10.0


def test_trade_setup_engine_normalizes_valid_ai_plan():
    request = TradeSetupRequest(
        symbol="BTC/USDT",
        timeframe="1h",
        account_size=1000,
        style="Intraday",
        strategy="最大收益",
        mode="ai",
    )
    result = TradeSetupEngine().build_ai(
        request,
        make_klines(130.0),
        {"side": "LONG", "entry": 130.0, "target": 145.0, "stop": 124.0, "confidence": 73, "reason": "AI看多"},
    )

    setup = result["setup"]
    assert setup["side"] == "long"
    assert setup["risk_reward"] == pytest.approx(2.5)
    assert setup["source"] == "ai"
    assert result["source"] == "ai"


def test_trade_setup_engine_rejects_invalid_ai_plan():
    request = TradeSetupRequest(
        symbol="BTC/USDT",
        timeframe="1h",
        account_size=1000,
        style="Intraday",
        strategy="最大收益",
        mode="ai",
    )
    result = TradeSetupEngine().build_ai(
        request,
        make_klines(130.0),
        {"side": "LONG", "entry": 130.0, "target": 120.0, "stop": 124.0, "confidence": 73},
    )

    assert result["setup"] is None
    assert "已拒绝显示" in result["reason"]
