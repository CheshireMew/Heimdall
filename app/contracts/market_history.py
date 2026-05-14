from __future__ import annotations

from typing import Any


def build_ohlcv_point_payloads(rows: list[list[float]]) -> list[dict[str, float | int]]:
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


def build_market_history_coverage_payload(
    missing_ranges: list[tuple[int, int]] | None = None,
) -> dict[str, object]:
    ranges = missing_ranges or []
    return {
        "complete": not ranges,
        "missing_ranges": [
            {"start_ts": int(start), "end_ts": int(end)}
            for start, end in ranges
        ],
    }


def build_market_history_payload(
    *,
    symbol: str,
    timeframe: str,
    rows: list[list[float]],
    missing_ranges: list[tuple[int, int]] | None = None,
) -> dict[str, object]:
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "items": build_ohlcv_point_payloads(rows),
        "coverage": build_market_history_coverage_payload(missing_ranges),
    }


def build_market_history_batch_payload(
    *,
    timeframe: str,
    series_by_symbol: dict[str, tuple[list[list[float]], list[tuple[int, int]]]],
) -> dict[str, object]:
    return {
        "timeframe": timeframe,
        "items": [
            {
                "symbol": symbol,
                "items": build_ohlcv_point_payloads(rows),
                "coverage": build_market_history_coverage_payload(missing_ranges),
            }
            for symbol, (rows, missing_ranges) in series_by_symbol.items()
        ],
    }


def build_kline_tail_payload(
    *,
    symbol: str,
    timeframe: str,
    timestamp: str,
    current_price: float | None,
    rows: list[list[float]],
) -> dict[str, object]:
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "timestamp": timestamp,
        "current_price": current_price,
        "kline_data": build_ohlcv_point_payloads(rows),
    }


def build_current_price_payload(
    *,
    symbol: str,
    timeframe: str,
    timestamp: str,
    current_price: float | None,
) -> dict[str, object]:
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "timestamp": timestamp,
        "current_price": current_price,
    }


def build_current_price_batch_item_payload(
    *,
    symbol: str,
    timeframe: str,
    timestamp: str,
    current_price: float | None,
    source: str,
) -> dict[str, object]:
    return {
        **build_current_price_payload(
            symbol=symbol,
            timeframe=timeframe,
            timestamp=timestamp,
            current_price=current_price,
        ),
        "source": source,
    }


def build_current_price_batch_payload(
    *,
    timeframe: str,
    items: list[dict[str, object]],
) -> dict[str, object]:
    return {"timeframe": timeframe, "items": items}


def build_realtime_payload(
    *,
    symbol: str,
    timestamp: str,
    current_price: float,
    indicators: dict[str, Any],
    ai_analysis: Any | None,
    rows: list[list[float]],
    timeframe: str | None,
    include_type: bool,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "symbol": symbol,
        "timestamp": timestamp,
        "current_price": current_price,
        "indicators": indicators,
        "ai_analysis": ai_analysis,
        "kline_data": build_ohlcv_point_payloads(rows),
        "timeframe": timeframe,
    }
    if include_type:
        payload["type"] = "realtime"
    return payload
