"""
数据保留策略 - 定期清理过期的 Kline 数据
"""
from datetime import datetime, timedelta

from app.infra.db import DatabaseRuntime
from app.infra.db.schema import Kline
from config import settings
from utils.logger import logger

# 短周期时间框架，日线/周线/月线不清理
SHORT_TIMEFRAMES = ['1m', '5m', '15m', '1h', '4h']


def cleanup_old_data(database_runtime: DatabaseRuntime):
    """定期清理过期数据"""
    session = database_runtime.get_session()
    try:
        # 1. 清理短周期 Kline (1m/5m/15m/1h/4h)
        cutoff_ts = int((datetime.now() - timedelta(days=settings.KLINE_RETENTION_DAYS)).timestamp() * 1000)
        deleted_klines = session.query(Kline).filter(
            Kline.timeframe.in_(SHORT_TIMEFRAMES),
            Kline.timestamp < cutoff_ts
        ).delete(synchronize_session=False)
        logger.info(f"[retention] Deleted {deleted_klines} short-tf klines older than {settings.KLINE_RETENTION_DAYS}d")

        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"[retention] Cleanup failed: {e}")
    finally:
        session.close()
