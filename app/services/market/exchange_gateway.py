from __future__ import annotations

import threading
import time
from typing import Optional, Tuple

import ccxt

from config import settings
from utils.logger import logger


class ExchangeGateway:
    def __init__(self, exchange_id: str = settings.EXCHANGE_ID) -> None:
        self.exchange_id = exchange_id
        self.max_retries = settings.EXCHANGE_MAX_RETRIES
        self.retry_delay = settings.EXCHANGE_RETRY_DELAY
        self.max_task_seconds = settings.EXCHANGE_TASK_TIMEOUT
        self._local = threading.local()
        self._exchange_config = {
            "enableRateLimit": True,
            "options": {
                "defaultType": "spot",
            },
        }

        if not hasattr(ccxt, exchange_id):
            logger.error(f"不支持的交易所 ID: {exchange_id}")
            raise ValueError(f"Unsupported exchange: {exchange_id}")

        logger.info(f"已连接到交易所: {exchange_id}")

    @property
    def exchange(self):
        if not hasattr(self._local, "exchange"):
            exchange_class = getattr(ccxt, self.exchange_id)
            self._local.exchange = exchange_class(self._exchange_config.copy())
        return self._local.exchange

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        since: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> Tuple[list[list[float]], int]:
        attempts = 0
        for attempt in range(self.max_retries):
            attempts = attempt + 1
            try:
                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
                if ohlcv:
                    return ohlcv, attempts
            except Exception as e:
                logger.warning(f"获取 K 线失败 (尝试 {attempts}): {e}")
                time.sleep(self.retry_delay)
        return [], attempts

    def sleep_for_rate_limit(self) -> None:
        time.sleep(self.exchange.rateLimit / 1000)
