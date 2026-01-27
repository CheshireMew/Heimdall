"""
API Serializers - 数据序列化
负责将数据库模型转换为 JSON 兼容的字典格式
"""
from models.schema import BacktestRun, BacktestSignal

def serialize_backtest_run(run: BacktestRun, include_signals: bool = False) -> dict:
    """
    序列化 BacktestRun 对象
    
    Args:
        run: BacktestRun 实例
        include_signals: 是否包含信号详情
        
    Returns:
        JSON 兼容字典
    """
    data = {
        'id': run.id,
        'symbol': run.symbol,
        'timeframe': run.timeframe,
        'start_date': run.start_date.isoformat() if run.start_date else None,
        'end_date': run.end_date.isoformat() if run.end_date else None,
        'status': run.status,
        'metadata': run.metadata_info,  # 取 metadata_info 字段
        'created_at': run.created_at.isoformat() if run.created_at else None,
        'metrics': {
            'total_candles': run.total_candles,
            'total_signals': run.total_signals,
            'buy_signals': run.buy_signals,
            'sell_signals': run.sell_signals,
            'hold_signals': run.hold_signals
        }
    }
    
    if include_signals and run.signals:
        data['signals'] = [serialize_backtest_signal(sig) for sig in run.signals]
        
    return data

def serialize_backtest_signal(signal: BacktestSignal) -> dict:
    """
    序列化 BacktestSignal 对象
    
    Args:
        signal: BacktestSignal 实例
        
    Returns:
        JSON 兼容字典
    """
    return {
        'id': signal.id,
        'timestamp': signal.timestamp.isoformat() if signal.timestamp else None,
        'price': signal.price,
        'signal': signal.signal,
        'confidence': signal.confidence,
        'indicators': signal.indicators,
        'reasoning': signal.reasoning
    }
