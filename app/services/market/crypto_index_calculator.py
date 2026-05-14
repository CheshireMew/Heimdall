from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any


def build_crypto_index_payload(
    *,
    top_n: int,
    days: int,
    base_value: float,
    constituents: list[dict[str, Any]],
    histories: list[dict[str, Any]],
) -> dict[str, Any]:
    if not constituents:
        return empty_crypto_index_payload(
            top_n=top_n,
            days=days,
            base_value=base_value,
            constituents=[],
            is_partial=False,
            resolved_constituents_count=0,
            missing_symbols=[],
        )

    available_ids = {item["id"] for item in histories if item["market_caps"]}
    available_sources = {
        item.get("source")
        for item in histories
        if item.get("market_caps") and item.get("source")
    }
    filtered_constituents = [item for item in constituents if item["id"] in available_ids]
    missing_symbols = [item["symbol"] for item in constituents if item["id"] not in available_ids]
    is_partial = len(filtered_constituents) != len(constituents)

    series_by_coin: dict[str, dict[str, float]] = {}
    first_dates: list[str] = []
    all_dates = set()

    for item in histories:
        per_date: dict[str, float] = {}
        for ts, market_cap in item["market_caps"]:
            date_key = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
            per_date[date_key] = market_cap
            all_dates.add(date_key)

        if per_date:
            first_date = min(per_date.keys())
            first_dates.append(first_date)
            series_by_coin[item["id"]] = per_date

    if not series_by_coin or not first_dates:
        return empty_crypto_index_payload(
            top_n=top_n,
            days=days,
            base_value=base_value,
            constituents=filtered_constituents,
            is_partial=True,
            resolved_constituents_count=len(filtered_constituents),
            missing_symbols=missing_symbols,
        )

    common_start = max(first_dates)
    ordered_dates = sorted(date for date in all_dates if date >= common_start)

    rolling_caps: dict[str, float] = {}
    aggregated_caps: dict[str, float] = defaultdict(float)

    for date in ordered_dates:
        for coin_id, series in series_by_coin.items():
            if date in series:
                rolling_caps[coin_id] = series[date]
            if coin_id in rolling_caps:
                aggregated_caps[date] += rolling_caps[coin_id]

    valid_dates = [date for date in ordered_dates if aggregated_caps[date] > 0]
    if not valid_dates:
        return empty_crypto_index_payload(
            top_n=top_n,
            days=days,
            base_value=base_value,
            constituents=filtered_constituents,
            is_partial=True,
            resolved_constituents_count=len(filtered_constituents),
            missing_symbols=missing_symbols,
        )

    base_cap = aggregated_caps[valid_dates[0]]
    history = [
        {
            "date": date,
            "timestamp": int(datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()),
            "market_cap": aggregated_caps[date],
            "index_value": round(base_value * aggregated_caps[date] / base_cap, 2),
        }
        for date in valid_dates
    ]

    current_basket_cap = sum(item["market_cap"] for item in filtered_constituents if item.get("market_cap"))
    weighted_change_numerator = sum(
        (item.get("market_cap_change_24h_pct") or 0) * (item.get("market_cap") or 0)
        for item in filtered_constituents
    )
    weighted_change = weighted_change_numerator / current_basket_cap if current_basket_cap else 0.0

    btc_market_cap = next((item["market_cap"] for item in filtered_constituents if item["symbol"] == "BTC"), 0)
    eth_market_cap = next((item["market_cap"] for item in filtered_constituents if item["symbol"] == "ETH"), 0)
    history_method = "exchange-price-history" if available_sources <= {"binance", "okx"} else "mixed-price-history"

    return {
        "top_n": top_n,
        "days": days,
        "base_value": base_value,
        "constituents": filtered_constituents,
        "history": history,
        "is_partial": is_partial,
        "resolved_constituents_count": len(filtered_constituents),
        "missing_symbols": missing_symbols,
        "summary": {
            "current_basket_market_cap": current_basket_cap,
            "current_index_value": history[-1]["index_value"],
            "basket_change_24h_pct": round(weighted_change, 2),
            "btc_weight_pct": round((btc_market_cap / current_basket_cap) * 100, 2) if current_basket_cap else 0.0,
            "eth_weight_pct": round((eth_market_cap / current_basket_cap) * 100, 2) if current_basket_cap else 0.0,
            "common_start_date": valid_dates[0],
            "methodology": (
                f"fixed-current-market-cap-weighted-{history_method}-partial"
                if is_partial
                else f"fixed-current-market-cap-weighted-{history_method}"
            ),
        },
    }


def empty_crypto_index_payload(
    *,
    top_n: int,
    days: int,
    base_value: float,
    constituents: list[dict[str, Any]],
    is_partial: bool,
    resolved_constituents_count: int,
    missing_symbols: list[str],
) -> dict[str, Any]:
    return {
        "top_n": top_n,
        "days": days,
        "base_value": base_value,
        "constituents": constituents,
        "history": [],
        "is_partial": is_partial,
        "resolved_constituents_count": resolved_constituents_count,
        "missing_symbols": missing_symbols,
    }
