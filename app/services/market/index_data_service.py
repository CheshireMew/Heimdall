from __future__ import annotations

from datetime import datetime, timedelta, timezone
from app.domain.market.index_catalog import (
    INDEX_CATALOG,
    IndexInstrument,
    get_index_instrument,
    get_supported_index_symbols,
)
from app.schemas.market import (
    MarketIndexHistoryResponse,
    MarketIndexResponse,
    build_ohlcv_points,
)
from app.services.executor import run_sync
from app.services.market.history_ranges import collect_missing_ranges
from app.services.market.index_history_sources import IndexFetchResult, IndexHistorySources
from app.services.market.kline_store import KlineStore


class IndexDataService:
    def __init__(
        self,
        kline_store: KlineStore,
        history_sources: IndexHistorySources | None = None,
    ) -> None:
        self.kline_store = kline_store
        self.history_sources = history_sources or IndexHistorySources()
        self.supported_timeframes = {"1d"}

    def list_indexes(self) -> list[MarketIndexResponse]:
        return [
            MarketIndexResponse(
                symbol=item.symbol,
                name=item.name,
                market=item.market,
                currency=item.currency,
                pricing_symbol=item.pricing_symbol,
                pricing_name=item.pricing_name,
                pricing_currency=item.pricing_currency or item.currency,
            )
            for item in INDEX_CATALOG.values()
        ]

    async def list_indexes_async(self) -> list[MarketIndexResponse]:
        return await run_sync(self.list_indexes)

    def get_instrument(self, symbol: str) -> IndexInstrument | None:
        return get_index_instrument(symbol)

    def get_history(
        self,
        *,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: str | None = None,
    ) -> MarketIndexHistoryResponse:
        instrument = self._validate(symbol, timeframe)
        return self._get_series_history(
            instrument=instrument,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            storage_symbol=instrument.storage_symbol,
            fetcher=self._fetch_history,
            price_basis="index",
            pricing_symbol=instrument.pricing_symbol,
            pricing_name=instrument.pricing_name,
            pricing_currency=instrument.pricing_currency or instrument.currency,
            native_currency=instrument.currency,
        )

    async def get_history_async(
        self,
        *,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: str | None = None,
    ) -> MarketIndexHistoryResponse:
        return await run_sync(
            lambda: self.get_history(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date,
            )
        )

    def get_pricing_history(
        self,
        *,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: str | None = None,
    ) -> MarketIndexHistoryResponse:
        instrument = self._validate(symbol, timeframe)
        if not instrument.pricing_symbol or not instrument.pricing_storage_symbol or not instrument.pricing_provider:
            raise ValueError(f"{instrument.symbol} 暂无默认 ETF 代理价格")
        return self._get_series_history(
            instrument=instrument,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            storage_symbol=instrument.pricing_storage_symbol,
            fetcher=self._fetch_pricing_history,
            price_basis="proxy_etf",
            pricing_symbol=instrument.pricing_symbol,
            pricing_name=instrument.pricing_name,
            pricing_currency="USD",
            native_currency=instrument.pricing_currency or instrument.currency,
        )

    async def get_pricing_history_async(
        self,
        *,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: str | None = None,
    ) -> MarketIndexHistoryResponse:
        return await run_sync(
            lambda: self.get_pricing_history(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date,
            )
        )

    def get_latest(self, *, symbol: str) -> MarketIndexHistoryResponse:
        result = self.get_history(symbol=symbol, timeframe="1d", start_date=self._latest_window_start())
        latest_data = result.data[-1:] if result.data else []
        return result.model_copy(update={"data": latest_data, "count": len(latest_data)})

    async def get_latest_async(self, *, symbol: str) -> MarketIndexHistoryResponse:
        return await run_sync(lambda: self.get_latest(symbol=symbol))

    def get_latest_pricing(self, *, symbol: str) -> MarketIndexHistoryResponse:
        result = self.get_pricing_history(symbol=symbol, timeframe="1d", start_date=self._latest_window_start())
        latest_data = result.data[-1:] if result.data else []
        return result.model_copy(update={"data": latest_data, "count": len(latest_data)})

    async def get_latest_pricing_async(self, *, symbol: str) -> MarketIndexHistoryResponse:
        return await run_sync(lambda: self.get_latest_pricing(symbol=symbol))

    def _get_series_history(
        self,
        *,
        instrument: IndexInstrument,
        timeframe: str,
        start_date: str,
        end_date: str | None,
        storage_symbol: str,
        fetcher,
        price_basis: str,
        pricing_symbol: str | None,
        pricing_name: str | None,
        pricing_currency: str,
        native_currency: str,
    ) -> MarketIndexHistoryResponse:
        start_dt = self._parse_date(start_date)
        end_dt = self._parse_date(end_date) if end_date else datetime.now(timezone.utc)
        if start_dt > end_dt:
            raise ValueError("start_date 不能晚于 end_date")

        start_ts = self._to_ms(start_dt)
        end_ts = self._to_ms(end_dt) + 86_399_999
        end_ts_exclusive = end_ts + 1
        cached = self.kline_store.get_range(storage_symbol, timeframe, start_ts, end_ts)
        merged = {row[0]: row for row in cached}
        source = "cache" if cached else "none"
        is_close_only = not cached

        missing_ranges = collect_missing_ranges(
            cached_klines=cached,
            timeframe=timeframe,
            start_ts=start_ts,
            end_ts_exclusive=end_ts_exclusive,
        )
        fetch_windows = [
            (
                self._from_ms(gap_start),
                self._from_ms(max(gap_start, gap_end - 1)),
            )
            for gap_start, gap_end in missing_ranges
        ]

        for window_start, window_end in fetch_windows:
            fetch_result = fetcher(instrument, window_start, window_end)
            if not fetch_result.data:
                continue

            if price_basis == "proxy_etf":
                fetch_result = IndexFetchResult(
                    data=self._convert_rows_to_usd(fetch_result.data, native_currency, window_start, window_end),
                    source=f"{fetch_result.source}:usd",
                    is_close_only=fetch_result.is_close_only,
                )
                if not fetch_result.data:
                    continue

            source = fetch_result.source
            if not fetch_result.is_close_only:
                is_close_only = False
                self.kline_store.save(storage_symbol, timeframe, fetch_result.data)

            for row in fetch_result.data:
                if start_ts <= row[0] <= end_ts:
                    merged[row[0]] = row

        data = sorted(merged.values(), key=lambda row: row[0])
        return MarketIndexHistoryResponse(
            symbol=instrument.symbol,
            name=instrument.name,
            market=instrument.market,
            currency=pricing_currency if price_basis == "proxy_etf" else instrument.currency,
            native_currency=native_currency,
            timeframe=timeframe,
            source=source,
            price_basis=price_basis,
            pricing_symbol=pricing_symbol,
            pricing_name=pricing_name,
            pricing_currency=pricing_currency,
            is_close_only=bool(data) and is_close_only,
            count=len(data),
            data=build_ohlcv_points(data),
        )

    def _validate(self, symbol: str, timeframe: str) -> IndexInstrument:
        instrument = get_index_instrument(symbol)
        if not instrument:
            raise ValueError(f"无效指数。可选: {get_supported_index_symbols()}")
        if timeframe not in self.supported_timeframes:
            raise ValueError("指数行情第一版只支持 1d 日线")
        return instrument

    def _fetch_history(
        self,
        instrument: IndexInstrument,
        start_dt: datetime,
        end_dt: datetime,
    ) -> IndexFetchResult:
        return self.history_sources.fetch_history(instrument, start_dt, end_dt)

    def _fetch_pricing_history(
        self,
        instrument: IndexInstrument,
        start_dt: datetime,
        end_dt: datetime,
    ) -> IndexFetchResult:
        return self.history_sources.fetch_pricing_history(instrument, start_dt, end_dt)

    def _convert_rows_to_usd(
        self,
        rows: list[list[float]],
        native_currency: str,
        start_dt: datetime,
        end_dt: datetime,
    ) -> list[list[float]]:
        currency = str(native_currency or "").upper()
        if currency in {"", "USD", "USDT"}:
            return rows

        fx_rates = self._fetch_usd_fx_rates(currency, start_dt, end_dt)
        converted: list[list[float]] = []
        last_rate: float | None = None
        for row in rows:
            row_dt = self._from_ms(int(row[0]))
            rate = fx_rates.get(row_dt.strftime("%Y-%m-%d")) or last_rate
            if not rate:
                continue
            last_rate = rate
            converted.append([
                row[0],
                row[1] * rate,
                row[2] * rate,
                row[3] * rate,
                row[4] * rate,
                row[5],
            ])
        return converted

    def _fetch_usd_fx_rates(
        self,
        currency: str,
        start_dt: datetime,
        end_dt: datetime,
    ) -> dict[str, float]:
        return self.history_sources.fetch_usd_fx_rates(currency, start_dt, end_dt)

    def _parse_date(self, value: str) -> datetime:
        return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)

    def _from_ms(self, value: int) -> datetime:
        return datetime.fromtimestamp(value / 1000, tz=timezone.utc)

    def _to_ms(self, value: datetime) -> int:
        return int(value.timestamp() * 1000)

    def _latest_window_start(self) -> str:
        return (datetime.now(timezone.utc) - timedelta(days=370)).strftime("%Y-%m-%d")
