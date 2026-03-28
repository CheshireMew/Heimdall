from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from app.services.market.market_data_service import MarketDataService
from app.services.sentiment_service import SentimentService
from app.services.tools.dca_calculator import prepare_dca_dataset, simulate_dca_schedule
from config import settings
from utils.logger import logger
from utils.time_manager import TimeManager


class DCAService:
    def __init__(
        self,
        market_data_service: MarketDataService | None = None,
        sentiment_service: SentimentService | None = None,
    ) -> None:
        if market_data_service is None or sentiment_service is None:
            raise ValueError("DCAService 需要显式注入 market_data_service 和 sentiment_service")
        self.market_data_service = market_data_service
        self.sentiment_service = sentiment_service

    def calculate_dca(
        self,
        *,
        symbol: str,
        start_date_str: str,
        end_date_str: str | None,
        daily_investment: float,
        target_time_str: str = "23:00",
        timezone: str = "Asia/Shanghai",
        strategy: str = "standard",
        strategy_params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            target_h, target_m = map(int, target_time_str.split(":"))
            now_local = TimeManager.get_now(timezone)

            start_dt_local = datetime.strptime(start_date_str, "%Y-%m-%d")
            if end_date_str:
                end_dt_local = datetime.strptime(end_date_str, "%Y-%m-%d")
                if end_dt_local.date() == now_local.date():
                    end_dt_local = now_local.replace(tzinfo=None)
                else:
                    end_dt_local = end_dt_local.replace(hour=23, minute=59, second=59)
            else:
                end_dt_local = now_local.replace(tzinfo=None)

            logger.info(
                f"计算定投: {symbol}, 日投 {daily_investment}, {start_dt_local} - {end_dt_local} (Local), 时区 {timezone}"
            )

            buffer_days = settings.DCA_INDICATOR_BUFFER_DAYS
            fetch_start_utc = TimeManager.convert_to_utc(start_dt_local - timedelta(days=buffer_days + 1), timezone)
            fetch_end_utc = TimeManager.convert_to_utc(end_dt_local + timedelta(days=1), timezone)
            klines = self.market_data_service.fetch_ohlcv_range(symbol, "1h", fetch_start_utc, fetch_end_utc)
            if not klines:
                return {"error": "该时间段无数据"}

            target_klines = prepare_dca_dataset(
                klines,
                timezone=timezone,
                start_dt_local=start_dt_local,
                target_hour=target_h,
            )

            sentiment_map: dict[str, int] = {}
            if strategy == "fear_greed":
                sentiment_map = self.sentiment_service.get_sentiment_history(start_dt_local, end_dt_local)

            history, total_invested, total_coins = simulate_dca_schedule(
                target_klines,
                daily_investment=daily_investment,
                strategy=strategy,
                strategy_params=strategy_params,
                sentiment_map=sentiment_map,
            )

            if not history:
                return {"error": "无符合时间的数据点 (可能数据太短)"}

            try:
                latest_kline = self.market_data_service.get_kline_data(symbol, "1m", limit=1)
                current_price = latest_kline[-1][4] if latest_kline and len(latest_kline[-1]) > 4 else history[-1]["price"]
            except Exception as exc:
                logger.warning(f"无法获取实时价格，降级使用最后一次定投价格: {exc}")
                current_price = history[-1]["price"]

            final_value = total_coins * current_price
            profit_loss = final_value - total_invested
            roi_percent = (profit_loss / total_invested) * 100 if total_invested > 0 else 0
            return {
                "symbol": symbol,
                "start_date": start_date_str,
                "end_date": end_dt_local.strftime("%Y-%m-%d"),
                "target_time": target_time_str,
                "total_days": len(history),
                "total_invested": round(total_invested, 2),
                "final_value": round(final_value, 2),
                "total_coins": round(total_coins, 6),
                "roi": round(roi_percent, 2),
                "average_cost": round(history[-1]["avg_cost"], 2),
                "profit_loss": round(profit_loss, 2),
                "current_price": current_price,
                "history": history,
            }
        except Exception as exc:
            logger.error(f"DCA Error: {exc}", exc_info=True)
            return {"error": str(exc)}
