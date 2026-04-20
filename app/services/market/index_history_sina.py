from __future__ import annotations

from datetime import datetime

from app.domain.market.index_catalog import IndexInstrument
from app.services.market.index_history_contracts import IndexFetchResult
from app.services.market.index_history_parsing import IndexHistoryParsing


class SinaIndexHistoryProvider(IndexHistoryParsing):
    def fetch_us_etf_history(
        self,
        instrument: IndexInstrument,
        start_dt: datetime,
        end_dt: datetime,
    ) -> IndexFetchResult:
        if not instrument.pricing_symbol:
            return IndexFetchResult(data=[], source="sina_us_etf")
        try:
            import akshare as ak
        except ImportError:
            return IndexFetchResult(data=[], source="sina_us_etf")

        frame = ak.stock_us_daily(symbol=instrument.pricing_symbol)
        return IndexFetchResult(
            data=self.frame_to_ohlcv(
                frame=frame,
                start_dt=start_dt,
                end_dt=end_dt,
                volume_field="volume",
            ),
            source="sina_us_etf",
        )

    def fetch_hk_etf_history(
        self,
        instrument: IndexInstrument,
        start_dt: datetime,
        end_dt: datetime,
    ) -> IndexFetchResult:
        if not instrument.pricing_symbol:
            return IndexFetchResult(data=[], source="sina_hk_etf")
        try:
            import akshare as ak
        except ImportError:
            return IndexFetchResult(data=[], source="sina_hk_etf")

        frame = ak.stock_hk_daily(symbol=instrument.pricing_symbol, adjust="")
        return IndexFetchResult(
            data=self.frame_to_ohlcv(
                frame=frame,
                start_dt=start_dt,
                end_dt=end_dt,
                volume_field="volume",
            ),
            source="sina_hk_etf",
        )

    def fetch_cn_etf_history(
        self,
        instrument: IndexInstrument,
        start_dt: datetime,
        end_dt: datetime,
    ) -> IndexFetchResult:
        if not instrument.pricing_symbol:
            return IndexFetchResult(data=[], source="sina_cn_etf")
        try:
            import akshare as ak
        except ImportError:
            return IndexFetchResult(data=[], source="sina_cn_etf")

        frame = ak.fund_etf_hist_sina(symbol=instrument.pricing_symbol)
        return IndexFetchResult(
            data=self.frame_to_ohlcv(
                frame=frame,
                start_dt=start_dt,
                end_dt=end_dt,
                volume_field="volume",
            ),
            source="sina_cn_etf",
        )

    def fetch_hk_history(
        self,
        instrument: IndexInstrument,
        start_dt: datetime,
        end_dt: datetime,
    ) -> IndexFetchResult:
        if not instrument.sina_hk_symbol:
            return IndexFetchResult(data=[], source="sina_hk")

        try:
            import akshare as ak
        except ImportError:
            return IndexFetchResult(data=[], source="sina_hk")

        frame = ak.stock_hk_index_daily_sina(symbol=instrument.sina_hk_symbol)
        if frame.empty:
            return IndexFetchResult(data=[], source="sina_hk")
        return IndexFetchResult(
            data=self.frame_to_ohlcv(
                frame=frame,
                start_dt=start_dt,
                end_dt=end_dt,
                volume_field="volume",
            ),
            source="sina_hk",
        )

    def fetch_cn_history(
        self,
        instrument: IndexInstrument,
        start_dt: datetime,
        end_dt: datetime,
    ) -> IndexFetchResult:
        if not instrument.sina_cn_symbol:
            return IndexFetchResult(data=[], source="sina_cn")

        try:
            import akshare as ak
        except ImportError:
            return IndexFetchResult(data=[], source="sina_cn")

        frame = ak.stock_zh_index_daily(symbol=instrument.sina_cn_symbol)
        if frame.empty:
            return IndexFetchResult(data=[], source="sina_cn")
        return IndexFetchResult(
            data=self.frame_to_ohlcv(
                frame=frame,
                start_dt=start_dt,
                end_dt=end_dt,
                volume_field="volume",
            ),
            source="sina_cn",
        )

    def fetch_us_history(
        self,
        instrument: IndexInstrument,
        start_dt: datetime,
        end_dt: datetime,
    ) -> IndexFetchResult:
        if not instrument.sina_us_symbol:
            return IndexFetchResult(data=[], source="sina_us")

        try:
            import akshare as ak
        except ImportError:
            return IndexFetchResult(data=[], source="sina_us")

        frame = ak.index_us_stock_sina(symbol=instrument.sina_us_symbol)
        if frame.empty:
            return IndexFetchResult(data=[], source="sina_us")
        return IndexFetchResult(
            data=self.frame_to_ohlcv(
                frame=frame,
                start_dt=start_dt,
                end_dt=end_dt,
                volume_field="volume",
            ),
            source="sina_us",
        )
