import ccxt
import time
from config import settings
from utils.logger import logger

class MarketProvider:
    def __init__(self, exchange_id=settings.EXCHANGE_ID):
        """
        初始化交易所连接
        """
        self.exchange_id = exchange_id
        self.max_retries = 3
        self.retry_delay = 2  # seconds

        try:
            # 动态实例化交易所类 (e.g., ccxt.binance())
            exchange_class = getattr(ccxt, exchange_id)
            self.exchange = exchange_class({
                'enableRateLimit': True,  # 启用内置的速率限制处理
                'options': {
                    'defaultType': 'spot', # 默认使用现货，如果需要合约可以改为 'future' 或 'swap'
                }
            })
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
        
        Args:
            symbol (str): 交易对, e.g., 'BTC/USDT'
            timeframe (str): 时间周期, e.g., '1h'
            limit (int): 获取条数
            
        Returns:
            list: OHLCV 数据列表，每项为 [timestamp, open, high, low, close, volume]
        """
        for attempt in range(self.max_retries):
            try:
                # ccxt 的 fetch_ohlcv 方法
                #返回值结构: [[time, open, high, low, close, volume], ...]
                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
                
                if not ohlcv:
                    logger.warning(f"{symbol} 获取到的 K 线数据为空")
                    return []
                    
                logger.info(f"成功获取 {symbol} {timeframe} K线数据: {len(ohlcv)} 条")
                return ohlcv
                
            except ccxt.NetworkError as e:
                logger.warning(f"网络错误 (尝试 {attempt+1}/{self.max_retries}): {e}")
            except ccxt.ExchangeError as e:
                logger.error(f"交易所错误: {e}")
                break  # 交易所报错通常不需要重试 (如交易对不存在)
            except Exception as e:
                logger.error(f"获取 K 线未知错误: {e}")
                break
            
            time.sleep(self.retry_delay)
            
        return []

    def close(self):
        """
        关闭连接 (对于某些需要显式关闭的连接)
        """
        # ccxt 同步模式通常不需要显式关闭，但保留作为接口规范
        pass

# 简单的测试入口
if __name__ == "__main__":
    provider = MarketProvider()
    data = provider.get_kline_data('BTC/USDT', limit=5)
    print(f"Latest 5 candles: {data}")
