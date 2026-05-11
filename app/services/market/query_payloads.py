from __future__ import annotations

from typing import Any


def ohlcv_points(rows: list[list[float]]) -> list[dict[str, float | int]]:
    return [
        {
            "timestamp": int(row[0]),
            "open": float(row[1]),
            "high": float(row[2]),
            "low": float(row[3]),
            "close": float(row[4]),
            "volume": float(row[5]),
        }
        for row in rows
        if isinstance(row, list) and len(row) >= 6
    ]


def market_history_coverage(missing_ranges: list[tuple[int, int]] | None = None) -> dict[str, Any]:
    ranges = missing_ranges or []
    return {
        "complete": not ranges,
        "missing_ranges": [
            {"start_ts": int(start), "end_ts": int(end)}
            for start, end in ranges
        ],
    }


def market_history_response(
    *,
    symbol: str,
    timeframe: str,
    rows: list[list[float]],
    missing_ranges: list[tuple[int, int]] | None = None,
) -> dict[str, Any]:
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "items": ohlcv_points(rows),
        "coverage": market_history_coverage(missing_ranges),
    }


def market_history_batch_response(
    *,
    timeframe: str,
    series_by_symbol: dict[str, tuple[list[list[float]], list[tuple[int, int]]]],
) -> dict[str, Any]:
    return {
        "timeframe": timeframe,
        "items": [
            {
                "symbol": symbol,
                "items": ohlcv_points(rows),
                "coverage": market_history_coverage(missing_ranges),
            }
            for symbol, (rows, missing_ranges) in series_by_symbol.items()
        ],
    }


def current_price_response(
    *,
    symbol: str,
    timeframe: str,
    timestamp: str,
    current_price: float | None,
    source: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "symbol": symbol,
        "timeframe": timeframe,
        "timestamp": timestamp,
        "current_price": current_price,
    }
    if source is not None:
        payload["source"] = source
    return payload


def realtime_response(
    *,
    symbol: str,
    timestamp: str,
    current_price: float,
    indicators: dict[str, Any],
    ai_analysis: Any,
    kline_data: list[list[float]],
    timeframe: str | None,
    include_type: bool,
) -> dict[str, Any]:
    return {
        "symbol": symbol,
        "timestamp": timestamp,
        "current_price": current_price,
        "indicators": indicators,
        "ai_analysis": ai_analysis,
        "kline_data": ohlcv_points(kline_data),
        "timeframe": timeframe,
        "type": "realtime" if include_type else None,
    }
