"""
Backtester - 历史回测引擎
负责获取历史数据、重放策略、计算性能指标并保存结果
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time

from core.market_provider import MarketProvider
from core.technical_analysis import TechnicalAnalysis
from core.prompt_engine import PromptEngine
from services.llm_client import LLMClient
from models.database import BacktestRun, BacktestSignal, get_session, init_db
from utils.logger import logger
from config import settings


class Backtester:
    def __init__(self, use_ai: bool = False):
        """
        初始化回测引擎
        
        Args:
            use_ai (bool): 是否在回测中使用 AI 分析（消耗 Token，速度慢）
        """
        self.market_provider = MarketProvider()
        self.use_ai = use_ai
        self.llm_client = LLMClient() if use_ai else None
        
        # 确保数据库已初始化
        init_db()
    
    def fetch_historical_data(
        self, 
        symbol: str, 
        start_date: datetime, 
        end_date: datetime,
        timeframe: str = '1h'
    ) -> List[List]:
        """
        获取历史 K 线数据
        
        Args:
            symbol: 交易对，如 'BTC/USDT'
            start_date: 开始日期
            end_date: 结束日期
            timeframe: 时间周期
            
        Returns:
            OHLCV 数据列表
        """
        logger.info(f"获取历史数据: {symbol} {start_date} - {end_date}")
        
        try:
            # 将 datetime 转换为毫秒时间戳
            since = int(start_date.timestamp() * 1000)
            
            # CCXT 的 fetch_ohlcv 有 limit 限制，需要分批获取
            all_data = []
            current_since = since
            end_timestamp = int(end_date.timestamp() * 1000)
            
            while current_since < end_timestamp:
                logger.info(f"正在获取数据... (当前时间戳: {current_since})")
                
                # 获取一批数据（默认 500 条）
                batch = self.market_provider.exchange.fetch_ohlcv(
                    symbol, 
                    timeframe, 
                    since=current_since,
                    limit=500
                )
                
                if not batch:
                    break
                
                all_data.extend(batch)
                
                # 更新 since 到最后一条数据的时间戳 + 1
                current_since = batch[-1][0] + 1
                
                # 避免速率限制
                time.sleep(self.market_provider.exchange.rateLimit / 1000)
                
                # 如果已经超过结束时间，停止
                if batch[-1][0] >= end_timestamp:
                    break
            
            # 过滤出在时间范围内的数据
            filtered_data = [
                candle for candle in all_data 
                if since <= candle[0] <= end_timestamp
            ]
            
            logger.info(f"历史数据获取完成: {len(filtered_data)} 条 K 线")
            return filtered_data
            
        except Exception as e:
            logger.error(f"获取历史数据失败: {e}")
            return []
    
    def analyze_candle(self, kline_data: List[List], current_index: int) -> Dict:
        """
        分析单根 K 线（获取指标和信号）
        
        Args:
            kline_data: 完整的 K 线数据列表
            current_index: 当前要分析的索引位置
            
        Returns:
            分析结果字典（包含指标和信号）
        """
        # 使用当前时刻之前的数据计算指标（避免未来函数）
        historical_slice = kline_data[:current_index + 1]
        
        if len(historical_slice) < settings.EMA_PERIOD:
            # 数据不足，跳过
            return None
        
        # 提取价格数据
        closes = [x[4] for x in historical_slice]
        highs = [x[2] for x in historical_slice]
        lows = [x[3] for x in historical_slice]
        
        # 计算技术指标
        indicators = {
            'ema': TechnicalAnalysis.calculate_ema(closes, settings.EMA_PERIOD),
            'rsi': TechnicalAnalysis.calculate_rsi(closes, settings.RSI_PERIOD),
            'macd': TechnicalAnalysis.calculate_macd(
                closes, settings.MACD_FAST, settings.MACD_SLOW, settings.MACD_SIGNAL
            ),
            'atr': TechnicalAnalysis.calculate_atr(highs, lows, closes, 14)
        }
        
        # 简单的规则生成信号（不使用 AI，节省成本）
        signal, confidence = self._generate_signal_by_rules(closes[-1], indicators)
        
        result = {
            'timestamp': historical_slice[-1][0],
            'price': closes[-1],
            'signal': signal,
            'confidence': confidence,
            'indicators': indicators,
            'reasoning': None
        }
        
        # 可选：使用 AI 分析（消耗 Token）
        if self.use_ai and self.llm_client:
            try:
                prompt = PromptEngine.build_analysis_prompt(
                    "回测分析", historical_slice, indicators
                )
                ai_result = self.llm_client.analyze(prompt)
                if ai_result:
                    result['signal'] = ai_result.get('signal', signal)
                    result['confidence'] = ai_result.get('confidence', confidence)
                    result['reasoning'] = ai_result.get('reasoning')
            except Exception as e:
                logger.warning(f"AI 分析失败，使用规则信号: {e}")
        
        return result
    
    def _generate_signal_by_rules(self, price: float, indicators: Dict) -> Tuple[str, float]:
        """
        基于技术指标的简单规则生成信号
        
        Args:
            price: 当前价格
            indicators: 技术指标字典
            
        Returns:
            (signal, confidence) 元组
        """
        ema = indicators.get('ema')
        rsi = indicators.get('rsi')
        macd = indicators.get('macd')
        
        # 默认 HOLD
        signal = 'HOLD'
        confidence = 50.0
        
        # 规则 1: 价格 > EMA 且 RSI < 70 => BUY
        if ema and rsi and price > ema and rsi < 70:
            signal = 'BUY'
            confidence = 60.0
            
            # MACD 金叉加强信号
            if macd and macd[0] is not None and macd[2] > 0:
                confidence = 75.0
        
        # 规则 2: 价格 < EMA 且 RSI > 30 => SELL
        elif ema and rsi and price < ema and rsi > 30:
            signal = 'SELL'
            confidence = 60.0
            
            # MACD 死叉加强信号
            if macd and macd[0] is not None and macd[2] < 0:
                confidence = 75.0
        
        return signal, confidence
    
    def run_backtest(
        self, 
        symbol: str, 
        start_date: datetime, 
        end_date: datetime,
        timeframe: str = '1h'
    ) -> Optional[int]:
        """
        执行回测
        
        Args:
            symbol: 交易对
            start_date: 开始日期
            end_date: 结束日期
            timeframe: 时间周期
            
        Returns:
            backtest_id (回测记录 ID) 或 None（失败）
        """
        logger.info(f"开始回测: {symbol} ({start_date} - {end_date})")
        
        # 1. 创建回测记录
        session = get_session()
        backtest_run = BacktestRun(
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            status='running',
            metadata={
                'ema_period': settings.EMA_PERIOD,
                'rsi_period': settings.RSI_PERIOD,
                'use_ai': self.use_ai
            }
        )
        session.add(backtest_run)
        session.commit()
        backtest_id = backtest_run.id
        
        try:
            # 2. 获取历史数据
            kline_data = self.fetch_historical_data(symbol, start_date, end_date, timeframe)
            
            if not kline_data or len(kline_data) < settings.EMA_PERIOD:
                logger.error("历史数据不足，无法进行回测")
                backtest_run.status = 'failed'
                session.commit()
                session.close()
                return None
            
            backtest_run.total_candles = len(kline_data)
            session.commit()
            
            # 3. 逐根 K 线分析
            signals_data = []
            buy_count = 0
            sell_count = 0
            hold_count = 0
            
            logger.info(f"开始分析 {len(kline_data)} 根 K 线...")
            
            for i in range(settings.EMA_PERIOD, len(kline_data)):
                result = self.analyze_candle(kline_data, i)
                
                if result:
                    # 统计信号
                    if result['signal'] == 'BUY':
                        buy_count += 1
                    elif result['signal'] == 'SELL':
                        sell_count += 1
                    else:
                        hold_count += 1
                    
                    # 保存信号（批量插入，提升性能）
                    signal_record = BacktestSignal(
                        backtest_id=backtest_id,
                        timestamp=datetime.fromtimestamp(result['timestamp'] / 1000),
                        price=result['price'],
                        signal=result['signal'],
                        confidence=result['confidence'],
                        indicators=result['indicators'],
                        reasoning=result['reasoning']
                    )
                    signals_data.append(signal_record)
                
                # 进度提示
                if (i + 1) % 100 == 0:
                    logger.info(f"进度: {i + 1}/{len(kline_data)}")
            
            # 4. 批量插入信号
            session.bulk_save_objects(signals_data)
            
            # 5. 更新回测记录
            backtest_run.status = 'completed'
            backtest_run.total_signals = len(signals_data)
            backtest_run.buy_signals = buy_count
            backtest_run.sell_signals = sell_count
            backtest_run.hold_signals = hold_count
            session.commit()
            
            logger.info(f"回测完成: ID={backtest_id}, 信号总数={len(signals_data)}")
            logger.info(f"  BUY: {buy_count}, SELL: {sell_count}, HOLD: {hold_count}")
            
            return backtest_id
            
        except Exception as e:
            logger.error(f"回测执行失败: {e}")
            backtest_run.status = 'failed'
            session.commit()
            return None
        finally:
            session.close()
    
    def get_backtest_result(self, backtest_id: int) -> Optional[Dict]:
        """
        获取回测结果
        
        Args:
            backtest_id: 回测记录 ID
            
        Returns:
            回测结果字典
        """
        session = get_session()
        try:
            backtest_run = session.query(BacktestRun).filter_by(id=backtest_id).first()
            
            if not backtest_run:
                return None
            
            # 获取信号列表
            signals = session.query(BacktestSignal).filter_by(backtest_id=backtest_id).all()
            
            result = {
                'id': backtest_run.id,
                'symbol': backtest_run.symbol,
                'timeframe': backtest_run.timeframe,
                'start_date': backtest_run.start_date.isoformat(),
                'end_date': backtest_run.end_date.isoformat(),
                'status': backtest_run.status,
                'total_candles': backtest_run.total_candles,
                'total_signals': backtest_run.total_signals,
                'buy_signals': backtest_run.buy_signals,
                'sell_signals': backtest_run.sell_signals,
                'hold_signals': backtest_run.hold_signals,
                'signals': [
                    {
                        'timestamp': signal.timestamp.isoformat(),
                        'price': signal.price,
                        'signal': signal.signal,
                        'confidence': signal.confidence,
                        'indicators': signal.indicators
                    }
                    for signal in signals
                ]
            }
            
            return result
            
        except Exception as e:
            logger.error(f"获取回测结果失败: {e}")
            return None
        finally:
            session.close()


if __name__ == "__main__":
    # 简单测试
    backtester = Backtester(use_ai=False)
    
    # 测试最近 7 天的数据
    end = datetime.now()
    start = end - timedelta(days=7)
    
    backtest_id = backtester.run_backtest('BTC/USDT', start, end, '1h')
    
    if backtest_id:
        result = backtester.get_backtest_result(backtest_id)
        print(f"回测结果: {result}")
