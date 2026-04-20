from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from app.domain.market.index_catalog import IndexInstrument
from app.services.market.index_history_contracts import IndexFetchResult
from app.services.market.index_history_fred import FredIndexHistoryProvider
from app.services.market.index_history_http import (
    BaostockIndexHistoryProvider,
    CboeIndexHistoryProvider,
    EastmoneyIndexHistoryProvider,
    SohuIndexHistoryProvider,
    YFinanceIndexHistoryProvider,
)
from app.services.market.index_history_parsing import IndexHistoryParsing
from app.services.market.index_history_sina import SinaIndexHistoryProvider
from utils.logger import logger


HistoryProvider = Callable[[IndexInstrument, datetime, datetime], IndexFetchResult]


class IndexHistorySources(IndexHistoryParsing):
    def __init__(self) -> None:
        self.sina = SinaIndexHistoryProvider()
        self.fred = FredIndexHistoryProvider()
        self.providers: tuple[HistoryProvider, ...] = (
            self.sina.fetch_hk_history,
            self.sina.fetch_cn_history,
            self.sina.fetch_us_history,
            EastmoneyIndexHistoryProvider().fetch_history,
            SohuIndexHistoryProvider().fetch_history,
            BaostockIndexHistoryProvider().fetch_history,
            CboeIndexHistoryProvider().fetch_history,
            YFinanceIndexHistoryProvider().fetch_history,
            self.fred.fetch_history,
        )
        self.pricing_providers = {
            "sina_us_etf": self.sina.fetch_us_etf_history,
            "sina_hk_etf": self.sina.fetch_hk_etf_history,
            "sina_cn_etf": self.sina.fetch_cn_etf_history,
        }

    def fetch_history(
        self,
        instrument: IndexInstrument,
        start_dt: datetime,
        end_dt: datetime,
    ) -> IndexFetchResult:
        errors: list[str] = []
        for provider in self.providers:
            try:
                result = provider(instrument, start_dt, end_dt)
            except Exception as exc:
                safe_error = self.safe_error(exc)
                provider_name = getattr(provider, "__name__", provider.__class__.__name__)
                errors.append(f"{provider_name}: {safe_error}")
                logger.warning(f"指数数据源失败 {instrument.symbol} {provider_name}: {safe_error}")
                continue
            if result.data:
                return result

        logger.error(f"指数历史数据获取失败 {instrument.symbol}: {'; '.join(errors)}")
        return IndexFetchResult(data=[], source="none")

    def fetch_pricing_history(
        self,
        instrument: IndexInstrument,
        start_dt: datetime,
        end_dt: datetime,
    ) -> IndexFetchResult:
        provider = self.pricing_providers.get(instrument.pricing_provider or "")
        if provider is None:
            return IndexFetchResult(data=[], source="none")
        return provider(instrument, start_dt, end_dt)

    def fetch_fred_history(
        self,
        instrument: IndexInstrument,
        start_dt: datetime,
        end_dt: datetime,
    ) -> IndexFetchResult:
        return self.fred.fetch_history(instrument, start_dt, end_dt)

    def fetch_usd_fx_rates(
        self,
        currency: str,
        start_dt: datetime,
        end_dt: datetime,
    ) -> dict[str, float]:
        return self.fred.fetch_usd_fx_rates(currency, start_dt, end_dt)
