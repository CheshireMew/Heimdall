from __future__ import annotations

import csv
import io
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

from app.domain.market.index_catalog import IndexInstrument
from config import settings
from utils.logger import logger


@dataclass(frozen=True)
class IndexFetchResult:
    data: list[list[float]]
    source: str
    is_close_only: bool = False


class IndexHistorySources:
    def fetch_history(
        self,
        instrument: IndexInstrument,
        start_dt: datetime,
        end_dt: datetime,
    ) -> IndexFetchResult:
        providers = [
            self._fetch_sina_hk_history,
            self._fetch_sina_cn_history,
            self._fetch_sina_us_history,
            self._fetch_eastmoney_history,
            self._fetch_sohu_history,
            self._fetch_baostock_history,
            self._fetch_cboe_history,
            self._fetch_yfinance_history,
            self.fetch_fred_history,
        ]
        errors: list[str] = []
        for provider in providers:
            try:
                result = provider(instrument, start_dt, end_dt)
            except Exception as exc:
                safe_error = self._safe_error(exc)
                errors.append(f"{provider.__name__}: {safe_error}")
                logger.warning(f"指数数据源失败 {instrument.symbol} {provider.__name__}: {safe_error}")
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
        provider_name = instrument.pricing_provider
        if provider_name == "sina_us_etf":
            return self._fetch_sina_us_etf_history(instrument, start_dt, end_dt)
        if provider_name == "sina_hk_etf":
            return self._fetch_sina_hk_etf_history(instrument, start_dt, end_dt)
        if provider_name == "sina_cn_etf":
            return self._fetch_sina_cn_etf_history(instrument, start_dt, end_dt)
        return IndexFetchResult(data=[], source="none")

    def fetch_fred_history(
        self,
        instrument: IndexInstrument,
        start_dt: datetime,
        end_dt: datetime,
    ) -> IndexFetchResult:
        if not instrument.fred_series_id:
            return IndexFetchResult(data=[], source="fred")

        if settings.FRED_API_KEY:
            result = self._fetch_fred_api_history(instrument, start_dt, end_dt)
            if result.data:
                return result

        response = requests.get(
            "https://fred.stlouisfed.org/graph/fredgraph.csv",
            params={"id": instrument.fred_series_id},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=settings.FRED_REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        reader = csv.DictReader(io.StringIO(response.text))
        data: list[list[float]] = []
        for row in reader:
            date_text = row.get("observation_date") or row.get("DATE") or row.get("date")
            value_text = row.get(instrument.fred_series_id)
            if not date_text or not value_text or value_text == ".":
                continue
            row_dt = self._parse_date(date_text)
            if row_dt < start_dt or row_dt > end_dt:
                continue
            value = float(value_text)
            data.append([self._to_ms(row_dt), value, value, value, value, 0.0])
        return IndexFetchResult(data=data, source="fred", is_close_only=True)

    def fetch_usd_fx_rates(
        self,
        currency: str,
        start_dt: datetime,
        end_dt: datetime,
    ) -> dict[str, float]:
        response = requests.get(
            f"https://api.frankfurter.app/{start_dt.strftime('%Y-%m-%d')}..{end_dt.strftime('%Y-%m-%d')}",
            params={"from": currency, "to": "USD"},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=settings.FRED_REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
        rates = payload.get("rates") or {}
        return {
            date_text: float((values or {}).get("USD"))
            for date_text, values in rates.items()
            if (values or {}).get("USD") is not None
        }

    def _fetch_fred_api_history(
        self,
        instrument: IndexInstrument,
        start_dt: datetime,
        end_dt: datetime,
    ) -> IndexFetchResult:
        response = requests.get(
            settings.FRED_API_URL,
            params={
                "series_id": instrument.fred_series_id,
                "api_key": settings.FRED_API_KEY,
                "file_type": "json",
                "observation_start": start_dt.strftime("%Y-%m-%d"),
                "observation_end": end_dt.strftime("%Y-%m-%d"),
            },
            timeout=settings.FRED_REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data: list[list[float]] = []
        for row in response.json().get("observations", []):
            value_text = row.get("value")
            if not value_text or value_text == ".":
                continue
            value = float(value_text)
            data.append([
                self._to_ms(self._parse_date(row["date"])),
                value,
                value,
                value,
                value,
                0.0,
            ])
        return IndexFetchResult(data=data, source="fred", is_close_only=True)

    def _fetch_sina_us_etf_history(
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
            data=self._frame_to_ohlcv(
                frame=frame,
                start_dt=start_dt,
                end_dt=end_dt,
                volume_field="volume",
            ),
            source="sina_us_etf",
        )

    def _fetch_sina_hk_etf_history(
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
            data=self._frame_to_ohlcv(
                frame=frame,
                start_dt=start_dt,
                end_dt=end_dt,
                volume_field="volume",
            ),
            source="sina_hk_etf",
        )

    def _fetch_sina_cn_etf_history(
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
            data=self._frame_to_ohlcv(
                frame=frame,
                start_dt=start_dt,
                end_dt=end_dt,
                volume_field="volume",
            ),
            source="sina_cn_etf",
        )

    def _fetch_sina_hk_history(
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
            data=self._frame_to_ohlcv(
                frame=frame,
                start_dt=start_dt,
                end_dt=end_dt,
                volume_field="volume",
            ),
            source="sina_hk",
        )

    def _fetch_sina_cn_history(
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
            data=self._frame_to_ohlcv(
                frame=frame,
                start_dt=start_dt,
                end_dt=end_dt,
                volume_field="volume",
            ),
            source="sina_cn",
        )

    def _fetch_sina_us_history(
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
            data=self._frame_to_ohlcv(
                frame=frame,
                start_dt=start_dt,
                end_dt=end_dt,
                volume_field="volume",
            ),
            source="sina_us",
        )

    def _fetch_eastmoney_history(
        self,
        instrument: IndexInstrument,
        start_dt: datetime,
        end_dt: datetime,
    ) -> IndexFetchResult:
        if not instrument.eastmoney_secid:
            return IndexFetchResult(data=[], source="eastmoney")

        params = {
            "secid": instrument.eastmoney_secid,
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56,f57",
            "klt": "101",
            "fqt": "0",
            "beg": start_dt.strftime("%Y%m%d"),
            "end": end_dt.strftime("%Y%m%d"),
        }
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://quote.eastmoney.com/",
        }
        response = None
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                response = requests.get(
                    "https://push2his.eastmoney.com/api/qt/stock/kline/get",
                    params=params,
                    headers=headers,
                    timeout=settings.FRED_REQUEST_TIMEOUT,
                )
                break
            except requests.RequestException as exc:
                last_error = exc
                if attempt < 2:
                    time.sleep(0.8 * (attempt + 1))
        if response is None:
            raise last_error or RuntimeError("Eastmoney request failed")
        response.raise_for_status()
        payload = response.json()
        rows = ((payload.get("data") or {}).get("klines") or [])
        return IndexFetchResult(
            data=[self._parse_eastmoney_row(row) for row in rows],
            source="eastmoney",
        )

    def _fetch_sohu_history(
        self,
        instrument: IndexInstrument,
        start_dt: datetime,
        end_dt: datetime,
    ) -> IndexFetchResult:
        if not instrument.sohu_code:
            return IndexFetchResult(data=[], source="sohu")

        response = requests.get(
            "https://q.stock.sohu.com/hisHq",
            params={
                "code": instrument.sohu_code,
                "start": start_dt.strftime("%Y%m%d"),
                "end": end_dt.strftime("%Y%m%d"),
                "stat": "1",
                "order": "D",
                "period": "d",
                "rt": "json",
            },
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=settings.FRED_REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list) or not payload:
            return IndexFetchResult(data=[], source="sohu")

        rows = payload[0].get("hq") or []
        data = [self._parse_sohu_row(row) for row in rows if len(row) >= 8]
        data.sort(key=lambda item: item[0])
        return IndexFetchResult(data=data, source="sohu")

    def _fetch_baostock_history(
        self,
        instrument: IndexInstrument,
        start_dt: datetime,
        end_dt: datetime,
    ) -> IndexFetchResult:
        if not instrument.baostock_code:
            return IndexFetchResult(data=[], source="baostock")

        try:
            import baostock as bs
        except ImportError:
            return IndexFetchResult(data=[], source="baostock")

        login_result = bs.login()
        if login_result.error_code != "0":
            return IndexFetchResult(data=[], source="baostock")

        try:
            query = bs.query_history_k_data_plus(
                instrument.baostock_code,
                "date,open,high,low,close,volume",
                start_date=start_dt.strftime("%Y-%m-%d"),
                end_date=end_dt.strftime("%Y-%m-%d"),
                frequency="d",
                adjustflag="3",
            )
            if query.error_code != "0":
                return IndexFetchResult(data=[], source="baostock")

            data: list[list[float]] = []
            while query.next():
                row = query.get_row_data()
                if len(row) < 6 or not row[1] or not row[4]:
                    continue
                row_dt = self._parse_date(row[0])
                data.append([
                    self._to_ms(row_dt),
                    float(row[1]),
                    float(row[2]),
                    float(row[3]),
                    float(row[4]),
                    float(row[5] or 0.0),
                ])
            return IndexFetchResult(data=data, source="baostock")
        finally:
            bs.logout()

    def _fetch_cboe_history(
        self,
        instrument: IndexInstrument,
        start_dt: datetime,
        end_dt: datetime,
    ) -> IndexFetchResult:
        if not instrument.cboe_csv_url:
            return IndexFetchResult(data=[], source="cboe")

        response = requests.get(
            instrument.cboe_csv_url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=settings.FRED_REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        reader = csv.DictReader(io.StringIO(response.text))
        close_only = "OPEN" not in (reader.fieldnames or [])
        value_column = next((name for name in (reader.fieldnames or []) if name != "DATE"), None)
        data: list[list[float]] = []
        for row in reader:
            date_text = row.get("DATE")
            if not date_text or not value_column:
                continue
            row_dt = datetime.strptime(date_text, "%m/%d/%Y").replace(tzinfo=timezone.utc)
            if row_dt < start_dt or row_dt > end_dt:
                continue
            if close_only:
                value = float(row[value_column])
                data.append([self._to_ms(row_dt), value, value, value, value, 0.0])
                continue
            data.append([
                self._to_ms(row_dt),
                float(row["OPEN"]),
                float(row["HIGH"]),
                float(row["LOW"]),
                float(row["CLOSE"]),
                0.0,
            ])
        return IndexFetchResult(data=data, source="cboe", is_close_only=close_only)

    def _fetch_yfinance_history(
        self,
        instrument: IndexInstrument,
        start_dt: datetime,
        end_dt: datetime,
    ) -> IndexFetchResult:
        if not instrument.yfinance_symbol:
            return IndexFetchResult(data=[], source="yfinance")

        import yfinance as yf

        history = yf.Ticker(instrument.yfinance_symbol).history(
            start=start_dt.strftime("%Y-%m-%d"),
            end=(end_dt + timedelta(days=1)).strftime("%Y-%m-%d"),
            interval="1d",
            auto_adjust=False,
        )
        if history.empty:
            return IndexFetchResult(data=[], source="yfinance")

        data: list[list[float]] = []
        for row_date, row in history.iterrows():
            if row[["Open", "High", "Low", "Close"]].isna().any():
                continue
            ts = self._date_to_ms(row_date.to_pydatetime())
            data.append([
                ts,
                float(row["Open"]),
                float(row["High"]),
                float(row["Low"]),
                float(row["Close"]),
                float(row.get("Volume") or 0.0),
            ])
        return IndexFetchResult(data=data, source="yfinance")

    def _parse_eastmoney_row(self, row: str) -> list[float]:
        date_text, open_text, close_text, high_text, low_text, volume_text, *_rest = row.split(",")
        return [
            self._to_ms(self._parse_date(date_text)),
            float(open_text),
            float(high_text),
            float(low_text),
            float(close_text),
            float(volume_text),
        ]

    def _parse_sohu_row(self, row: list[str]) -> list[float]:
        return [
            self._to_ms(self._parse_date(row[0])),
            float(row[1]),
            float(row[6]),
            float(row[5]),
            float(row[2]),
            float(row[7]),
        ]

    def _frame_to_ohlcv(
        self,
        *,
        frame,
        start_dt: datetime,
        end_dt: datetime,
        volume_field: str,
    ) -> list[list[float]]:
        if frame is None or frame.empty:
            return []

        data: list[list[float]] = []
        for row in frame.to_dict("records"):
            if any(row.get(field) is None for field in ("date", "open", "high", "low", "close")):
                continue
            row_dt = self._normalize_date_value(row["date"])
            if row_dt < start_dt or row_dt > end_dt:
                continue
            data.append([
                self._to_ms(row_dt),
                float(row["open"]),
                float(row["high"]),
                float(row["low"]),
                float(row["close"]),
                float(row.get(volume_field) or 0.0),
            ])
        data.sort(key=lambda item: item[0])
        return data

    def _parse_date(self, value: str) -> datetime:
        return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)

    def _normalize_date_value(self, value: Any) -> datetime:
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc)
        return self._parse_date(str(value))

    def _safe_error(self, exc: Exception) -> str:
        message = str(exc)
        if settings.FRED_API_KEY:
            message = message.replace(settings.FRED_API_KEY, "***")
        return message

    def _date_to_ms(self, value: datetime) -> int:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return self._to_ms(value.astimezone(timezone.utc))

    def _to_ms(self, value: datetime) -> int:
        return int(value.timestamp() * 1000)
