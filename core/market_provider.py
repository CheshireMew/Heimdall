import ccxt
import time
from datetime import datetime, timedelta
from config import settings
from utils.logger import logger
from models.database import get_session, init_db, session_scope
from models.schema import Kline

class MarketProvider:
    def __init__(self, exchange_id=settings.EXCHANGE_ID):
        """
        初始化交易所连接
        """
        self.exchange_id = exchange_id
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        self.max_task_seconds = 90  # 超时保护

        try:
            # 动态实例化交易所类 (e.g., ccxt.binance())
            exchange_class = getattr(ccxt, exchange_id)
            self.exchange = exchange_class({
                'enableRateLimit': True,  # 启用内置的速率限制处理
                'options': {
                    'defaultType': 'spot', # 默认使用现货
                }
            })
            # 确保数据库初始化 (用于缓存)
            init_db()
            logger.info(f"已连接到交易所: {exchange_id}")
        except AttributeError:
            logger.error(f"不支持的交易所 ID: {exchange_id}")
            raise ValueError(f"Unsupported exchange: {exchange_id}")
        except Exception as e:
            logger.error(f"交易所初始化失败: {e}")
            raise e

    def get_kline_data(self, symbol, timeframe=settings.TIMEFRAME, limit=settings.LIMIT):
        """
        获取K线数据
        策略：Redis (300s TTL) -> Exchange -> Update Redis
        """
        start_time = time.time()
        cache_hit = False
        attempts = 0
        try:
            from services.redis_service import redis_service
            
            # 1. 尝试从Redis获取
            cache_key = f"kline:{symbol}:{timeframe}:{limit}"
            cached_data = redis_service.get(cache_key)
            
            if cached_data:
                # logger.debug(f"K线数据缓存命中: {cache_key}")
                cache_hit = True
                return cached_data
            
            # 2. 从交易所获取
            # 优先尝试从数据库获取最新数据，如果数据库是最新的
            # 但简单起见，这里还是混合策略。
            # 实际上 get_kline_data 通常是“首页”用的，用Redis -> Exchange最快。
            # 只有 verify_data 和 history 才重度依赖 DB。
            
            data, attempts = self._fetch_from_exchange(symbol, timeframe, limit=limit)
            
            # 3. 写入Redis (5分钟过期)
            if data:
                redis_service.set(cache_key, data, ttl=300)
                
            return data
            
        except ImportError:
            # 降级：如果没有Redis依赖，直接查交易所
            data, attempts = self._fetch_from_exchange(symbol, timeframe, limit=limit)
            return data
        except Exception as e:
            logger.error(f"K线数据获取错误 (Redis/Exchange): {e}")
            data, attempts = self._fetch_from_exchange(symbol, timeframe, limit=limit)
            return data
        finally:
            elapsed = time.time() - start_time
            logger.info(
                f"[metrics] get_kline_data symbol={symbol} tf={timeframe} limit={limit} "
                f"cache_hit={cache_hit} attempts={attempts} elapsed={elapsed:.2f}s"
            )

    def get_history_data(self, symbol, timeframe, end_ts, limit=500):
        """
        获取历史数据 (用于无限加载)
        指定 end_ts，获取该时间之前的数据
        """
        start_time = time.time()
        try:
            with session_scope() as session:
                # 从数据库查询
                klines = session.query(Kline).filter(
                    Kline.symbol == symbol,
                    Kline.timeframe == timeframe,
                    Kline.timestamp < end_ts
                ).order_by(Kline.timestamp.desc()).limit(limit).all()
                
                # 按时间正序排列返回
                result = [k.to_list() for k in klines]
                result.sort(key=lambda x: x[0])
                return result
        except Exception as e:
            logger.error(f"历史数据查询失败: {e}")
            return []
        finally:
            elapsed = time.time() - start_time
            logger.info(f"[metrics] get_history_data symbol={symbol} tf={timeframe} limit={limit} elapsed={elapsed:.2f}s")

    def _fetch_from_exchange(self, symbol, timeframe, since=None, limit=None):
        """直接从交易所获取数据 (带重试)"""
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

    def fetch_ohlcv_range(self, symbol: str, timeframe: str, start_date: datetime, end_date: datetime):
        """
        获取指定时间范围的 K 线数据 (优先读缓存，缺失部分从交易所补全)
        """
        start_ts = int(start_date.timestamp() * 1000)
        end_ts = int(end_date.timestamp() * 1000)
        range_start = time.time()
        
        try:
            with session_scope() as session:
                # 1. 查询数据库中的现有数据
                cached_klines = session.query(Kline).filter(
                    Kline.symbol == symbol,
                    Kline.timeframe == timeframe,
                    Kline.timestamp >= start_ts,
                    Kline.timestamp <= end_ts
                ).order_by(Kline.timestamp.asc()).all()
                
                # 如果缓存覆盖了整个区间 (这需要严谨判断，这里简单判断首尾)
                # 注意：这无法检测中间的空洞。但在当前设计下，我们总是补全空洞。
                if cached_klines:
                    min_cached = cached_klines[0].timestamp
                    max_cached = cached_klines[-1].timestamp
                else:
                    min_cached = None
                    max_cached = None
                
                logger.info(f"缓存命中: {len(cached_klines)} 条 ({symbol})")
                
                new_data = []
                
                # 2. 补全头部数据 (Start -> Min Cached)
                if min_cached is None or start_ts < min_cached:
                    # 如果没有缓存，或者请求开始早于缓存开始
                    target_end = min_cached if min_cached else end_ts
                    head_data = self._fetch_gap(symbol, timeframe, start_ts, target_end)
                    new_data.extend(head_data)
                    
                # 3. 补全尾部数据 (Max Cached -> End)
                if max_cached is not None and end_ts > max_cached:
                    # 尾部通常是“最新数据”，需要注意不要重复 fetch max_cached 那一条
                    # fetch_gap 内部处理 since，我们传 max_cached + 1ms
                    tail_data = self._fetch_gap(symbol, timeframe, max_cached + 1, end_ts)
                    new_data.extend(tail_data)
                
                # 4. 保存新数据到数据库
                if new_data:
                    logger.info(f"下载新数据: {len(new_data)} 条")
                    self._save_klines_to_db(session, symbol, timeframe, new_data)
                    # 提交由 session_scope 统一处理
                    
                # 5. 手动合并缓存+新增
                cached_map = {k.timestamp: k.to_list() for k in cached_klines}
                for d in new_data:
                    cached_map[d[0]] = d
                    
                final_data = sorted(cached_map.values(), key=lambda x: x[0])
                
                # 再次过滤，确保精确在 start_ts, end_ts 之间
                result = [x for x in final_data if start_ts <= x[0] <= end_ts]
                return result
            
        except Exception as e:
            logger.error(f"带缓存数据获取失败: {e}")
            # Fallback: 直接从交易所下，不走缓存逻辑
            return self._fetch_gap(symbol, timeframe, start_ts, end_ts)
        finally:
            elapsed = time.time() - range_start
            logger.info(
                f"[metrics] fetch_ohlcv_range symbol={symbol} tf={timeframe} "
                f"cached={len(cached_klines) if 'cached_klines' in locals() else 0} "
                f"new={len(new_data) if 'new_data' in locals() else 0} "
                f"elapsed={elapsed:.2f}s"
            )
            
    def _save_klines_to_db(self, session, symbol, timeframe, klines):
        """保存K线数据到数据库 (批量 + 忽略重复)"""
        try:
            from sqlalchemy.dialects.postgresql import insert
            
            stmt = insert(Kline).values([
                {
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'timestamp': k[0],
                    'open': k[1],
                    'high': k[2],
                    'low': k[3],
                    'close': k[4],
                    'volume': k[5]
                }
                for k in klines
            ])
            
            # 忽略重复键错误 (ON CONFLICT DO NOTHING)
            # index_elements 用于指定判断冲突的字段
            do_nothing_stmt = stmt.on_conflict_do_nothing(
                index_elements=['symbol', 'timeframe', 'timestamp']
            )
            
            session.execute(do_nothing_stmt)
            # session.commit() 由外层 session_scope 管理
            
        except Exception as e:
            logger.error(f"保存数据失败: {e}")
            # 不抛出，避免这部分失败影响整个查询返回


    def _fetch_gap(self, symbol, timeframe, since, until):
        """循环获取指定时间段的完整数据"""
        data = []
        current_since = since
        task_start = time.time()
        
        while current_since < until:
            # 避免死循环
            limit = 1000 # CCXT 默认
            batch, attempts = self._fetch_from_exchange(symbol, timeframe, since=current_since, limit=limit)
            
            if not batch:
                break
                
            filtered = [x for x in batch if x[0] < until]
            if not filtered:
                # 获取到的数据都在 until 之后（可能交易所只有最新数据）
                break
                
            data.extend(filtered)
            
            # Update since
            last_ts = filtered[-1][0]
            if last_ts >= current_since:
                current_since = last_ts + 1
            else:
                # 死循环保护
                break
                
            # Rate limit sleep
            time.sleep(self.exchange.rateLimit / 1000)
            
            if len(batch) < limit:
                # 没有更多数据了
                break
            
            if time.time() - task_start > self.max_task_seconds:
                logger.warning(f"[_fetch_gap] 超时终止 symbol={symbol} tf={timeframe} since={since} until={until}")
                break
                
        return data

    def close(self):
        pass


# 简单的测试入口
if __name__ == "__main__":
    provider = MarketProvider()
    data = provider.get_kline_data('BTC/USDT', limit=5)
    print(f"Latest 5 candles: {data}")
