"""
数据保留策略 - 定期清理过期的 Kline 和回测数据
"""
from datetime import datetime, timedelta

from app.infra.db.database import SessionLocal
from app.infra.db.schema import Kline, BacktestRun
from config import settings
from utils.logger import logger

# 短周期时间框架，日线/周线/月线不清理
SHORT_TIMEFRAMES = ['1m', '5m', '15m', '1h', '4h']


async def cleanup_old_data():
    """定期清理过期数据"""
    session = SessionLocal()
    try:
        # 1. 清理短周期 Kline (1m/5m/15m/1h/4h)
        cutoff_ts = int((datetime.now() - timedelta(days=settings.KLINE_RETENTION_DAYS)).timestamp() * 1000)
        deleted_klines = session.query(Kline).filter(
            Kline.timeframe.in_(SHORT_TIMEFRAMES),
            Kline.timestamp < cutoff_ts
        ).delete(synchronize_session=False)
        logger.info(f"[retention] Deleted {deleted_klines} short-tf klines older than {settings.KLINE_RETENTION_DAYS}d")

        # 2. 清理旧回测 (CASCADE 自动删信号)
        cutoff_dt = datetime.now() - timedelta(days=settings.BACKTEST_RETENTION_DAYS)
        deleted_bt = session.query(BacktestRun).filter(
            BacktestRun.created_at < cutoff_dt
        ).delete(synchronize_session=False)
        logger.info(f"[retention] Deleted {deleted_bt} old backtests older than {settings.BACKTEST_RETENTION_DAYS}d")

        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"[retention] Cleanup failed: {e}")
    finally:
        session.close()
