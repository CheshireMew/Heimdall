from __future__ import annotations

from typing import Any

from .binance_numbers import to_float, to_int


def normalize_ticker_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "symbol": item.get("symbol"),
        "price_change": to_float(item.get("priceChange")),
        "price_change_pct": to_float(item.get("priceChangePercent")),
        "weighted_avg_price": to_float(item.get("weightedAvgPrice")),
        "last_price": to_float(item.get("lastPrice")),
        "last_qty": to_float(item.get("lastQty")),
        "open_price": to_float(item.get("openPrice")),
        "high_price": to_float(item.get("highPrice")),
        "low_price": to_float(item.get("lowPrice")),
        "volume": to_float(item.get("volume")),
        "quote_volume": to_float(item.get("quoteVolume")),
        "open_time": to_int(item.get("openTime")),
        "close_time": to_int(item.get("closeTime")),
        "count": to_int(item.get("count")),
    }


def normalize_levels(levels: list[list[Any]]) -> list[dict[str, float | None]]:
    return [{"price": to_float(level[0]), "qty": to_float(level[1])} for level in levels]


def normalize_trade(item: dict[str, Any], *, aggregate: bool = False) -> dict[str, Any]:
    return {
        "id": to_int(item.get("a") if aggregate else item.get("id")),
        "price": to_float(item.get("p") if aggregate else item.get("price")),
        "qty": to_float(item.get("q") if aggregate else item.get("qty")),
        "quote_qty": to_float(item.get("quoteQty")),
        "time": to_int(item.get("T") if aggregate else item.get("time")),
        "is_buyer_maker": bool(item.get("m") if aggregate else item.get("isBuyerMaker")),
    }


def normalize_kline_response(market: str, symbol: str, interval: str, rows: list[list[Any]]) -> dict[str, Any]:
    return {
        "exchange": "binance",
        "market": market,
        "symbol": symbol,
        "interval": interval,
        "items": [
            {
                "open_time": to_int(row[0]),
                "open": to_float(row[1]),
                "high": to_float(row[2]),
                "low": to_float(row[3]),
                "close": to_float(row[4]),
                "volume": to_float(row[5]),
                "close_time": to_int(row[6]),
                "quote_volume": to_float(row[7]) if len(row) > 7 else None,
                "trade_count": to_int(row[8]) if len(row) > 8 else None,
            }
            for row in rows
        ],
    }


def normalize_derivatives_exchange_info(market: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "exchange": "binance",
        "market": market,
        "timezone": payload.get("timezone"),
        "server_time": payload.get("serverTime"),
        "symbols": [
            {
                "symbol": item.get("symbol"),
                "status": item.get("status"),
                "pair": item.get("pair"),
                "contract_type": item.get("contractType"),
                "base_asset": item.get("baseAsset"),
                "quote_asset": item.get("quoteAsset"),
            }
            for item in payload.get("symbols", [])
        ],
    }


def normalize_derivatives_ticker_list(market: str, payload: Any) -> dict[str, Any]:
    items = payload if isinstance(payload, list) else [payload]
    return {
        "exchange": "binance",
        "market": market,
        "items": [normalize_ticker_item(item) for item in items],
    }


def normalize_mark_price_list(market: str, payload: Any) -> dict[str, Any]:
    items = payload if isinstance(payload, list) else [payload]
    return {
        "exchange": "binance",
        "market": market,
        "items": [
            {
                "symbol": item.get("symbol"),
                "pair": item.get("pair"),
                "mark_price": to_float(item.get("markPrice")),
                "index_price": to_float(item.get("indexPrice")),
                "estimated_settle_price": to_float(item.get("estimatedSettlePrice")),
                "last_funding_rate": to_float(item.get("lastFundingRate")),
                "next_funding_time": to_int(item.get("nextFundingTime")),
                "interest_rate": to_float(item.get("interestRate")),
                "time": to_int(item.get("time")),
            }
            for item in items
        ],
    }


def normalize_open_interest_snapshot(market: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "exchange": "binance",
        "market": market,
        "symbol": payload.get("symbol"),
        "pair": payload.get("pair"),
        "open_interest": to_float(payload.get("openInterest")),
        "contract_type": payload.get("contractType"),
        "time": to_int(payload.get("time")),
    }


def normalize_open_interest_stats(market: str, payload: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "exchange": "binance",
        "market": market,
        "items": [
            {
                "symbol": item.get("symbol"),
                "pair": item.get("pair"),
                "contract_type": item.get("contractType"),
                "sum_open_interest": to_float(item.get("sumOpenInterest")),
                "sum_open_interest_value": to_float(item.get("sumOpenInterestValue")),
                "timestamp": to_int(item.get("timestamp")),
            }
            for item in payload
        ],
    }


def normalize_ratio_series(market: str, payload: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "exchange": "binance",
        "market": market,
        "items": [
            {
                "symbol": item.get("symbol"),
                "pair": item.get("pair"),
                "long_short_ratio": to_float(item.get("longShortRatio")),
                "long_account": to_float(item.get("longAccount")),
                "short_account": to_float(item.get("shortAccount")),
                "long_position": to_float(item.get("longPosition")),
                "short_position": to_float(item.get("shortPosition")),
                "timestamp": to_int(item.get("timestamp")),
            }
            for item in payload
        ],
    }


def normalize_taker_volume(market: str, payload: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "exchange": "binance",
        "market": market,
        "items": [
            {
                "symbol": item.get("symbol"),
                "pair": item.get("pair"),
                "buy_sell_ratio": to_float(item.get("buySellRatio")),
                "buy_vol": to_float(item.get("buyVol")),
                "sell_vol": to_float(item.get("sellVol")),
                "buy_vol_value": to_float(item.get("buyVolValue")),
                "sell_vol_value": to_float(item.get("sellVolValue")),
                "timestamp": to_int(item.get("timestamp")),
            }
            for item in payload
        ],
    }


def normalize_basis(market: str, payload: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "exchange": "binance",
        "market": market,
        "items": [
            {
                "symbol": item.get("symbol"),
                "pair": item.get("pair"),
                "contract_type": item.get("contractType"),
                "basis": to_float(item.get("basis")),
                "basis_rate": to_float(item.get("basisRate")),
                "annualized_basis_rate": to_float(item.get("annualizedBasisRate")),
                "futures_price": to_float(item.get("futuresPrice")),
                "index_price": to_float(item.get("indexPrice")),
                "timestamp": to_int(item.get("timestamp")),
            }
            for item in payload
        ],
    }
