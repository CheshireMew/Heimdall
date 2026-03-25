from __future__ import annotations

import time
from datetime import datetime
from typing import Callable

from config import settings
from app.domain.market.constants import KEY_PREFIX_KLINE
from utils.logger import logger

from .exchange_gateway import ExchangeGateway
from .kline_store import KlineStore


class MarketDataService:
    def __init__(
        self,
        exchange_gateway: ExchangeGateway | None = None,
        kline_store: KlineStore | None = None,
    ) -> None:
        self.exchange_gateway = exchange_gateway or ExchangeGateway()
        self.kline_store = kline_store or KlineStore()

    def get_kline_data(
        self,
        symbol: str,
        timeframe: str = settings.TIMEFRAME,
        limit: int = settings.LIMIT,
    ) -> list[list[float]]:
        start_time = time.time()
        cache_hit = False
        attempts = 0
        try:
            from app.infra.cache import redis_service

            cache_key = f"{KEY_PREFIX_KLINE}:{symbol}:{timeframe}:{limit}"
            cached_data = redis_service.get(cache_key)
            if cached_data:
                cache_hit = True
                return cached_data

            data, attempts = self.exchange_gateway.fetch_ohlcv(symbol, timeframe, limit=limit)
            if data:
                redis_service.set(cache_key, data, ttl=settings.REDIS_KLINE_TTL)
            return data
        except ImportError:
            data, attempts = self.exchange_gateway.fetch_ohlcv(symbol, timeframe, limit=limit)
            return data
        except Exception as e:
            logger.error(f"K线数据获取错误 (Redis/Exchange): {e}")
            data, attempts = self.exchange_gateway.fetch_ohlcv(symbol, timeframe, limit=limit)
            return data
        finally:
            elapsed = time.time() - start_time
            logger.debug(
                f"[metrics] get_kline_data symbol={symbol} tf={timeframe} limit={limit} "
                f"cache_hit={cache_hit} attempts={attempts} elapsed={elapsed:.2f}s"
            )

    def get_history_data(self, symbol: str, timeframe: str, end_ts: int, limit: int = 500) -> list[list[float]]:
        start_time = time.time()
        try:
            return self.kline_store.get_before(symbol, timeframe, end_ts, limit)
        except Exception as e:
            logger.error(f"历史数据查询失败: {e}")
            return []
        finally:
            elapsed = time.time() - start_time
            logger.debug(f"[metrics] get_history_data symbol={symbol} tf={timeframe} limit={limit} elapsed={elapsed:.2f}s")

    def fetch_ohlcv_range(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
        persist_klines: Callable[[str, str, list[list[float]]], None] | None = None,
    ) -> list[list[float]]:
        start_ts = int(start_date.timestamp() * 1000)
        end_ts = int(end_date.timestamp() * 1000)
        range_start = time.time()
        cached_klines: list[list[float]] = []
        new_data: list[list[float]] = []

        try:
            cached_klines = self.kline_store.get_range(symbol, timeframe, start_ts, end_ts)
            min_cached = cached_klines[0][0] if cached_klines else None
            max_cached = cached_klines[-1][0] if cached_klines else None

            logger.info(f"缓存命中: {len(cached_klines)} 条 ({symbol})")

            if min_cached is None or start_ts < min_cached:
                target_end = min_cached if min_cached else end_ts
                new_data.extend(self._fetch_gap(symbol, timeframe, start_ts, target_end))

            if max_cached is not None and end_ts > max_cached:
                new_data.extend(self._fetch_gap(symbol, timeframe, max_cached + 1, end_ts))

            if new_data:
                logger.info(f"下载新数据: {len(new_data)} 条")
                if persist_klines:
                    persist_klines(symbol, timeframe, new_data)
                else:
                    self.kline_store.save(symbol, timeframe, new_data)

            merged = {k[0]: k for k in cached_klines}
            for row in new_data:
                merged[row[0]] = row

            final_data = sorted(merged.values(), key=lambda x: x[0])
            return [row for row in final_data if start_ts <= row[0] <= end_ts]
        except Exception as e:
            logger.error(f"带缓存数据获取失败: {e}")
            return self._fetch_gap(symbol, timeframe, start_ts, end_ts)
        finally:
            elapsed = time.time() - range_start
            logger.debug(
                f"[metrics] fetch_ohlcv_range symbol={symbol} tf={timeframe} "
                f"cached={len(cached_klines)} new={len(new_data)} elapsed={elapsed:.2f}s"
            )

    def save_klines_background(self, symbol: str, timeframe: str, klines: list[list[float]]) -> None:
        try:
            self.kline_store.save(symbol, timeframe, klines)
            logger.info(f"[Background] Saved {len(klines)} klines for {symbol}")
        except Exception as e:
            logger.error(f"[Background] Save failed: {e}")

    def _fetch_gap(self, symbol: str, timeframe: str, since: int, until: int) -> list[list[float]]:
        data: list[list[float]] = []
        current_since = since
        task_start = time.time()

        while current_since < until:
            limit = settings.EXCHANGE_FETCH_LIMIT
            batch, _attempts = self.exchange_gateway.fetch_ohlcv(
                symbol,
                timeframe,
                since=current_since,
                limit=limit,
            )

            if not batch:
                break

            filtered = [row for row in batch if row[0] < until]
            if not filtered:
                break

            data.extend(filtered)
            last_ts = filtered[-1][0]
            if last_ts < current_since:
                break

            current_since = last_ts + 1
            self.exchange_gateway.sleep_for_rate_limit()

            if len(batch) < limit:
                break

            if time.time() - task_start > self.exchange_gateway.max_task_seconds:
                logger.warning(f"[_fetch_gap] 超时终止 symbol={symbol} tf={timeframe} since={since} until={until}")
                break

        return data
