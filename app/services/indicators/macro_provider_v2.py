"""
宏观经济指标提供者 V2 - 多数据源版本
优先使用 FRED API（稳定可靠），降级到 YFinance
"""
import requests as req_sync
import yfinance as yf
from datetime import datetime, timedelta
import asyncio
from typing import List, Dict, Any, Optional
from .base_provider import BaseIndicatorProvider, logger
from config import settings
from app.domain.market.dli_catalog import MACRO_INDICATOR_SOURCES
from app.infra.executor import run_external_io
from app.services.fred_api_config_service import get_fred_api_key


class MacroProviderV2(BaseIndicatorProvider):
    """
    宏观经济指标提供者（多源版本）
    数据源优先级：
    1. FRED API (官方数据，最稳定)
    2. YFinance (fallback)
    """

    def __init__(self):
        super().__init__()

    @property
    def fred_api_key(self) -> str:
        return get_fred_api_key()

    async def _fetch_fred_api(self, series_id: str, indicator_id: str) -> Optional[List[Dict[str, Any]]]:
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
                'limit': 3650
            }
            res = req_sync.get(url, params=params, timeout=settings.FRED_REQUEST_TIMEOUT)
            if res.status_code == 200:
                data = res.json()
                observations = data.get('observations', [])
                points = []
                for latest in observations:
                    value_str = latest.get('value')
                    if value_str == '.' or not value_str:
                        continue
                    points.append(
                        {
                            "indicator_id": indicator_id,
                            "timestamp": datetime.strptime(latest['date'], '%Y-%m-%d'),
                            "value": float(value_str)
                        }
                    )
                return list(reversed(points)) if points else None
            return None

        try:
            return await run_external_io(_get)
        except Exception as e:
            logger.error(f"Failed to fetch FRED {series_id}: {e}")

        return None

    async def _fetch_treasury_tga(self) -> Optional[List[Dict[str, Any]]]:
        def _get():
            start_date = (datetime.now() - timedelta(days=3650)).strftime("%Y-%m-%d")
            url = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/operating_cash_balance"
            points_by_date: dict[datetime, float] = {}
            account_types = [
                "Federal Reserve Account",
                "Treasury General Account (TGA) Closing Balance",
            ]
            for account_type in account_types:
                page_number = 1
                total_pages = 1
                while page_number <= total_pages:
                    params = {
                        "fields": "record_date,account_type,open_today_bal,close_today_bal",
                        "filter": f"record_date:gte:{start_date},account_type:eq:{account_type}",
                        "sort": "record_date",
                        "page[number]": page_number,
                        "page[size]": 1000,
                    }
                    res = req_sync.get(
                        url,
                        params=params,
                        headers={"Accept": "application/json", "User-Agent": "Heimdall/1.0"},
                        timeout=settings.FRED_REQUEST_TIMEOUT,
                    )
                    if res.status_code != 200:
                        return None

                    payload = res.json()
                    total_pages = int(payload.get("meta", {}).get("total-pages") or 1)
                    for row in payload.get("data", []):
                        value_str = row.get("close_today_bal")
                        if value_str in (None, "", "null", "."):
                            value_str = row.get("open_today_bal")
                        if value_str in (None, "", "null", "."):
                            continue
                        timestamp = datetime.strptime(row["record_date"], "%Y-%m-%d")
                        points_by_date[timestamp] = float(value_str)
                    page_number += 1
            return [
                {"indicator_id": "TGA", "timestamp": timestamp, "value": value}
                for timestamp, value in sorted(points_by_date.items())
            ] or None

        try:
            return await run_external_io(_get)
        except Exception as e:
            logger.error(f"Failed to fetch Treasury TGA: {e}")
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

            return await run_external_io(_get)

        except Exception as e:
            logger.error(f"Failed to fetch YFinance {ticker}: {e}")
            return None

    async def _get_indicator_with_fallback(self,
                                          fred_id: Optional[str],
                                          yf_ticker: str | None,
                                          indicator_id: str) -> List[Dict[str, Any]]:
        """
        多源降级获取
        优先 FRED -> 降级 YFinance
        """
        if indicator_id == "TGA":
            result = await self._fetch_treasury_tga()
            if result:
                logger.info("[OK] TGA from Treasury Fiscal Data")
                return result

        # 尝试 FRED
        if fred_id and self.fred_api_key:
            result = await self._fetch_fred_api(fred_id, indicator_id)
            if result:
                logger.info(f"[OK] {indicator_id} from FRED")
                return result

        if not yf_ticker:
            return []

        # 降级到 YFinance
        logger.info(f"[FALLBACK] {indicator_id} fallback to YFinance")
        await asyncio.sleep(settings.YFINANCE_REQUEST_DELAY)  # 限流延迟
        result = await self._fetch_yfinance_ticker(yf_ticker, indicator_id)
        if result:
            logger.info(f"[OK] {indicator_id} from YFinance")
            return [result]
        return []

    async def fetch_data(self) -> List[Dict[str, Any]]:
        results = []

        for source in MACRO_INDICATOR_SOURCES:
            result = await self._get_indicator_with_fallback(
                source.fred_id,
                source.yf_ticker,
                source.indicator_id,
            )

            results.extend(result)

        return results

if __name__ == "__main__":
    async def main():
        p = MacroProviderV2()
        data = await p.fetch_data()
        for d in data:
            print(f"{d['indicator_id']:15} | {d['timestamp']} | {d['value']}")
    asyncio.run(main())
