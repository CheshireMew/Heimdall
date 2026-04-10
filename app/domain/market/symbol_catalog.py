from __future__ import annotations

from dataclasses import dataclass

from config import settings


EXTRA_MARKET_SYMBOL_EXCHANGES: dict[str, str] = {
    "BNB/USDT": settings.EXCHANGE_ID,
    "PAXG/USDT": settings.EXCHANGE_ID,
    "OKB/USDT": "okx",
}


@dataclass(frozen=True)
class MarketSymbolSource:
    symbol: str
    exchange_id: str
    storage_symbol: str


def normalize_market_symbol(value: str) -> str:
    symbol = str(value or "").strip().upper()
    if not symbol:
        return ""
    if "/" in symbol:
        return symbol
    return f"{symbol}/USDT"


def _build_source(symbol: str, exchange_id: str) -> MarketSymbolSource:
    normalized_symbol = normalize_market_symbol(symbol)
    storage_symbol = normalized_symbol if exchange_id == settings.EXCHANGE_ID else f"{exchange_id}:{normalized_symbol}"
    return MarketSymbolSource(
        symbol=normalized_symbol,
        exchange_id=exchange_id,
        storage_symbol=storage_symbol,
    )


def build_market_symbol_catalog() -> dict[str, MarketSymbolSource]:
    catalog: dict[str, MarketSymbolSource] = {}
    for symbol in settings.SYMBOLS:
        source = _build_source(symbol, settings.EXCHANGE_ID)
        catalog[source.symbol] = source
    for symbol, exchange_id in EXTRA_MARKET_SYMBOL_EXCHANGES.items():
        source = _build_source(symbol, exchange_id)
        catalog[source.symbol] = source
    return catalog


MARKET_SYMBOL_CATALOG = build_market_symbol_catalog()


def get_market_symbol_source(symbol: str) -> MarketSymbolSource | None:
    normalized_symbol = normalize_market_symbol(symbol)
    if not normalized_symbol:
        return None
    return MARKET_SYMBOL_CATALOG.get(normalized_symbol)


def get_supported_market_symbols() -> list[str]:
    return list(MARKET_SYMBOL_CATALOG.keys())


__all__ = [
    "MarketSymbolSource",
    "MARKET_SYMBOL_CATALOG",
    "build_market_symbol_catalog",
    "get_market_symbol_source",
    "get_supported_market_symbols",
    "normalize_market_symbol",
]
