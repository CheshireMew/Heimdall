"""
数据库模型定义 - 使用 SQLAlchemy ORM
用于存储回测记录和信号数据
"""
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# 数据库文件路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'heimdall.db')

# 确保 data 目录存在
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# 创建数据库引擎
engine = create_engine(f'sqlite:///{DB_PATH}', echo=False)

# 创建声明基类
Base = declarative_base()

# Session 工厂
SessionLocal = sessionmaker(bind=engine)


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
    metadata = Column(JSON, nullable=True)  # 额外元数据（JSON格式，存储参数配置）
    
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


def init_db():
    """
    初始化数据库，创建所有表
    """
    Base.metadata.create_all(engine)
    print(f"数据库初始化完成: {DB_PATH}")


def get_session():
    """
    获取数据库会话
    """
    return SessionLocal()


if __name__ == "__main__":
    # 测试：初始化数据库
    init_db()
