"""
宏观经济指标提供者 V2 - 多数据源版本
优先使用 FRED API（稳定可靠），降级到 YFinance
"""
import requests as req_sync
import yfinance as yf
from datetime import datetime
import asyncio
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from .base_provider import BaseIndicatorProvider, logger
from config import settings
from app.infra.executor import run_sync
from app.services.fred_api_config_service import get_fred_api_key

@dataclass(frozen=True)
class MacroIndicatorSource:
    fred_id: str | None
    yf_ticker: str | None
    indicator_id: str


MACRO_INDICATOR_SOURCES = [
    MacroIndicatorSource("DGS10", "^TNX", "US10Y"),
    MacroIndicatorSource("DGS2", None, "US02Y"),
    MacroIndicatorSource("NASDAQCOM", "^IXIC", "NASDAQ"),
    MacroIndicatorSource("BAMLH0A0HYM2", None, "HY_SPREAD"),
    MacroIndicatorSource("FEDFUNDS", None, "FED_RATE"),
    MacroIndicatorSource("WALCL", None, "FED_BALANCE"),
    MacroIndicatorSource("WTREGEN", None, "TGA"),
    MacroIndicatorSource("RRPONTSYD", None, "ONRRP"),
    MacroIndicatorSource("SOFR", None, "SOFR"),
    MacroIndicatorSource("M2SL", None, "M2"),
    MacroIndicatorSource("VIXCLS", "^VIX", "VIX"),
    MacroIndicatorSource("DTWEXBGS", None, "DXY"),
    MacroIndicatorSource("DCOILWTICO", "CL=F", "WTI"),
]


class MacroProviderV2(BaseIndicatorProvider):
    """
    宏观经济指标提供者（多源版本）
    数据源优先级：
    1. FRED API (官方数据，最稳定)
    2. Alpha Vantage (备用)
    3. YFinance (最后选择)
    """

    def __init__(self):
        super().__init__()
        self.av_api_key = settings.ALPHA_VANTAGE_API_KEY

    @property
    def fred_api_key(self) -> str:
        return get_fred_api_key()

    async def _fetch_fred_api(self, series_id: str, indicator_id: str) -> Optional[Dict[str, Any]]:
        """
        从 FRED 官方 API 获取数据（使用 sync requests 在线程池中执行，避免 httpx async TLS 问题）
        """
        fred_api_key = self.fred_api_key
        if not fred_api_key:
            logger.warning("FRED_API_KEY not configured, skipping FRED source")
            return None

        def _get():
            url = settings.FRED_API_URL
            params = {
                'series_id': series_id,
                'api_key': fred_api_key,
                'file_type': 'json',
                'sort_order': 'desc',
                'limit': 10
            }
            res = req_sync.get(url, params=params, timeout=settings.FRED_REQUEST_TIMEOUT)
            if res.status_code == 200:
                data = res.json()
                observations = data.get('observations', [])
                for latest in observations:
                    value_str = latest.get('value')
                    if value_str == '.' or not value_str:
                        continue
                    return {
                        "indicator_id": indicator_id,
                        "timestamp": datetime.strptime(latest['date'], '%Y-%m-%d'),
                        "value": float(value_str)
                    }
            return None

        try:
            return await run_sync(_get)
        except Exception as e:
            logger.error(f"Failed to fetch FRED {series_id}: {e}")

        return None

    async def _fetch_yfinance_ticker(self, ticker: str, indicator_id: str) -> Optional[Dict[str, Any]]:
        """从 Yahoo Finance 拉取（降级备用）"""
        try:
            def _get():
                # 不传 session，让 yfinance 自动使用 curl_cffi
                tkr = yf.Ticker(ticker)
                hist = tkr.history(period="5d")
                if hist.empty:
                    return None
                last_row = hist.iloc[-1]
                dt = last_row.name.to_pydatetime()
                val = float(last_row['Close'])
                return {
                    "indicator_id": indicator_id,
                    "timestamp": dt,
                    "value": val
                }

            return await run_sync(_get)

        except Exception as e:
            logger.error(f"Failed to fetch YFinance {ticker}: {e}")
            return None

    async def _get_indicator_with_fallback(self,
                                          fred_id: Optional[str],
                                          yf_ticker: str | None,
                                          indicator_id: str) -> Optional[Dict[str, Any]]:
        """
        多源降级获取
        优先 FRED -> 降级 YFinance
        """
        # 尝试 FRED
        if fred_id and self.fred_api_key:
            result = await self._fetch_fred_api(fred_id, indicator_id)
            if result:
                logger.info(f"[OK] {indicator_id} from FRED")
                return result

        if not yf_ticker:
            return None

        # 降级到 YFinance
        logger.info(f"[FALLBACK] {indicator_id} fallback to YFinance")
        await asyncio.sleep(settings.YFINANCE_REQUEST_DELAY)  # 限流延迟
        result = await self._fetch_yfinance_ticker(yf_ticker, indicator_id)
        if result:
            logger.info(f"[OK] {indicator_id} from YFinance")
        return result

    async def fetch_data(self) -> List[Dict[str, Any]]:
        results = []

        for source in MACRO_INDICATOR_SOURCES:
            result = await self._get_indicator_with_fallback(
                source.fred_id,
                source.yf_ticker,
                source.indicator_id,
            )

            if result:
                results.append(result)

        return results

if __name__ == "__main__":
    async def main():
        p = MacroProviderV2()
        data = await p.fetch_data()
        for d in data:
            print(f"{d['indicator_id']:15} | {d['timestamp']} | {d['value']}")
    asyncio.run(main())
