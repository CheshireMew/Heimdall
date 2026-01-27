"""
币种对比分析器
比较两个币种的K线数据并计算比值K线
"""
from datetime import datetime, timedelta
from core.market_provider import MarketProvider
from utils.logger import logger


class PairComparator:
    def __init__(self):
        self.market_provider = MarketProvider()
    
    def compare_pairs(self, symbol_a: str, symbol_b: str, days: int = 7, timeframe: str = '1h') -> dict:
        """
        比较两个币种并计算比值K线
        
        Args:
            symbol_a: 币种A符号（如 'BTC'）
            symbol_b: 币种B符号（如 'ETH'）
            days: 回溯天数
            timeframe: K线周期（显示周期，实际统一获取5m数据后聚合）
        
        Returns:
            {
                'symbol_a': 'BTC/USDT',
                'symbol_b': 'ETH/USDT',
                'data_a': [...],  # lightweight-charts格式
                'data_b': [...],
                'ratio_ohlc': [...]  # 比值K线
            }
        """
        try:
            # 构造完整交易对符号
            full_symbol_a = f"{symbol_a}/USDT"
            full_symbol_b = f"{symbol_b}/USDT"
            
            logger.info(f"开始对比: {full_symbol_a} vs {full_symbol_b}, {days}天, 显示周期{timeframe}")
            
            # 计算时间范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # 统一获取5分钟数据（用于聚合）
            base_timeframe = '5m'
            klines_a = self.market_provider.fetch_ohlcv_range(
                full_symbol_a, base_timeframe, start_date, end_date
            )
            klines_b = self.market_provider.fetch_ohlcv_range(
                full_symbol_b, base_timeframe, start_date, end_date
            )
            
            if not klines_a or not klines_b:
                return {'error': '获取数据失败'}
            
            logger.info(f"获取5m数据: A={len(klines_a)}条, B={len(klines_b)}条")
            
            # 如果需要的周期不是5m，则进行聚合
            if timeframe != base_timeframe:
                klines_a = self._aggregate_klines(klines_a, timeframe)
                klines_b = self._aggregate_klines(klines_b, timeframe)
                logger.info(f"聚合为{timeframe}: A={len(klines_a)}条, B={len(klines_b)}条")
            
            # 对齐时间戳（取交集）
            aligned_data = self._align_timestamps(klines_a, klines_b)
            
            if not aligned_data['timestamps']:
                return {'error': '数据时间戳无法对齐'}
            
            # 转换为lightweight-charts格式
            data_a_formatted = self._format_for_chart(aligned_data['data_a'])
            data_b_formatted = self._format_for_chart(aligned_data['data_b'])
            
            # 计算比值K线
            ratio_ohlc = self._calculate_ratio_ohlc(
                aligned_data['data_a'], 
                aligned_data['data_b']
            )
            
            logger.info(f"对比完成: 共 {len(ratio_ohlc)} 个数据点")
            
            return {
                'symbol_a': full_symbol_a,
                'symbol_b': full_symbol_b,
                'data_a': data_a_formatted,
                'data_b': data_b_formatted,
                'ratio_ohlc': ratio_ohlc,
                'ratio_symbol': f"{symbol_a}/{symbol_b}"
            }
            
        except Exception as e:
            logger.error(f"币种对比失败: {e}")
            return {'error': str(e)}
    
    def _aggregate_klines(self, klines: list, target_timeframe: str) -> list:
        """
        将5分钟K线聚合为更大周期
        
        Args:
            klines: 5分钟K线数据 [[ts, o, h, l, c, v], ...]
            target_timeframe: 目标周期 (15m, 30m, 1h, 4h, 1d, 1w, 1M)
        
        Returns:
            聚合后的K线数据 [[ts, o, h, l, c, v], ...]
        """
        # 周期对应的分钟数
        timeframe_minutes = {
            '5m': 5,
            '15m': 15,
            '30m': 30,
            '1h': 60,
            '4h': 240,
            '1d': 1440,
            '1w': 10080,
            '1M': 43200  # 约30天
        }
        
        if target_timeframe not in timeframe_minutes:
            return klines  # 不支持的周期，返回原始数据
        
        interval_ms = timeframe_minutes[target_timeframe] * 60 * 1000
        aggregated = []
        current_bucket = None
        
        for kline in klines:
            ts, o, h, l, c, v = kline
            # 计算当前K线所属的bucket起始时间
            bucket_start = (ts // interval_ms) * interval_ms
            
            if current_bucket is None or current_bucket[0] != bucket_start:
                # 开始新bucket
                if current_bucket:
                    aggregated.append(current_bucket)
                current_bucket = [bucket_start, o, h, l, c, v]
            else:
                # 合并到当前bucket
                current_bucket[2] = max(current_bucket[2], h)  # high
                current_bucket[3] = min(current_bucket[3], l)  # low
                current_bucket[4] = c  # 使用最新的close
                current_bucket[5] += v  # 累加volume
        
        # 添加最后一个bucket
        if current_bucket:
            aggregated.append(current_bucket)
        
        return aggregated
    
    def _align_timestamps(self, klines_a: list, klines_b: list) -> dict:
        """
        对齐两组K线数据的时间戳
        返回: {'timestamps': [...], 'data_a': [...], 'data_b': [...]}
        """
        # 创建时间戳索引
        dict_a = {k[0]: k for k in klines_a}
        dict_b = {k[0]: k for k in klines_b}
        
        # 取交集
        common_ts = sorted(set(dict_a.keys()) & set(dict_b.keys()))
        
        aligned_a = [dict_a[ts] for ts in common_ts]
        aligned_b = [dict_b[ts] for ts in common_ts]
        
        return {
            'timestamps': common_ts,
            'data_a': aligned_a,
            'data_b': aligned_b
        }
    
    def _format_for_chart(self, klines: list) -> list:
        """
        转换为lightweight-charts的K线格式
        输入: [[ts, o, h, l, c, v], ...]
        输出: [{'time': ts_seconds, 'open': o, 'high': h, 'low': l, 'close': c}, ...]
        """
        return [
            {
                'time': int(k[0] / 1000),  # 毫秒转秒
                'open': k[1],
                'high': k[2],
                'low': k[3],
                'close': k[4]
            }
            for k in klines
        ]
    
    def _calculate_ratio_ohlc(self, klines_a: list, klines_b: list) -> list:
        """
        计算比值K线（OHLC都直接相除）
        """
        ratio_klines = []
        
        for ka, kb in zip(klines_a, klines_b):
            # ka, kb 格式: [ts, o, h, l, c, v]
            # 跳过零值/缺失，避免除零或 NaN 结果污染前端图表
            if any(x in (0, None) for x in (ka[1], ka[2], ka[3], ka[4], kb[1], kb[2], kb[3], kb[4])):
                continue
            ratio_klines.append({
                'time': int(ka[0] / 1000),
                'open': ka[1] / kb[1],
                'high': ka[2] / kb[2],
                'low': ka[3] / kb[3],
                'close': ka[4] / kb[4]
            })
        
        return ratio_klines


# 测试入口
if __name__ == "__main__":
    comparator = PairComparator()
    result = comparator.compare_pairs('BTC', 'ETH', days=7)
    
    if 'error' in result:
        print(f"错误: {result['error']}")
    else:
        print(f"对比成功:")
        print(f"  币种A: {result['symbol_a']}, 数据点: {len(result['data_a'])}")
        print(f"  币种B: {result['symbol_b']}, 数据点: {len(result['data_b'])}")
        print(f"  比值: {result['ratio_symbol']}, 数据点: {len(result['ratio_ohlc'])}")
