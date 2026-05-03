from __future__ import annotations

import time
from datetime import datetime
from typing import Callable

from config import settings
from app.infra.cache import RedisService
from app.domain.market.constants import KEY_PREFIX_KLINE
from app.domain.market.symbol_catalog import get_market_symbol_source
from utils.logger import logger

from .exchange_gateway import ExchangeGateway
from .history_ranges import collect_missing_ranges, is_recent_cache_usable
from .kline_store import KlineStore


class MarketDataService:
    def __init__(
        self,
        exchange_gateway: ExchangeGateway | None = None,
        kline_store: KlineStore | None = None,
        cache_service: RedisService | None = None,
    ) -> None:
        if exchange_gateway is None or kline_store is None:
            raise ValueError("MarketDataService 需要显式注入 exchange_gateway 和 kline_store")
        self.exchange_gateway = exchange_gateway
        self.kline_store = kline_store
        self.cache_service = cache_service
        self._exchange_gateways: dict[str, ExchangeGateway] = {
            self.exchange_gateway.exchange_id: self.exchange_gateway,
        }

    def _resolve_market_source(self, symbol: str):
        return get_market_symbol_source(symbol) or get_market_symbol_source(f"{symbol}/USDT")

    def _storage_symbol(self, symbol: str) -> str:
        source = self._resolve_market_source(symbol)
        return source.storage_symbol if source else symbol

    def _fetch_symbol(self, symbol: str) -> str:
        source = self._resolve_market_source(symbol)
        return source.symbol if source else symbol

    def _gateway_for_symbol(self, symbol: str) -> ExchangeGateway:
        source = self._resolve_market_source(symbol)
        exchange_id = source.exchange_id if source else self.exchange_gateway.exchange_id
        gateway = self._exchange_gateways.get(exchange_id)
        if gateway:
            return gateway
        gateway = ExchangeGateway(exchange_id=exchange_id)
        self._exchange_gateways[exchange_id] = gateway
        return gateway

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
            storage_symbol = self._storage_symbol(symbol)
            fetch_symbol = self._fetch_symbol(symbol)
            gateway = self._gateway_for_symbol(symbol)
            cache_key = f"{KEY_PREFIX_KLINE}:{storage_symbol}:{timeframe}:{limit}"
            cached_data = self.cache_service.get(cache_key) if self.cache_service is not None else None
            if cached_data:
                cache_hit = True
                return cached_data

            data, attempts = gateway.fetch_ohlcv(fetch_symbol, timeframe, limit=limit)
            if data and self.cache_service is not None:
                self.cache_service.set(cache_key, data, ttl=settings.REDIS_KLINE_TTL)
            return data
        except Exception as e:
            logger.error(f"K线数据获取错误 (Redis/Exchange): {e}")
            fetch_symbol = self._fetch_symbol(symbol)
            gateway = self._gateway_for_symbol(symbol)
            data, attempts = gateway.fetch_ohlcv(fetch_symbol, timeframe, limit=limit)
            return data
        finally:
            elapsed = time.time() - start_time
            logger.debug(
                f"[metrics] get_kline_data symbol={symbol} tf={timeframe} limit={limit} "
                f"cache_hit={cache_hit} attempts={attempts} elapsed={elapsed:.2f}s"
            )

    def get_live_kline_data(
        self,
        symbol: str,
        timeframe: str = settings.TIMEFRAME,
        limit: int = settings.LIMIT,
        *,
        max_retries: int | None = None,
    ) -> list[list[float]]:
        start_time = time.time()
        attempts = 0
        try:
            storage_symbol = self._storage_symbol(symbol)
            fetch_symbol = self._fetch_symbol(symbol)
            gateway = self._gateway_for_symbol(symbol)
            cache_key = f"{KEY_PREFIX_KLINE}:{storage_symbol}:{timeframe}:{limit}"
            data, attempts = gateway.fetch_ohlcv(fetch_symbol, timeframe, limit=limit, max_retries=max_retries)
            if data and self.cache_service is not None:
                self.cache_service.set(cache_key, data, ttl=settings.REDIS_KLINE_TTL)
            return data
        except Exception as e:
            logger.error(f"实时K线获取错误 (Exchange): {e}")
            return []
        finally:
            elapsed = time.time() - start_time
            logger.debug(
                f"[metrics] get_live_kline_data symbol={symbol} tf={timeframe} limit={limit} "
                f"attempts={attempts} elapsed={elapsed:.2f}s"
            )

    def get_history_data(self, symbol: str, timeframe: str, end_ts: int, limit: int = 500) -> list[list[float]]:
        start_time = time.time()
        try:
            return self.kline_store.get_before(self._storage_symbol(symbol), timeframe, end_ts, limit)
        except Exception as e:
            logger.error(f"历史数据查询失败: {e}")
            raise
        finally:
            elapsed = time.time() - start_time
            logger.debug(f"[metrics] get_history_data symbol={symbol} tf={timeframe} limit={limit} elapsed={elapsed:.2f}s")

    def get_recent_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = settings.LIMIT,
        *,
        allow_cached_response: bool = False,
        live_max_retries: int | None = None,
    ) -> list[list[float]]:
        end_ts = int(time.time() * 1000) + 1
        try:
            cached = self.get_history_data(symbol, timeframe, end_ts, limit)
        except Exception as exc:
            logger.warning(f"最近 K 线缓存读取失败，改用交易所实时数据: {exc}")
            cached = []
        if allow_cached_response and is_recent_cache_usable(
            cached=cached,
            timeframe=timeframe,
            limit=limit,
            now_ms=end_ts,
        ):
            return cached[-limit:]

        live = self.get_live_kline_data(symbol, timeframe, limit=limit, max_retries=live_max_retries)
        if live:
            merged = self._merge_klines(cached, live)
            try:
                self.kline_store.save(self._storage_symbol(symbol), timeframe, live)
            except Exception as exc:
                logger.warning(f"最近 K 线回写缓存失败: {exc}")
            return merged[-limit:]
        return cached[-limit:]

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
        end_ts_exclusive = end_ts + 1
        range_start = time.time()
        cached_klines: list[list[float]] = []
        new_data: list[list[float]] = []
        missing_ranges: list[tuple[int, int]] = []
        storage_symbol = self._storage_symbol(symbol)

        try:
            try:
                cached_klines = self.kline_store.get_range(storage_symbol, timeframe, start_ts, end_ts)
            except Exception as exc:
                logger.error(f"缓存读取失败，改用交易所数据: {exc}")
                return self._fetch_gap(symbol, timeframe, start_ts, end_ts_exclusive)

            logger.info(f"缓存命中: {len(cached_klines)} 条 ({storage_symbol})")

            missing_ranges = collect_missing_ranges(
                cached_klines=cached_klines,
                timeframe=timeframe,
                start_ts=start_ts,
                end_ts_exclusive=end_ts_exclusive,
            )
            for gap_start, gap_end in missing_ranges:
                new_data.extend(self._fetch_gap(symbol, timeframe, gap_start, gap_end))

            if new_data:
                logger.info(f"下载新数据: {len(new_data)} 条")
                try:
                    if persist_klines:
                        persist_klines(storage_symbol, timeframe, new_data)
                    else:
                        self.kline_store.save(storage_symbol, timeframe, new_data)
                except Exception as exc:
                    # 历史数据写缓存只是加速下一次读取；不能因为回写失败丢掉本次已经拉到的真实行情。
                    logger.warning(f"历史 K 线回写缓存失败: {exc}")

            merged = {k[0]: k for k in cached_klines}
            for row in new_data:
                merged[row[0]] = row

            final_data = sorted(merged.values(), key=lambda x: x[0])
            return [row for row in final_data if start_ts <= row[0] <= end_ts]
        finally:
            elapsed = time.time() - range_start
            logger.debug(
                f"[metrics] fetch_ohlcv_range symbol={symbol} tf={timeframe} "
                f"cached={len(cached_klines)} new={len(new_data)} gaps={len(missing_ranges)} elapsed={elapsed:.2f}s"
            )

    def get_cached_ohlcv_range(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
    ) -> list[list[float]]:
        start_ts = int(start_date.timestamp() * 1000)
        end_ts = int(end_date.timestamp() * 1000)
        range_start = time.time()
        try:
            return self.kline_store.get_range(self._storage_symbol(symbol), timeframe, start_ts, end_ts)
        finally:
            elapsed = time.time() - range_start
            logger.debug(
                f"[metrics] get_cached_ohlcv_range symbol={symbol} tf={timeframe} "
                f"elapsed={elapsed:.2f}s"
            )

    def fetch_live_ohlcv_range(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
    ) -> list[list[float]]:
        start_ts = int(start_date.timestamp() * 1000)
        end_ts = int(end_date.timestamp() * 1000)
        range_start = time.time()
        try:
            return self._fetch_gap(symbol, timeframe, start_ts, end_ts + 1)
        finally:
            elapsed = time.time() - range_start
            logger.debug(
                f"[metrics] fetch_live_ohlcv_range symbol={symbol} tf={timeframe} "
                f"elapsed={elapsed:.2f}s"
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
        fetch_symbol = self._fetch_symbol(symbol)
        gateway = self._gateway_for_symbol(symbol)

        while current_since < until:
            limit = settings.EXCHANGE_FETCH_LIMIT
            batch, _attempts = gateway.fetch_ohlcv(
                fetch_symbol,
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
            gateway.sleep_for_rate_limit()

            if len(batch) < limit:
                break

            if time.time() - task_start > gateway.max_task_seconds:
                logger.warning(f"[_fetch_gap] 超时终止 symbol={symbol} tf={timeframe} since={since} until={until}")
                break

        return data

    def _merge_klines(self, *batches: list[list[float]]) -> list[list[float]]:
        merged: dict[float, list[float]] = {}
        for batch in batches:
            for row in batch:
                if row:
                    merged[row[0]] = row
        return sorted(merged.values(), key=lambda item: item[0])
