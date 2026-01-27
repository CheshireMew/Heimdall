"""
数据库 Schema 定义
仅定义表结构数据模型，与业务逻辑分离
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class BacktestRun(Base):
    """回测运行记录表"""
    __tablename__ = 'backtest_runs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False)  # 交易对，如 'BTC/USDT'
    timeframe = Column(String(10), nullable=False)  # 时间周期，如 '1h'
    start_date = Column(DateTime, nullable=False)  # 回测开始日期
    end_date = Column(DateTime, nullable=False)  # 回测结束日期
    created_at = Column(DateTime, default=datetime.utcnow)  # 创建时间
    status = Column(String(20), default='running')  # 状态: running/completed/failed
    total_candles = Column(Integer, default=0)  # K线数量
    total_signals = Column(Integer, default=0)  # 信号总数
    buy_signals = Column(Integer, default=0)  # 买入信号数
    sell_signals = Column(Integer, default=0)  # 卖出信号数
    hold_signals = Column(Integer, default=0)  # 持有信号数
    metadata_info = Column('metadata', JSON, nullable=True)  # 额外元数据（JSON格式），重命名避免冲突
    
    # 关联关系
    signals = relationship("BacktestSignal", back_populates="backtest_run", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<BacktestRun(id={self.id}, symbol={self.symbol}, status={self.status})>"


class BacktestSignal(Base):
    """回测信号记录表"""
    __tablename__ = 'backtest_signals'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    backtest_id = Column(Integer, ForeignKey('backtest_runs.id'), nullable=False)  # 外键
    timestamp = Column(DateTime, nullable=False)  # 信号时间戳
    price = Column(Float, nullable=False)  # 当前价格
    signal = Column(String(10), nullable=False)  # 信号类型: BUY/SELL/HOLD
    confidence = Column(Float, default=0.0)  # 置信度 (0-100)
    indicators = Column(JSON, nullable=True)  # 技术指标（JSON格式）
    reasoning = Column(Text, nullable=True)  # AI 分析理由（如果有）
    
    # 关联关系
    backtest_run = relationship("BacktestRun", back_populates="signals")
    
    
    def __repr__(self):
        return f"<BacktestSignal(id={self.id}, signal={self.signal}, price={self.price})>"

class Kline(Base):
    """K线数据表 (用于缓存)"""
    __tablename__ = 'klines'
    
    # 复合主键: symbol + timeframe + timestamp
    symbol = Column(String(20), primary_key=True, nullable=False)
    timeframe = Column(String(10), primary_key=True, nullable=False)
    timestamp = Column(BigInteger, primary_key=True, nullable=False) # 毫秒时间戳
    
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    
    def to_list(self):
        """转换为 [ts, o, h, l, c, v] 格式"""
        return [self.timestamp, self.open, self.high, self.low, self.close, self.volume]
    
    
    def __repr__(self):
        return f"<Kline({self.symbol}, {self.timeframe}, {self.timestamp})>"

class Sentiment(Base):
    """市场情绪数据表 (如 Fear & Greed Index)"""
    __tablename__ = 'sentiment'
    
    date = Column(DateTime, primary_key=True) # 日期 (00:00:00)
    value = Column(Integer, nullable=False) # 指数数值 (0-100)
    classification = Column(String(20), nullable=True) # 分类 (Extreme Fear, etc.)
    timestamp = Column(BigInteger, nullable=True) # 原始时间戳
    
    def __repr__(self):
        return f"<Sentiment({self.date}, {self.value})>"
