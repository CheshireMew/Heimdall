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
from app.services.executor import run_sync

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
        self.fred_api_key = settings.FRED_API_KEY
        self.av_api_key = settings.ALPHA_VANTAGE_API_KEY

    async def _fetch_fred_api(self, series_id: str, indicator_id: str) -> Optional[Dict[str, Any]]:
        """
        从 FRED 官方 API 获取数据（使用 sync requests 在线程池中执行，避免 httpx async TLS 问题）
        """
        if not self.fred_api_key:
            logger.warning("FRED_API_KEY not configured, skipping FRED source")
            return None

        def _get():
            url = settings.FRED_API_URL
            params = {
                'series_id': series_id,
                'api_key': self.fred_api_key,
                'file_type': 'json',
                'sort_order': 'desc',
                'limit': 1
            }
            res = req_sync.get(url, params=params, timeout=settings.FRED_REQUEST_TIMEOUT)
            if res.status_code == 200:
                data = res.json()
                observations = data.get('observations', [])
                if observations:
                    latest = observations[0]
                    value_str = latest.get('value')
                    if value_str == '.' or not value_str:
                        return None
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
                                          yf_ticker: str,
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

        # 降级到 YFinance
        logger.info(f"[FALLBACK] {indicator_id} fallback to YFinance")
        await asyncio.sleep(settings.YFINANCE_REQUEST_DELAY)  # 限流延迟
        result = await self._fetch_yfinance_ticker(yf_ticker, indicator_id)
        if result:
            logger.info(f"[OK] {indicator_id} from YFinance")
        return result

    async def fetch_data(self) -> List[Dict[str, Any]]:
        results = []

        # 指标配置 (FRED Series ID, YFinance Ticker, 输出ID)
        indicators = [
            # FRED Series ID, YF Ticker, Indicator ID
            ("DGS10", "^TNX", "US10Y"),           # 10年期美债收益率
            ("NASDAQCOM", "^IXIC", "NASDAQ"),     # 纳斯达克 (FRED有日频数据)
            ("BAMLH0A0HYM2", None, "HY_SPREAD"), # 高收益债利差（仅FRED）
            ("FEDFUNDS", None, "FED_RATE"),       # 联邦基金利率
            ("WALCL", None, "FED_BALANCE"),       # 美联储资产负债表总资产 (百万美元)
            # GOLD moved to CryptoGoldProvider (Binance PAXG/USDT)
        ]

        for fred_id, yf_ticker, indicator_id in indicators:
            if yf_ticker:  # 有YF备选
                result = await self._get_indicator_with_fallback(fred_id, yf_ticker, indicator_id)
            elif fred_id:  # 仅FRED
                result = await self._fetch_fred_api(fred_id, indicator_id)
            else:
                continue

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
