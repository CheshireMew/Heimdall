"""
数据库 Schema 定义
仅定义表结构数据模型，与业务逻辑分离
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON, BigInteger, Index, Boolean
from sqlalchemy.orm import declarative_base, relationship

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
    trades = relationship("BacktestTrade", back_populates="backtest_run", cascade="all, delete-orphan")
    equity_points = relationship("BacktestEquityPoint", back_populates="backtest_run", cascade="all, delete-orphan")

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

    __table_args__ = (
        Index('ix_signal_backtest_id', 'backtest_id'),
    )

    def __repr__(self):
        return f"<BacktestSignal(id={self.id}, signal={self.signal}, price={self.price})>"


class BacktestTrade(Base):
    """回测成交记录表"""
    __tablename__ = 'backtest_trades'

    id = Column(Integer, primary_key=True, autoincrement=True)
    backtest_id = Column(Integer, ForeignKey('backtest_runs.id'), nullable=False)
    pair = Column(String(20), nullable=False)
    opened_at = Column(DateTime, nullable=False)
    closed_at = Column(DateTime, nullable=True)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    stake_amount = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)
    profit_abs = Column(Float, nullable=False)
    profit_pct = Column(Float, nullable=False)
    max_drawdown_pct = Column(Float, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    entry_tag = Column(String(100), nullable=True)
    exit_reason = Column(String(100), nullable=True)
    leverage = Column(Float, default=1.0)

    backtest_run = relationship("BacktestRun", back_populates="trades")

    __table_args__ = (
        Index('ix_trade_backtest_id', 'backtest_id'),
        Index('ix_trade_backtest_opened_at', 'backtest_id', 'opened_at'),
    )

    def __repr__(self):
        return f"<BacktestTrade(id={self.id}, pair={self.pair}, profit_abs={self.profit_abs})>"


class BacktestEquityPoint(Base):
    """回测资金曲线点"""
    __tablename__ = 'backtest_equity_points'

    id = Column(Integer, primary_key=True, autoincrement=True)
    backtest_id = Column(Integer, ForeignKey('backtest_runs.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    equity = Column(Float, nullable=False)
    pnl_abs = Column(Float, nullable=False)
    drawdown_pct = Column(Float, nullable=False)

    backtest_run = relationship("BacktestRun", back_populates="equity_points")

    __table_args__ = (
        Index('ix_equity_backtest_id', 'backtest_id'),
        Index('ix_equity_backtest_timestamp', 'backtest_id', 'timestamp'),
    )

    def __repr__(self):
        return f"<BacktestEquityPoint(id={self.id}, equity={self.equity})>"


class StrategyDefinition(Base):
    """策略定义"""
    __tablename__ = 'strategy_definitions'

    key = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    template = Column(String(50), nullable=False)
    category = Column(String(50), nullable=False, default='trend')
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    versions = relationship("StrategyVersion", back_populates="strategy", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<StrategyDefinition(key={self.key}, template={self.template})>"


class StrategyVersion(Base):
    """策略版本"""
    __tablename__ = 'strategy_versions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_key = Column(String(50), ForeignKey('strategy_definitions.key'), nullable=False)
    version = Column(Integer, nullable=False)
    name = Column(String(100), nullable=False)
    config = Column(JSON, nullable=False)
    parameter_space = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    is_default = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    strategy = relationship("StrategyDefinition", back_populates="versions")

    __table_args__ = (
        Index('ix_strategy_version_key_version', 'strategy_key', 'version', unique=True),
        Index('ix_strategy_version_default', 'strategy_key', 'is_default'),
    )

    def __repr__(self):
        return f"<StrategyVersion(strategy_key={self.strategy_key}, version={self.version})>"


class IndicatorDefinition(Base):
    """用户自定义指标注册表"""
    __tablename__ = 'indicator_definitions'

    key = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    engine = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    outputs = Column(JSON, nullable=False)
    params = Column(JSON, nullable=False)
    is_builtin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<IndicatorDefinition(key={self.key}, engine={self.engine})>"


class StrategyTemplateDefinition(Base):
    """用户自定义策略模板"""
    __tablename__ = 'strategy_template_definitions'

    key = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False, default='custom')
    description = Column(Text, nullable=True)
    indicator_keys = Column(JSON, nullable=False)
    default_config = Column(JSON, nullable=False)
    default_parameter_space = Column(JSON, nullable=True)
    is_builtin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<StrategyTemplateDefinition(key={self.key}, category={self.category})>"

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

    __table_args__ = (
        Index('ix_kline_sym_tf_ts', 'symbol', 'timeframe', 'timestamp'),
    )

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

class MarketIndicatorMeta(Base):
    """市场指标元数据配置表"""
    __tablename__ = 'market_indicator_meta'
    
    id = Column(String(50), primary_key=True)  # 指标唯一标识，如 'US10Y', 'FearGreedIndex'
    name = Column(String(100), nullable=False)  # 展示名称
    category = Column(String(50), nullable=False)  # 所属维度: Macro, Onchain, Sentiment, Tech
    unit = Column(String(20), nullable=True)  # 单位: %, USD, EH/s等
    frequency = Column(String(20), default='daily')  # 更新频率: daily, hourly
    description = Column(Text, nullable=True)  # 指标描述说明
    is_active = Column(Integer, default=1)  # 是否激活采抓取 (1/0)
    
    # 关联关系
    data_points = relationship("MarketIndicatorData", back_populates="meta_info", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<MarketIndicatorMeta(id={self.id}, name={self.name})>"

class MarketIndicatorData(Base):
    """市场指标历史数据流"""
    __tablename__ = 'market_indicator_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    indicator_id = Column(String(50), ForeignKey('market_indicator_meta.id'), nullable=False)  # 外键
    timestamp = Column(DateTime, nullable=False)  # 数据时间点 (可能精确到日或小时)
    value = Column(Float, nullable=False)  # 指标数值
    
    # 关联关系
    meta_info = relationship("MarketIndicatorMeta", back_populates="data_points")

    __table_args__ = (
        Index('ix_indicator_data_id_ts', 'indicator_id', 'timestamp'),
    )

    def __repr__(self):
        return f"<MarketIndicatorData(indicator={self.indicator_id}, ts={self.timestamp}, val={self.value})>"


class FactorDataset(Base):
    """因子研究数据集快照"""
    __tablename__ = 'factor_datasets'

    id = Column(Integer, primary_key=True, autoincrement=True)
    signature = Column(String(128), nullable=False, unique=True)
    symbol = Column(String(20), nullable=False)
    timeframe = Column(String(10), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    primary_horizon = Column(Integer, nullable=False)
    forward_horizons = Column(JSON, nullable=False)
    factor_ids = Column(JSON, nullable=False)
    categories = Column(JSON, nullable=False)
    cleaning = Column(JSON, nullable=False)
    row_count = Column(Integer, default=0, nullable=False)
    dataset_info = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    rows = relationship("FactorDatasetRow", back_populates="dataset", cascade="all, delete-orphan")
    research_runs = relationship("FactorResearchRun", back_populates="dataset", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_factor_dataset_signature', 'signature', unique=True),
        Index('ix_factor_dataset_symbol_tf', 'symbol', 'timeframe'),
    )

    def __repr__(self):
        return f"<FactorDataset(id={self.id}, symbol={self.symbol}, timeframe={self.timeframe})>"


class FactorDatasetRow(Base):
    """因子数据集逐行快照"""
    __tablename__ = 'factor_dataset_rows'

    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_id = Column(Integer, ForeignKey('factor_datasets.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    raw_values = Column(JSON, nullable=False)
    feature_values = Column(JSON, nullable=False)
    labels = Column(JSON, nullable=False)

    dataset = relationship("FactorDataset", back_populates="rows")

    __table_args__ = (
        Index('ix_factor_dataset_row_dataset_ts', 'dataset_id', 'timestamp', unique=True),
    )

    def __repr__(self):
        return f"<FactorDatasetRow(dataset_id={self.dataset_id}, timestamp={self.timestamp})>"


class FactorResearchRun(Base):
    """因子研究结果快照"""
    __tablename__ = 'factor_research_runs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_id = Column(Integer, ForeignKey('factor_datasets.id'), nullable=False)
    status = Column(String(20), default='completed', nullable=False)
    request_payload = Column(JSON, nullable=False)
    summary = Column(JSON, nullable=False)
    ranking = Column(JSON, nullable=False)
    details = Column(JSON, nullable=False)
    blend = Column(JSON, nullable=False)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    dataset = relationship("FactorDataset", back_populates="research_runs")

    __table_args__ = (
        Index('ix_factor_research_run_dataset_id', 'dataset_id'),
        Index('ix_factor_research_run_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<FactorResearchRun(id={self.id}, dataset_id={self.dataset_id}, status={self.status})>"
