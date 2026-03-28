from __future__ import annotations

from datetime import datetime, timedelta

from app.services.market.market_data_service import MarketDataService
from config import settings
from utils.logger import logger


class PairCompareService:
    def __init__(self, market_data_service: MarketDataService | None = None) -> None:
        if market_data_service is None:
            raise ValueError("PairCompareService 需要显式注入 market_data_service")
        self.market_data_service = market_data_service

    def compare_pairs(self, symbol_a: str, symbol_b: str, days: int = 7, timeframe: str = "1h") -> dict:
        try:
            full_symbol_a = f"{symbol_a}/USDT"
            full_symbol_b = f"{symbol_b}/USDT"
            logger.info(f"开始对比: {full_symbol_a} vs {full_symbol_b}, {days}天, 显示周期{timeframe}")

            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            base_timeframe = settings.PAIR_COMPARE_BASE_TIMEFRAME
            klines_a = self.market_data_service.fetch_ohlcv_range(full_symbol_a, base_timeframe, start_date, end_date)
            klines_b = self.market_data_service.fetch_ohlcv_range(full_symbol_b, base_timeframe, start_date, end_date)
            if not klines_a or not klines_b:
                return {"error": "获取数据失败"}

            if timeframe != base_timeframe:
                klines_a = self._aggregate_klines(klines_a, timeframe)
                klines_b = self._aggregate_klines(klines_b, timeframe)

            aligned = self._align_timestamps(klines_a, klines_b)
            if not aligned["timestamps"]:
                return {"error": "数据时间戳无法对齐"}

            return {
                "symbol_a": full_symbol_a,
                "symbol_b": full_symbol_b,
                "data_a": self._format_for_chart(aligned["data_a"]),
                "data_b": self._format_for_chart(aligned["data_b"]),
                "ratio_ohlc": self._calculate_ratio_ohlc(aligned["data_a"], aligned["data_b"]),
                "ratio_symbol": f"{symbol_a}/{symbol_b}",
            }
        except Exception as exc:
            logger.error(f"币种对比失败: {exc}")
            return {"error": str(exc)}

    def _aggregate_klines(self, klines: list[list[float]], target_timeframe: str) -> list[list[float]]:
        timeframe_minutes = {
            "5m": 5,
            "15m": 15,
            "30m": 30,
            "1h": 60,
            "4h": 240,
            "1d": 1440,
            "1w": 10080,
            "1M": 43200,
        }
        if target_timeframe not in timeframe_minutes:
            return klines

        interval_ms = timeframe_minutes[target_timeframe] * 60 * 1000
        aggregated: list[list[float]] = []
        current_bucket: list[float] | None = None
        for ts, open_price, high, low, close, volume in klines:
            bucket_start = (ts // interval_ms) * interval_ms
            if current_bucket is None or current_bucket[0] != bucket_start:
                if current_bucket:
                    aggregated.append(current_bucket)
                current_bucket = [bucket_start, open_price, high, low, close, volume]
                continue
            current_bucket[2] = max(current_bucket[2], high)
            current_bucket[3] = min(current_bucket[3], low)
            current_bucket[4] = close
            current_bucket[5] += volume
        if current_bucket:
            aggregated.append(current_bucket)
        return aggregated

    def _align_timestamps(self, klines_a: list[list[float]], klines_b: list[list[float]]) -> dict[str, list]:
        dict_a = {row[0]: row for row in klines_a}
        dict_b = {row[0]: row for row in klines_b}
        common_ts = sorted(set(dict_a.keys()) & set(dict_b.keys()))
        return {
            "timestamps": common_ts,
            "data_a": [dict_a[ts] for ts in common_ts],
            "data_b": [dict_b[ts] for ts in common_ts],
        }

    def _format_for_chart(self, klines: list[list[float]]) -> list[dict[str, float]]:
        return [
            {
                "time": int(row[0] / 1000),
                "open": row[1],
                "high": row[2],
                "low": row[3],
                "close": row[4],
            }
            for row in klines
        ]

    def _calculate_ratio_ohlc(self, klines_a: list[list[float]], klines_b: list[list[float]]) -> list[dict[str, float]]:
        ratio_klines = []
        for left, right in zip(klines_a, klines_b):
            if any(value in (0, None) for value in (left[1], left[2], left[3], left[4], right[1], right[2], right[3], right[4])):
                continue
            ratio_klines.append(
                {
                    "time": int(left[0] / 1000),
                    "open": left[1] / right[1],
                    "high": left[2] / right[2],
                    "low": left[3] / right[3],
                    "close": left[4] / right[4],
                }
            )
        return ratio_klines
