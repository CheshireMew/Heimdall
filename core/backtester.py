"""
Backtester - 历史回测引擎
负责获取历史数据、重放策略、计算性能指标并保存结果
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time
import os

from core.market_provider import MarketProvider
from core.technical_analysis import TechnicalAnalysis
from core.prompt_engine import PromptEngine
from services.llm_client import LLMClient
from models.database import get_session, init_db, session_scope
from models.schema import BacktestRun, BacktestSignal  # 更新导入路径
from utils.logger import logger
from utils.time_manager import TimeManager
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
        获取历史 K 线数据 (使用带缓存的 MarketProvider)
        """
        logger.info(f"获取历史数据: {symbol} {start_date} - {end_date}")
        return self.market_provider.fetch_ohlcv_range(symbol, timeframe, start_date, end_date)
    
    def analyze_candle(self, kline_data: List[List], current_index: int) -> Optional[Dict]:
        """
        分析单根 K 线（获取指标和信号）
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
        """
        try:
            ema = indicators.get('ema')
            rsi = indicators.get('rsi')
            macd = indicators.get('macd')
            
            # 默认 HOLD
            signal = 'HOLD'
            confidence = 50.0
            
            # 确保数据有效且为数值类型 (FIXED: Added strict type conversion)
            if ema is None or rsi is None:
                return signal, confidence
                
            price = float(price)
            ema = float(ema)
            rsi = float(rsi)
            
            # 规则 1: 价格 > EMA 且 RSI < 70 => BUY
            if price > ema and rsi < 70:
                signal = 'BUY'
                confidence = 60.0
                
                # MACD 金叉加强信号
                if macd and macd[0] is not None and macd[2] is not None and float(macd[2]) > 0:
                    confidence = 75.0
            
            # 规则 2: 价格 < EMA 且 RSI > 30 => SELL
            elif price < ema and rsi > 30:
                signal = 'SELL'
                confidence = 60.0
                
                # MACD 死叉加强信号
                if macd and macd[0] is not None and macd[2] is not None and float(macd[2]) < 0:
                    confidence = 75.0
            
            return signal, confidence
            
        except Exception as e:
            logger.warning(f"信号生成出错: {e}")
            import traceback
            traceback.print_exc()
            return 'HOLD', 50.0
    
    def run_backtest(
        self, 
        symbol: str, 
        start_date: datetime, 
        end_date: datetime,
        timeframe: str = '1h'
    ) -> Optional[int]:
        """
        执行回测
        """
        logger.info(f"开始回测: {symbol} ({start_date} - {end_date})")
        task_start = time.time()
        
        # 1. 创建回测记录
        with session_scope() as session:
            backtest_run = BacktestRun(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date,
                status='running',
                metadata_info={  # 使用 metadata_info 避免冲突
                    'ema_period': settings.EMA_PERIOD,
                    'rsi_period': settings.RSI_PERIOD,
                    'use_ai': self.use_ai
                }
            )
            session.add(backtest_run)
            session.flush()  # 获取自增ID
            backtest_id = backtest_run.id
        
            try:
                # 2. 获取历史数据
                fetch_start = time.time()
                kline_data = self.fetch_historical_data(symbol, start_date, end_date, timeframe)
                fetch_elapsed = time.time() - fetch_start
                
                if not kline_data or len(kline_data) < settings.EMA_PERIOD:
                    logger.error("历史数据不足，无法进行回测")
                    backtest_run.status = 'failed'
                    session.commit()
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
                total_elapsed = time.time() - task_start
                logger.info(
                    f"[metrics] backtest id={backtest_id} symbol={symbol} tf={timeframe} "
                    f"candles={len(kline_data)} signals={len(signals_data)} "
                    f"fetch_elapsed={fetch_elapsed:.2f}s total_elapsed={total_elapsed:.2f}s"
                )
                
                return backtest_id
                
            except Exception as e:
                # FIXED: Add traceback logging to file for debugging
                try:
                    import traceback
                    with open("traceback.log", "w") as f:
                        traceback.print_exc(file=f)
                except:
                    pass
                logger.error(f"回测执行失败: {e}")
                session.rollback()
                backtest_run.status = 'failed'
                session.commit()
                return None
    
    def get_backtest_result(self, backtest_id: int) -> Optional[Dict]:
        """
        获取回测结果
        """
        try:
            with session_scope() as session:
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


if __name__ == "__main__":
    # 简单测试
    backtester = Backtester(use_ai=False)
    
    # 测试最近 7 天的数据
    end = TimeManager.get_now()
    start = end - timedelta(days=7)
    
    backtest_id = backtester.run_backtest('BTC/USDT', start, end, '1h')
    
    if backtest_id:
        result = backtester.get_backtest_result(backtest_id)
        print(f"回测结果: {result}")
