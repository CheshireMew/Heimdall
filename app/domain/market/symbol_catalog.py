from __future__ import annotations

from dataclasses import dataclass

from app.domain.market.index_catalog import INDEX_CATALOG, get_index_instrument
from config import settings


EXTRA_MARKET_SYMBOL_EXCHANGES: dict[str, str] = {
    "BNB/USDT": settings.EXCHANGE_ID,
    "PAXG/USDT": settings.EXCHANGE_ID,
    "OKB/USDT": "okx",
}

USD_EQUIVALENT_SYMBOLS = (
    "USD",
    "USDT",
    "USDC",
    "FDUSD",
    "BUSD",
    "DAI",
    "TUSD",
    "USDP",
    "PYUSD",
    "USDS",
)


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


def get_supported_crypto_symbols() -> list[str]:
    return list(MARKET_SYMBOL_CATALOG.keys())


def get_market_symbol_source(symbol: str) -> MarketSymbolSource | None:
    normalized_symbol = normalize_market_symbol(symbol)
    if not normalized_symbol:
        return None
    return MARKET_SYMBOL_CATALOG.get(normalized_symbol)


def get_supported_market_symbols() -> list[str]:
    return get_supported_crypto_symbols()


def get_usd_equivalent_symbols() -> list[str]:
    return list(USD_EQUIVALENT_SYMBOLS)


def is_usd_equivalent_symbol(symbol: str) -> bool:
    value = str(symbol or "").strip().upper()
    if not value:
        return False
    base_symbol = value.split("/")[0]
    return base_symbol in USD_EQUIVALENT_SYMBOLS


def list_market_search_items() -> list[dict[str, object]]:
    cash_symbols = [
        {
            "symbol": symbol,
            "name": "US Dollar" if symbol == "USD" else f"{symbol} USD equivalent",
            "asset_class": "cash",
            "market": "USD",
            "currency": "USD",
            "exchange": "USD",
            "aliases": ["美元", "现金", "stablecoin", "稳定币", "usd equivalent"],
            "pricing_symbol": None,
            "pricing_name": None,
            "pricing_currency": "USD",
        }
        for symbol in get_usd_equivalent_symbols()
    ]
    crypto_symbols = [
        {
            "symbol": source.symbol,
            "name": source.symbol,
            "asset_class": "crypto",
            "market": "CRYPTO",
            "currency": "USDT",
            "exchange": source.exchange_id.upper(),
            "aliases": [source.symbol.split("/")[0]],
            "pricing_symbol": None,
            "pricing_name": None,
            "pricing_currency": "USDT",
        }
        for source in MARKET_SYMBOL_CATALOG.values()
    ]
    index_symbols = [
        {
            "symbol": instrument.symbol,
            "name": instrument.name,
            "asset_class": "index",
            "market": instrument.market,
            "currency": instrument.currency,
            "exchange": instrument.market,
            "aliases": list(instrument.aliases),
            "pricing_symbol": instrument.pricing_symbol,
            "pricing_name": instrument.pricing_name,
            "pricing_currency": instrument.pricing_currency or instrument.currency,
        }
        for instrument in INDEX_CATALOG.values()
    ]
    return cash_symbols + crypto_symbols + index_symbols


def resolve_market_asset(symbol: str) -> dict[str, str] | None:
    value = str(symbol or "").strip().upper()
    if not value:
        return None
    if is_usd_equivalent_symbol(value):
        return {"symbol": value.split("/")[0], "asset_class": "cash"}

    instrument = get_index_instrument(value)
    if instrument:
        return {"symbol": instrument.symbol, "asset_class": "index"}

    source = get_market_symbol_source(value)
    if source:
        return {"symbol": source.symbol, "asset_class": "crypto"}
    return None


__all__ = [
    "MarketSymbolSource",
    "MARKET_SYMBOL_CATALOG",
    "build_market_symbol_catalog",
    "get_market_symbol_source",
    "get_supported_crypto_symbols",
    "get_supported_market_symbols",
    "get_usd_equivalent_symbols",
    "is_usd_equivalent_symbol",
    "list_market_search_items",
    "normalize_market_symbol",
    "resolve_market_asset",
]
