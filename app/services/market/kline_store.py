from __future__ import annotations

import json
from functools import lru_cache
from sqlalchemy.exc import SQLAlchemyError
from typing import List

from config import settings
from config.settings import DEFAULT_DB_PATH
from app.infra.db.database import session_scope
from app.infra.db.schema import Kline
from utils.logger import logger


@lru_cache(maxsize=1)
def _load_early_btc_history() -> List[List]:
    file_path = DEFAULT_DB_PATH.parent / "btc_history_early.json"
    if file_path.exists():
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            logger.info(f"加载早期 BTC 历史数据: {len(data)} 条 (内存缓存)")
            return data
    return []


class KlineStore:
    def get_before(self, symbol: str, timeframe: str, end_ts: int, limit: int) -> list[list[float]]:
        with session_scope() as session:
            result = [
                k.to_list()
                for k in (
                    session.query(Kline)
                    .filter(
                        Kline.symbol == symbol,
                        Kline.timeframe == timeframe,
                        Kline.timestamp < end_ts,
                    )
                    .order_by(Kline.timestamp.desc())
                    .limit(limit)
                    .all()
                )
            ]

        result.sort(key=lambda x: x[0])
        return result

    def get_range(self, symbol: str, timeframe: str, start_ts: int, end_ts: int) -> list[list[float]]:
        with session_scope() as session:
            cached_klines = [
                k.to_list()
                for k in (
                    session.query(Kline)
                    .filter(
                        Kline.symbol == symbol,
                        Kline.timeframe == timeframe,
                        Kline.timestamp >= start_ts,
                        Kline.timestamp <= end_ts,
                    )
                    .order_by(Kline.timestamp.asc())
                    .all()
                )
            ]

            if symbol == "BTC/USDT" and start_ts < settings.BTC_EARLY_HISTORY_CUTOFF_TS:
                early_in_db = (
                    session.query(Kline)
                    .filter(
                        Kline.symbol == symbol,
                        Kline.timeframe == timeframe,
                        Kline.timestamp < settings.BTC_EARLY_HISTORY_CUTOFF_TS,
                    )
                    .count()
                )

                if early_in_db == 0:
                    early_history = _load_early_btc_history()
                    if early_history:
                        self._save_with_session(session, symbol, timeframe, early_history)
                        logger.info(f"早期 BTC 历史数据已写入 DB: {len(early_history)} 条")
                        cached_klines = [
                            k.to_list()
                            for k in (
                                session.query(Kline)
                                .filter(
                                    Kline.symbol == symbol,
                                    Kline.timeframe == timeframe,
                                    Kline.timestamp >= start_ts,
                                    Kline.timestamp <= end_ts,
                                )
                                .order_by(Kline.timestamp.asc())
                                .all()
                            )
                        ]

        return cached_klines

    def save(self, symbol: str, timeframe: str, klines: list[list[float]]) -> None:
        with session_scope() as session:
            self._save_with_session(session, symbol, timeframe, klines)

    def _save_with_session(self, session, symbol: str, timeframe: str, klines: list[list[float]]) -> None:
        if not klines:
            return
        try:
            values = [
                {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "timestamp": k[0],
                    "open": k[1],
                    "high": k[2],
                    "low": k[3],
                    "close": k[4],
                    "volume": k[5],
                }
                for k in klines
            ]

            dialect_name = session.bind.dialect.name

            if dialect_name == "postgresql":
                from sqlalchemy.dialects.postgresql import insert as pg_insert

                stmt = pg_insert(Kline).values(values)
                stmt = stmt.on_conflict_do_update(
                    index_elements=["symbol", "timeframe", "timestamp"],
                    set_={
                        "open": stmt.excluded.open,
                        "high": stmt.excluded.high,
                        "low": stmt.excluded.low,
                        "close": stmt.excluded.close,
                        "volume": stmt.excluded.volume,
                    },
                )
                session.execute(stmt)
            elif dialect_name == "sqlite":
                from sqlalchemy.dialects.sqlite import insert as sqlite_insert

                stmt = sqlite_insert(Kline).values(values)
                stmt = stmt.on_conflict_do_update(
                    index_elements=["symbol", "timeframe", "timestamp"],
                    set_={
                        "open": stmt.excluded.open,
                        "high": stmt.excluded.high,
                        "low": stmt.excluded.low,
                        "close": stmt.excluded.close,
                        "volume": stmt.excluded.volume,
                    },
                )
                session.execute(stmt)
            else:
                from sqlalchemy.exc import IntegrityError as SAIntegrityError

                for value in values:
                    try:
                        session.execute(Kline.__table__.insert().values(**value))
                        session.flush()
                    except SAIntegrityError:
                        session.rollback()
        except SQLAlchemyError as exc:
            session.rollback()
            logger.error(
                "保存 K 线缓存失败: "
                f"symbol={symbol} timeframe={timeframe} rows={len(klines)} reason={self._safe_db_error(exc)}"
            )
        except Exception as exc:
            session.rollback()
            logger.error(
                "保存 K 线缓存失败: "
                f"symbol={symbol} timeframe={timeframe} rows={len(klines)} reason={self._safe_db_error(exc)}"
            )

    @staticmethod
    def _safe_db_error(exc: Exception) -> str:
        original = getattr(exc, "orig", None)
        message = str(original or exc).splitlines()[0]
        if len(message) > 240:
            return f"{message[:240]}..."
        return message
