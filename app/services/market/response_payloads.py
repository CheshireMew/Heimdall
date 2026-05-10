from __future__ import annotations


def build_ohlcv_points(rows: list[list[float]]) -> list[dict[str, float | int]]:
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


def build_market_history_coverage(
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


def build_market_history_response(
    *,
    symbol: str,
    timeframe: str,
    rows: list[list[float]],
    missing_ranges: list[tuple[int, int]] | None = None,
) -> dict[str, object]:
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "items": build_ohlcv_points(rows),
        "coverage": build_market_history_coverage(missing_ranges),
    }


def build_market_history_batch_response(
    *,
    timeframe: str,
    series_by_symbol: dict[str, tuple[list[list[float]], list[tuple[int, int]]]],
) -> dict[str, object]:
    return {
        "timeframe": timeframe,
        "items": [
            {
                "symbol": symbol,
                "items": build_ohlcv_points(rows),
                "coverage": build_market_history_coverage(missing_ranges),
            }
            for symbol, (rows, missing_ranges) in series_by_symbol.items()
        ],
    }
